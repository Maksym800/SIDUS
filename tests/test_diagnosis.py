"""Owner: backend developer 1 (diagnosis engine)."""
import os
import tempfile
import unittest
from datetime import date, datetime

from backend.diagnosis import engine, knowledge_base, service
from data import catalog, db, repository

BASELINE = catalog.default_values()


_TEMP = None


def setUpModule():
    global _TEMP
    _TEMP = tempfile.TemporaryDirectory()
    os.environ["ASTRO_HEALTH_DB"] = os.path.join(_TEMP.name, "test_diagnosis.db")
    db.init_db()


def tearDownModule():
    os.environ.pop("ASTRO_HEALTH_DB", None)
    _TEMP.cleanup()


def diagnose(environment="orbit", flight_day=30, **changes):
    current = {**BASELINE, "vision_clear": 1, **changes}
    return {finding.code: finding.severity
            for finding in engine.evaluate(current, BASELINE, environment, flight_day)}


class ContractTests(unittest.TestCase):

    def test_metric_order_matches_the_catalog(self):
        self.assertEqual(engine.metric_order(), catalog.KEYS)

    def test_environments_match_the_catalog(self):
        self.assertEqual(engine.environments(), catalog.ENVIRONMENTS)

    def test_every_code_has_texts_in_both_languages(self):
        self.assertEqual(set(engine.codes()), set(knowledge_base.CODES))
        for code in engine.codes():
            self.assertTrue(knowledge_base.describe(code, "en").name.startswith("Suspected "))
            self.assertTrue(knowledge_base.describe(code, "uk").name.startswith("Підозра на "))
            for key in knowledge_base.related_metrics(code):
                self.assertIn(key, catalog.BY_KEY)


class RuleTests(unittest.TestCase):
    def test_healthy_values_give_no_findings(self):
        self.assertEqual(diagnose(), {})
        self.assertEqual(engine.evaluate(BASELINE, BASELINE, "earth", 0), [])

    def test_missing_values_never_fire(self):
        self.assertEqual(engine.evaluate({}, BASELINE, "orbit", 10), [])
        self.assertEqual(engine.evaluate({"heart_rate_bpm": None}, {}, "orbit", 10), [])

    def test_heart_rate(self):
        self.assertEqual(diagnose(heart_rate_bpm=99), {"TACHYCARDIA": 1})
        self.assertEqual(diagnose(heart_rate_bpm=80), {})
        self.assertEqual(diagnose(heart_rate_bpm=130), {"TACHYCARDIA": 2})
        self.assertEqual(diagnose(heart_rate_bpm=45), {"BRADYCARDIA": 1})
        self.assertEqual(diagnose(heart_rate_bpm=39), {"BRADYCARDIA": 2})

    def test_a_slow_trained_heart_is_not_flagged_at_its_own_norm(self):
        athlete = {**BASELINE, "heart_rate_bpm": 46}
        findings = engine.evaluate({**athlete, "vision_clear": 1}, athlete, "orbit", 30)
        self.assertEqual(findings, [])

    def test_blood_pressure(self):
        self.assertEqual(diagnose(bp_systolic=140, bp_diastolic=88), {"HYPERTENSION": 1})
        self.assertEqual(diagnose(bp_systolic=165, bp_diastolic=102), {"HYPERTENSION": 2})
        self.assertEqual(diagnose(bp_systolic=86, bp_diastolic=58), {"HYPOTENSION": 1})
        self.assertEqual(diagnose(bp_systolic=78, bp_diastolic=50), {"HYPOTENSION": 2})

    def test_thresholds_are_inclusive_on_the_documented_side(self):
        self.assertEqual(diagnose(body_temp_c=37.4), {})
        self.assertEqual(diagnose(body_temp_c=37.5), {"FEVER": 1})
        self.assertEqual(diagnose(body_temp_c=38.5), {"FEVER": 2})
        self.assertEqual(diagnose(glucose_mmol_l=3.9), {})
        self.assertEqual(diagnose(glucose_mmol_l=3.8), {"HYPOGLYCEMIA": 1})
        self.assertEqual(diagnose(glucose_mmol_l=7.8), {"HYPERGLYCEMIA": 1})
        self.assertEqual(diagnose(glucose_mmol_l=11.1), {"HYPERGLYCEMIA": 2})
        self.assertEqual(diagnose(spo2_pct=95), {})
        self.assertEqual(diagnose(spo2_pct=94), {"HYPOXEMIA": 1})
        self.assertEqual(diagnose(spo2_pct=89), {"HYPOXEMIA": 2})

    def test_blurred_vision_depends_on_gravity(self):
        self.assertEqual(diagnose("earth", vision_clear=0), {"VISUAL_IMPAIRMENT": 1})
        for environment in ("mars", "moon", "deep_space", "orbit"):
            self.assertEqual(diagnose(environment, vision_clear=0), {"SANS": 1})
        self.assertEqual(diagnose("orbit", vision_clear=0, vascular_condition=1),
                         {"SANS": 2, "VENOUS_CONGESTION": 1})

    def test_unloading_makes_muscle_and_bone_rules_stricter(self):
        thinner = BASELINE["muscle_thickness_mm"] * 0.92
        self.assertEqual(diagnose("earth", muscle_thickness_mm=thinner), {})
        self.assertEqual(diagnose("orbit", muscle_thickness_mm=thinner), {"MUSCLE_ATROPHY": 1})
        higher = round(BASELINE["bone_resorption_ntx"] * 1.4)
        self.assertEqual(diagnose("earth", bone_resorption_ntx=higher), {})
        self.assertEqual(diagnose("orbit", bone_resorption_ntx=higher), {"BONE_LOSS": 1})

    def test_first_days_of_weightlessness_relax_the_coordination_rule(self):
        worse = round(BASELINE["coordination_pct"] * 0.8)
        self.assertEqual(diagnose("orbit", flight_day=2, coordination_pct=worse), {})
        self.assertEqual(diagnose("orbit", flight_day=30, coordination_pct=worse),
                         {"SENSORIMOTOR": 1})
        self.assertEqual(diagnose("earth", flight_day=2, coordination_pct=worse),
                         {"SENSORIMOTOR": 1})

    def test_radiation(self):
        base_dose = BASELINE["radiation_total_msv"]
        self.assertEqual(diagnose("earth", radiation_total_msv=300), {"RADIATION_DOSE": 1})
        self.assertEqual(diagnose("earth", radiation_total_msv=600), {"RADIATION_DOSE": 2})
        self.assertEqual(diagnose("orbit", 30, radiation_total_msv=base_dose + 60),
                         {"RADIATION_DOSE": 1})
        self.assertEqual(diagnose("deep_space", 30, radiation_total_msv=base_dose + 60), {})
        self.assertEqual(diagnose("earth", neutron_rate_usv_h=6), {"RADIATION_RATE": 2})
        self.assertEqual(diagnose("mars", neutron_rate_usv_h=6), {"RADIATION_RATE": 1})
        self.assertEqual(diagnose("orbit", neutron_rate_usv_h=6), {})

    def test_other_rules(self):
        cases = (
            (dict(ecg_rhythm=1), {"ARRHYTHMIA": 1}),
            (dict(ecg_rhythm=2), {"ARRHYTHMIA": 2}),
            (dict(hrv_rmssd_ms=30), {"LOW_HRV": 1}),
            (dict(blood_flow_cm_s=12.0), {"VENOUS_CONGESTION": 1}),
            (dict(vascular_condition=2), {"VENOUS_CONGESTION": 2}),
            (dict(sleep_hours=5.5), {"SLEEP_DISORDER": 1}),
            (dict(sleep_hours=3.5, sleep_efficiency_pct=60), {"SLEEP_DISORDER": 2}),
            (dict(muscle_structure=2), {"MUSCLE_ATROPHY": 2}),
            (dict(body_temp_c=34.8), {"HYPOTHERMIA": 2}),
            (dict(cortisol_nmol_l=560), {"STRESS_IMMUNE": 1}),
            (dict(viral_activation=1), {"VIRAL_REACTIVATION": 1}),
            (dict(viral_activation=1, body_temp_c=38.0), {"VIRAL_REACTIVATION": 2, "FEVER": 1}),
            (dict(calcium_mmol_l=2.70), {"HYPERCALCEMIA": 1}),
            (dict(calcium_mmol_l=2.00), {"HYPOCALCEMIA": 1}),
            (dict(mood_score=4), {"PSYCH_STRAIN": 1}),
            (dict(stress_score=9), {"PSYCH_STRAIN": 2}),
            (dict(mass_kg=BASELINE["mass_kg"] * 0.94), {"MASS_LOSS": 1}),
            (dict(mass_kg=BASELINE["mass_kg"] * 0.89), {"MASS_LOSS": 2}),
        )
        for changes, expected in cases:
            with self.subTest(changes=changes):
                self.assertEqual(diagnose(**changes), expected)

    def test_worst_finding_comes_first(self):
        findings = engine.evaluate({**BASELINE, "vision_clear": 1, "mood_score": 4,
                                    "spo2_pct": 85}, BASELINE, "orbit", 30)
        self.assertEqual([f.severity for f in findings], [2, 1])

    def test_unknown_environment_is_refused(self):
        with self.assertRaises(ValueError):
            engine.evaluate(BASELINE, BASELINE, "venus", 1)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.profile_id = repository.create_profile(
            f"Service {self.id()}", 40, date(2026, 10, 1), BASELINE,
            created_at=datetime(2026, 9, 20, 10, 0))

    def test_diagnosis_is_stored_once_per_entry_and_environment(self):
        repository.add_entry(self.profile_id, {**BASELINE, "vision_clear": 0,
                                               "heart_rate_bpm": 135},
                             "orbit", recorded_at=datetime(2026, 11, 14, 9, 0))
        first = service.assess_latest(self.profile_id, "orbit")
        again = service.assess_latest(self.profile_id, "orbit")
        on_earth = service.assess_latest(self.profile_id, "earth")
        self.assertEqual(first.run_id, again.run_id)
        self.assertNotEqual(first.run_id, on_earth.run_id)
        self.assertEqual(first.flight_day, 45)
        self.assertEqual({f.code for f in first.findings}, {"TACHYCARDIA", "SANS"})
        self.assertEqual({f.code for f in on_earth.findings}, {"TACHYCARDIA", "VISUAL_IMPAIRMENT"})
        self.assertEqual(first.zone_levels(), {"heart": 2, "eyes": 1})
        self.assertEqual(first.overall, 2)
        self.assertIsInstance(first.diagnosed_at, datetime)

    def test_baseline_before_launch_uses_flight_day_zero(self):
        assessment = service.assess_latest(self.profile_id, "earth")
        self.assertEqual((assessment.flight_day, assessment.findings), (0, ()))

    def test_unknown_profile(self):
        self.assertIsNone(service.assess_latest(987654, "earth"))


if __name__ == "__main__":
    unittest.main()
