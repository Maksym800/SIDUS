/* Owner: backend developer 1 (diagnosis engine, C part). */
#include "diagnosis.h"

#include <math.h>
#include <stddef.h>


static const char *const METRIC_NAMES[M_COUNT] = {
    [M_MASS_KG] = "mass_kg",
    [M_HEART_RATE] = "heart_rate_bpm",
    [M_BP_SYSTOLIC] = "bp_systolic",
    [M_BP_DIASTOLIC] = "bp_diastolic",
    [M_ECG_RHYTHM] = "ecg_rhythm",
    [M_HRV_RMSSD] = "hrv_rmssd_ms",
    [M_BLOOD_FLOW] = "blood_flow_cm_s",
    [M_VASCULAR] = "vascular_condition",
    [M_VISION_CLEAR] = "vision_clear",
    [M_SLEEP_HOURS] = "sleep_hours",
    [M_SLEEP_EFFICIENCY] = "sleep_efficiency_pct",
    [M_MUSCLE_THICKNESS] = "muscle_thickness_mm",
    [M_MUSCLE_STRUCTURE] = "muscle_structure",
    [M_BODY_TEMP] = "body_temp_c",
    [M_SPO2] = "spo2_pct",
    [M_COORDINATION] = "coordination_pct",
    [M_GLUCOSE] = "glucose_mmol_l",
    [M_CORTISOL] = "cortisol_nmol_l",
    [M_VIRAL_ACTIVATION] = "viral_activation",
    [M_CALCIUM] = "calcium_mmol_l",
    [M_BONE_RESORPTION] = "bone_resorption_ntx",
    [M_MOOD] = "mood_score",
    [M_STRESS] = "stress_score",
    [M_RADIATION_TOTAL] = "radiation_total_msv",
    [M_NEUTRON_RATE] = "neutron_rate_usv_h",
};

typedef struct {
    const char *name;
    double gravity_g;
    double typical_daily_msv;
    double neutron_caution;
    double neutron_critical;
} EnvProfile;


static const EnvProfile ENVIRONMENTS[ENV_COUNT] = {

    [ENV_EARTH]      = {"earth",      1.000, 0.01,    0.5,     2.0},
    [ENV_MARS]       = {"mars",       0.379, 0.67,    4.0,     12.0},
    [ENV_MOON]       = {"moon",       0.166, 1.37,    25.0,    75.0},
    [ENV_DEEP_SPACE] = {"deep_space", 0.000, 1.80,    5.0,     15.0},
    [ENV_ORBIT]      = {"orbit",      0.000, 0.70,    12.0,    36.0},
};


#define CAREER_LIMIT_MSV 600.0

#define MIN_DAYS_FOR_DOSE_RATE 7

#define ADAPTATION_DAYS 3

#define EPSILON 1e-9


typedef struct {
    const double *current;
    const double *baseline;
    const EnvProfile *env;
    int env_index;
    int flight_day;
    double unloading;
    int reduced_gravity;
    int weightless;
} Ctx;


static int known(double value)
{
    return !isnan(value);
}

static int worst(int a, int b)
{
    return a > b ? a : b;
}


static int at_least(double value, double caution, double critical)
{
    if (!known(value)) return DIAG_OK;
    if (value >= critical - EPSILON) return DIAG_CRITICAL;
    if (value >= caution - EPSILON) return DIAG_CAUTION;
    return DIAG_OK;
}


static int below(double value, double caution, double critical)
{
    if (!known(value)) return DIAG_OK;
    if (value < critical - EPSILON) return DIAG_CRITICAL;
    if (value < caution - EPSILON) return DIAG_CAUTION;
    return DIAG_OK;
}


static int graded(double grade)
{
    return at_least(grade, 0.5, 1.5);
}

static double cur(const Ctx *c, MetricIndex m)
{
    return c->current[m];
}


static double change(const Ctx *c, MetricIndex m)
{
    return c->current[m] - c->baseline[m];
}


static double ratio(const Ctx *c, MetricIndex m)
{
    double base = c->baseline[m];
    if (!known(base) || base <= 0.0) return NAN;
    return c->current[m] / base;
}


static double drop_fraction(const Ctx *c, MetricIndex m)
{
    return 1.0 - ratio(c, m);
}

static int vision_blurred(const Ctx *c)
{
    double clear = cur(c, M_VISION_CLEAR);
    return known(clear) && clear < 0.5;
}


static int rule_tachycardia(const Ctx *c)
{
    int severity = at_least(cur(c, M_HEART_RATE), 100.0, 130.0);

    if (change(c, M_HEART_RATE) >= 25.0)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_bradycardia(const Ctx *c)
{
    double hr = cur(c, M_HEART_RATE);
    double slowdown = -change(c, M_HEART_RATE);

    if (!known(hr)) return DIAG_OK;
    if (hr < 40.0) return DIAG_CRITICAL;
    if (!known(slowdown)) return hr < 50.0 ? DIAG_CAUTION : DIAG_OK;

    if (slowdown >= 20.0 || (hr < 50.0 && slowdown >= 8.0)) return DIAG_CAUTION;
    return DIAG_OK;
}

static int rule_hypertension(const Ctx *c)
{
    int severity = worst(at_least(cur(c, M_BP_SYSTOLIC), 135.0, 160.0),
                         at_least(cur(c, M_BP_DIASTOLIC), 85.0, 100.0));
    if (change(c, M_BP_SYSTOLIC) >= 20.0 || change(c, M_BP_DIASTOLIC) >= 15.0)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_hypotension(const Ctx *c)
{
    int severity = worst(below(cur(c, M_BP_SYSTOLIC), 90.0, 80.0),
                         below(cur(c, M_BP_DIASTOLIC), 55.0, 45.0));
    if (-change(c, M_BP_SYSTOLIC) >= 20.0)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_arrhythmia(const Ctx *c)
{
    return graded(cur(c, M_ECG_RHYTHM));
}

static int rule_low_hrv(const Ctx *c)
{
    return worst(below(ratio(c, M_HRV_RMSSD), 0.70, 0.50),
                 below(cur(c, M_HRV_RMSSD), 20.0, 10.0));
}

static int rule_venous_congestion(const Ctx *c)
{

    double caution = 0.40 - 0.10 * c->unloading;
    double critical = 0.70 - 0.10 * c->unloading;
    return worst(graded(cur(c, M_VASCULAR)),
                 at_least(drop_fraction(c, M_BLOOD_FLOW), caution, critical));
}


static int rule_sans(const Ctx *c)
{
    if (!c->reduced_gravity || !vision_blurred(c)) return DIAG_OK;

    if (cur(c, M_VASCULAR) >= 0.5 || drop_fraction(c, M_BLOOD_FLOW) >= 0.30)
        return DIAG_CRITICAL;
    return DIAG_CAUTION;
}


static int rule_visual_impairment(const Ctx *c)
{
    return (!c->reduced_gravity && vision_blurred(c)) ? DIAG_CAUTION : DIAG_OK;
}

static int rule_sleep_disorder(const Ctx *c)
{
    int severity = worst(below(cur(c, M_SLEEP_HOURS), 6.0, 4.0),
                         below(cur(c, M_SLEEP_EFFICIENCY), 85.0, 70.0));
    if (-change(c, M_SLEEP_HOURS) >= 2.0)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_muscle_atrophy(const Ctx *c)
{

    double caution = 0.10 - 0.03 * c->unloading;
    double critical = 0.20 - 0.05 * c->unloading;
    return worst(graded(cur(c, M_MUSCLE_STRUCTURE)),
                 at_least(drop_fraction(c, M_MUSCLE_THICKNESS), caution, critical));
}

static int rule_fever(const Ctx *c)
{
    int severity = at_least(cur(c, M_BODY_TEMP), 37.5, 38.5);
    if (change(c, M_BODY_TEMP) >= 1.0 - EPSILON)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_hypothermia(const Ctx *c)
{
    return below(cur(c, M_BODY_TEMP), 35.5, 35.0);
}

static int rule_hypoxemia(const Ctx *c)
{
    int severity = below(cur(c, M_SPO2), 95.0, 90.0);
    if (-change(c, M_SPO2) >= 4.0)
        severity = worst(severity, DIAG_CAUTION);
    return severity;
}

static int rule_sensorimotor(const Ctx *c)
{

    int adapting = c->weightless && c->flight_day >= 1 && c->flight_day <= ADAPTATION_DAYS;
    double caution = adapting ? 0.25 : 0.15;
    double critical = adapting ? 0.45 : 0.30;
    return at_least(drop_fraction(c, M_COORDINATION), caution, critical);
}

static int rule_hypoglycemia(const Ctx *c)
{
    return below(cur(c, M_GLUCOSE), 3.9, 3.0);
}

static int rule_hyperglycemia(const Ctx *c)
{
    return at_least(cur(c, M_GLUCOSE), 7.8, 11.1);
}

static int rule_stress_immune(const Ctx *c)
{
    return worst(at_least(ratio(c, M_CORTISOL), 1.5, 2.0),
                 at_least(cur(c, M_CORTISOL), 700.0, 1000.0));
}

static int rule_viral_reactivation(const Ctx *c)
{
    double noticed = cur(c, M_VIRAL_ACTIVATION);
    if (!known(noticed) || noticed < 0.5) return DIAG_OK;

    return cur(c, M_BODY_TEMP) >= 37.5 - EPSILON ? DIAG_CRITICAL : DIAG_CAUTION;
}

static int rule_bone_loss(const Ctx *c)
{

    double caution = 0.50 - 0.20 * c->unloading;
    double critical = 1.00 - 0.30 * c->unloading;
    return at_least(ratio(c, M_BONE_RESORPTION) - 1.0, caution, critical);
}

static int rule_hypercalcemia(const Ctx *c)
{
    return at_least(cur(c, M_CALCIUM), 2.65, 3.00);
}

static int rule_hypocalcemia(const Ctx *c)
{
    return below(cur(c, M_CALCIUM), 2.10, 1.90);
}

static int rule_psych_strain(const Ctx *c)
{
    return worst(below(cur(c, M_MOOD), 5.0, 3.0),
                 at_least(cur(c, M_STRESS), 7.0, 9.0));
}

static int rule_radiation_dose(const Ctx *c)
{
    int severity = at_least(cur(c, M_RADIATION_TOTAL),
                            0.5 * CAREER_LIMIT_MSV, CAREER_LIMIT_MSV);
    double gained = change(c, M_RADIATION_TOTAL);


    if (c->env_index != ENV_EARTH && c->flight_day >= MIN_DAYS_FOR_DOSE_RATE && known(gained)) {
        double per_day = gained / (double)c->flight_day;
        double typical = c->env->typical_daily_msv;
        severity = worst(severity, at_least(per_day, 1.5 * typical, 3.0 * typical));
    }
    return severity;
}

static int rule_radiation_rate(const Ctx *c)
{
    return at_least(cur(c, M_NEUTRON_RATE),
                    c->env->neutron_caution, c->env->neutron_critical);
}

static int rule_mass_loss(const Ctx *c)
{
    return at_least(drop_fraction(c, M_MASS_KG), 0.05, 0.10);
}


typedef struct {
    const char *name;
    const char *zone;
    int (*evaluate)(const Ctx *ctx);
} Rule;

static const Rule RULES[D_COUNT] = {
    [D_TACHYCARDIA]        = {"TACHYCARDIA",        "heart",      rule_tachycardia},
    [D_BRADYCARDIA]        = {"BRADYCARDIA",        "heart",      rule_bradycardia},
    [D_HYPERTENSION]       = {"HYPERTENSION",       "heart",      rule_hypertension},
    [D_HYPOTENSION]        = {"HYPOTENSION",        "heart",      rule_hypotension},
    [D_ARRHYTHMIA]         = {"ARRHYTHMIA",         "heart",      rule_arrhythmia},
    [D_LOW_HRV]            = {"LOW_HRV",            "heart",      rule_low_hrv},
    [D_VENOUS_CONGESTION]  = {"VENOUS_CONGESTION",  "neck",       rule_venous_congestion},
    [D_SANS]               = {"SANS",               "eyes",       rule_sans},
    [D_VISUAL_IMPAIRMENT]  = {"VISUAL_IMPAIRMENT",  "eyes",       rule_visual_impairment},
    [D_SLEEP_DISORDER]     = {"SLEEP_DISORDER",     "head",       rule_sleep_disorder},
    [D_MUSCLE_ATROPHY]     = {"MUSCLE_ATROPHY",     "muscles",    rule_muscle_atrophy},
    [D_FEVER]              = {"FEVER",              "whole_body", rule_fever},
    [D_HYPOTHERMIA]        = {"HYPOTHERMIA",        "whole_body", rule_hypothermia},
    [D_HYPOXEMIA]          = {"HYPOXEMIA",          "lungs",      rule_hypoxemia},
    [D_SENSORIMOTOR]       = {"SENSORIMOTOR",       "head",       rule_sensorimotor},
    [D_HYPOGLYCEMIA]       = {"HYPOGLYCEMIA",       "metabolism", rule_hypoglycemia},
    [D_HYPERGLYCEMIA]      = {"HYPERGLYCEMIA",      "metabolism", rule_hyperglycemia},
    [D_STRESS_IMMUNE]      = {"STRESS_IMMUNE",      "immune",     rule_stress_immune},
    [D_VIRAL_REACTIVATION] = {"VIRAL_REACTIVATION", "immune",     rule_viral_reactivation},
    [D_BONE_LOSS]          = {"BONE_LOSS",          "bones",      rule_bone_loss},
    [D_HYPERCALCEMIA]      = {"HYPERCALCEMIA",      "bones",      rule_hypercalcemia},
    [D_HYPOCALCEMIA]       = {"HYPOCALCEMIA",       "bones",      rule_hypocalcemia},
    [D_PSYCH_STRAIN]       = {"PSYCH_STRAIN",       "head",       rule_psych_strain},
    [D_RADIATION_DOSE]     = {"RADIATION_DOSE",     "whole_body", rule_radiation_dose},
    [D_RADIATION_RATE]     = {"RADIATION_RATE",     "whole_body", rule_radiation_rate},
    [D_MASS_LOSS]          = {"MASS_LOSS",          "metabolism", rule_mass_loss},
};


int diag_engine_version(void)
{
    return DIAG_ENGINE_VERSION;
}

int diag_metric_count(void)
{
    return M_COUNT;
}

const char *diag_metric_name(int index)
{
    return (index >= 0 && index < M_COUNT) ? METRIC_NAMES[index] : NULL;
}

int diag_environment_count(void)
{
    return ENV_COUNT;
}

const char *diag_environment_name(int index)
{
    return (index >= 0 && index < ENV_COUNT) ? ENVIRONMENTS[index].name : NULL;
}

int diag_code_count(void)
{
    return D_COUNT;
}

const char *diag_code_name(int index)
{
    return (index >= 0 && index < D_COUNT) ? RULES[index].name : NULL;
}

const char *diag_code_zone(int index)
{
    return (index >= 0 && index < D_COUNT) ? RULES[index].zone : NULL;
}

int diag_evaluate(const double *current, const double *baseline, int n_metrics,
                  int environment, int flight_day,
                  int *out_codes, int *out_severity, int max_out)
{
    Ctx ctx;
    int code;
    int count = 0;

    if (current == NULL || baseline == NULL || out_codes == NULL ||
        out_severity == NULL || max_out < 0)
        return DIAG_ERR_ARGUMENT;
    if (n_metrics != M_COUNT)
        return DIAG_ERR_METRICS;
    if (environment < 0 || environment >= ENV_COUNT)
        return DIAG_ERR_ENVIRONMENT;

    ctx.current = current;
    ctx.baseline = baseline;
    ctx.env = &ENVIRONMENTS[environment];
    ctx.env_index = environment;
    ctx.flight_day = flight_day;
    ctx.unloading = 1.0 - ctx.env->gravity_g;
    ctx.reduced_gravity = ctx.env->gravity_g < 0.999;
    ctx.weightless = ctx.env->gravity_g < 0.05;

    for (code = 0; code < D_COUNT; code++) {
        int severity = RULES[code].evaluate(&ctx);
        if (severity == DIAG_OK)
            continue;
        if (count >= max_out)
            return DIAG_ERR_CAPACITY;
        out_codes[count] = code;
        out_severity[count] = severity;
        count++;
    }
    return count;
}
