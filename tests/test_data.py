import os
import tempfile
import unittest
from datetime import date, datetime

from data import catalog, db, repository


_TEMP = None


def setUpModule():
    global _TEMP
    _TEMP = tempfile.TemporaryDirectory()
    os.environ["ASTRO_HEALTH_DB"] = os.path.join(_TEMP.name, "test_data.db")
    db.init_db()


def tearDownModule():
    os.environ.pop("ASTRO_HEALTH_DB", None)
    _TEMP.cleanup()


def make_profile(name, **baseline_changes):
    baseline = {**catalog.default_values(), **baseline_changes}
    return repository.create_profile(name, 35, date(2026, 10, 1), baseline,
                                     created_at=datetime(2026, 9, 20, 10, 0, 0))


class SchemaTests(unittest.TestCase):
    def test_init_is_repeatable(self):
        db.init_db()
        db.init_db()

    def test_every_metric_has_a_column(self):
        with db.connect() as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(metric_entries)")}
        self.assertTrue(set(catalog.KEYS) <= columns)


class ProfileTests(unittest.TestCase):
    def test_profile_is_created_with_a_baseline_on_earth(self):
        profile_id = make_profile("Anna Baseline")
        profile = repository.get_profile(profile_id)
        baseline = repository.get_baseline(profile_id)
        self.assertEqual(profile["name"], "Anna Baseline")
        self.assertEqual(profile["flight_start"], date(2026, 10, 1))
        self.assertTrue(baseline["is_baseline"])
        self.assertEqual(baseline["environment"], "earth")
        self.assertEqual(baseline["recorded_at"], datetime(2026, 9, 20, 10, 0, 0))
        self.assertIsNone(baseline["vision_clear"])
        self.assertIsInstance(baseline["heart_rate_bpm"], int)

    def test_names_are_trimmed_and_unique_ignoring_case(self):
        make_profile("  Олена   Тест ")
        self.assertTrue(repository.profile_name_exists("олена тест"))
        with self.assertRaises(ValueError):
            make_profile("ОЛЕНА ТЕСТ")
        with self.assertRaises(ValueError):
            make_profile("   ")

    def test_profile_list_reports_the_latest_entry(self):
        profile_id = make_profile("Latest Entry")
        values = {**catalog.default_values(), "vision_clear": 1}
        repository.add_entry(profile_id, values, "orbit", recorded_at=datetime(2026, 11, 3, 8, 30))
        row = repository.list_profiles().set_index("id").loc[profile_id]
        self.assertEqual(row["last_entry_at"].to_pydatetime(), datetime(2026, 11, 3, 8, 30))
        self.assertEqual(row["entries"], 2)


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.profile_id = make_profile(f"Entry {self.id()}")
        self.values = {**catalog.default_values(), "vision_clear": 1}

    def test_editing_adds_a_row_and_keeps_the_old_ones(self):
        first = repository.add_entry(self.profile_id, self.values, "orbit",
                                     recorded_at=datetime(2026, 11, 1, 9, 0))
        second = repository.add_entry(self.profile_id, {**self.values, "heart_rate_bpm": 90},
                                      "orbit", recorded_at=datetime(2026, 11, 1, 21, 0))
        entries = repository.get_entries(self.profile_id)
        self.assertEqual(len(entries), 3)
        self.assertEqual(repository.get_entry(first)["heart_rate_bpm"], 62)
        self.assertEqual(repository.get_latest_entry(self.profile_id)["id"], second)
        self.assertEqual(repository.get_previous_entry(repository.get_entry(second))["id"], first)

    def test_time_range_filter(self):
        repository.add_entry(self.profile_id, self.values, "orbit",
                             recorded_at=datetime(2026, 11, 30, 23, 59, 59))
        repository.add_entry(self.profile_id, self.values, "orbit",
                             recorded_at=datetime(2026, 12, 1, 0, 0, 0))
        november = repository.get_entries(self.profile_id, datetime(2026, 11, 1),
                                          datetime(2026, 12, 1))
        self.assertEqual(len(november), 1)

    def test_bad_values_are_rejected(self):
        bad_sets = (
            {**self.values, "spo2_pct": 150},
            {**self.values, "ecg_rhythm": 5},
            {**self.values, "mass_kg": "heavy"},
            {k: v for k, v in self.values.items() if k != "mass_kg"},
        )
        for values in bad_sets:
            with self.assertRaises(ValueError):
                repository.add_entry(self.profile_id, values, "orbit")
        with self.assertRaises(ValueError):
            repository.add_entry(self.profile_id, self.values, "venus")

    def test_vision_may_be_left_empty(self):
        entry_id = repository.add_entry(self.profile_id, {**self.values, "vision_clear": None},
                                        "orbit", source="game")
        self.assertIsNone(repository.get_entry(entry_id)["vision_clear"])


class DiagnosisStorageTests(unittest.TestCase):
    def test_runs_and_findings_round_trip(self):
        profile_id = make_profile("Stored Runs")
        entry_id = repository.get_baseline(profile_id)["id"]
        repository.save_diagnosis(entry_id, profile_id, "orbit", 12,
                                  [("FEVER", 1, "whole_body"), ("TACHYCARDIA", 2, "heart")],
                                  diagnosed_at=datetime(2026, 11, 2, 7, 0))
        repository.save_diagnosis(entry_id, profile_id, "earth", 12, [])
        orbit = repository.get_latest_run(entry_id, "orbit")
        self.assertEqual(orbit["overall_severity"], 2)
        self.assertEqual(orbit["diagnosed_at"], datetime(2026, 11, 2, 7, 0))
        self.assertEqual([f["code"] for f in orbit["findings"]], ["TACHYCARDIA", "FEVER"])
        earth = repository.get_latest_run(entry_id, "earth")
        self.assertEqual((earth["overall_severity"], earth["findings"]), (0, []))
        self.assertIsNone(repository.get_latest_run(entry_id, "mars"))
        self.assertEqual(len(repository.get_runs(profile_id)), 2)


class WorkoutAndSettingTests(unittest.TestCase):
    def test_one_answer_per_day(self):
        profile_id = make_profile("Workout Answers")
        day = date(2026, 11, 14)
        self.assertIsNone(repository.get_workout_status(profile_id, day))
        repository.set_workout(profile_id, day, repository.WORKOUT_DONE)
        repository.set_workout(profile_id, day, repository.WORKOUT_NOT_SCHEDULED)
        self.assertEqual(repository.get_workout_status(profile_id, day), "not_scheduled")
        self.assertEqual(len(repository.get_workouts(profile_id)), 1)
        repository.clear_workout(profile_id, day)
        self.assertIsNone(repository.get_workout_status(profile_id, day))
        with self.assertRaises(ValueError):
            repository.set_workout(profile_id, day, "skipped")

    def test_settings(self):
        self.assertEqual(repository.get_setting("missing", "fallback"), "fallback")
        repository.set_setting("language", "uk")
        repository.set_setting("language", "en")
        self.assertEqual(repository.get_setting("language"), "en")


if __name__ == "__main__":
    unittest.main()
