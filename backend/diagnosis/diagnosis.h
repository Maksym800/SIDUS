/* Owner: backend developer 1 (diagnosis engine, C part). */
#ifndef ASTRO_DIAGNOSIS_H
#define ASTRO_DIAGNOSIS_H

#if defined(_WIN32)
#  define DIAG_API __declspec(dllexport)
#elif defined(__GNUC__)
#  define DIAG_API __attribute__((visibility("default")))
#else
#  define DIAG_API
#endif

#ifdef __cplusplus
extern "C" {
#endif


#define DIAG_ENGINE_VERSION 1


enum {
    DIAG_OK = 0,
    DIAG_CAUTION = 1,
    DIAG_CRITICAL = 2
};


enum {
    DIAG_ERR_ARGUMENT = -1,
    DIAG_ERR_METRICS = -2,
    DIAG_ERR_ENVIRONMENT = -3,
    DIAG_ERR_CAPACITY = -4
};


typedef enum {
    M_MASS_KG = 0,
    M_HEART_RATE,
    M_BP_SYSTOLIC,
    M_BP_DIASTOLIC,
    M_ECG_RHYTHM,
    M_HRV_RMSSD,
    M_BLOOD_FLOW,
    M_VASCULAR,
    M_VISION_CLEAR,
    M_SLEEP_HOURS,
    M_SLEEP_EFFICIENCY,
    M_MUSCLE_THICKNESS,
    M_MUSCLE_STRUCTURE,
    M_BODY_TEMP,
    M_SPO2,
    M_COORDINATION,
    M_GLUCOSE,
    M_CORTISOL,
    M_VIRAL_ACTIVATION,
    M_CALCIUM,
    M_BONE_RESORPTION,
    M_MOOD,
    M_STRESS,
    M_RADIATION_TOTAL,
    M_NEUTRON_RATE,
    M_COUNT
} MetricIndex;

typedef enum {
    ENV_EARTH = 0,
    ENV_MARS,
    ENV_MOON,
    ENV_DEEP_SPACE,
    ENV_ORBIT,
    ENV_COUNT
} Environment;


typedef enum {
    D_TACHYCARDIA = 0,
    D_BRADYCARDIA,
    D_HYPERTENSION,
    D_HYPOTENSION,
    D_ARRHYTHMIA,
    D_LOW_HRV,
    D_VENOUS_CONGESTION,
    D_SANS,
    D_VISUAL_IMPAIRMENT,
    D_SLEEP_DISORDER,
    D_MUSCLE_ATROPHY,
    D_FEVER,
    D_HYPOTHERMIA,
    D_HYPOXEMIA,
    D_SENSORIMOTOR,
    D_HYPOGLYCEMIA,
    D_HYPERGLYCEMIA,
    D_STRESS_IMMUNE,
    D_VIRAL_REACTIVATION,
    D_BONE_LOSS,
    D_HYPERCALCEMIA,
    D_HYPOCALCEMIA,
    D_PSYCH_STRAIN,
    D_RADIATION_DOSE,
    D_RADIATION_RATE,
    D_MASS_LOSS,
    D_COUNT
} DiagnosisCode;


DIAG_API int diag_engine_version(void);

DIAG_API int diag_metric_count(void);
DIAG_API const char *diag_metric_name(int index);

DIAG_API int diag_environment_count(void);
DIAG_API const char *diag_environment_name(int index);

DIAG_API int diag_code_count(void);
DIAG_API const char *diag_code_name(int index);
DIAG_API const char *diag_code_zone(int index);


DIAG_API int diag_evaluate(const double *current, const double *baseline, int n_metrics,
                           int environment, int flight_day,
                           int *out_codes, int *out_severity, int max_out);

#ifdef __cplusplus
}
#endif

#endif
