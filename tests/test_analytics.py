"""Owner: backend developer 2 (analytics; NumPy + Statistics + Pandas)."""
import unittest
from datetime import date, datetime

import pandas as pd

from backend.analytics import (coordination, deviations, export, flight, freshness, history,
                               units, workouts)


class FlightTests(unittest.TestCase):
    def test_flight_day_counts_from_one(self):
        start = date(2026, 10, 1)
        self.assertEqual(flight.flight_day(start, date(2026, 10, 1)), 1)
        self.assertEqual(flight.flight_day(start, date(2026, 11, 14)), 45)
        self.assertEqual(flight.flight_day(start, date(2026, 9, 28)), -2)
        self.assertEqual(flight.days_to_launch(start, date(2026, 9, 28)), 3)
        self.assertEqual(flight.days_to_launch(start, date(2026, 10, 5)), 0)

    def test_stages(self):
        stages = [flight.flight_stage(day) for day in (0, 1, 14, 15, 150, 151)]
        self.assertEqual(stages, ["preflight", "adaptation", "adaptation", "main", "main",
                                  "long_duration"])


class FreshnessTests(unittest.TestCase):
    NOW = datetime(2026, 11, 15, 12, 0)

    def test_stale_after_24_hours(self):
        self.assertFalse(freshness.is_stale(datetime(2026, 11, 14, 12, 0), self.NOW))
        self.assertTrue(freshness.is_stale(datetime(2026, 11, 14, 11, 59), self.NOW))
        self.assertTrue(freshness.is_stale(None, self.NOW))

    def test_profile_table(self):
        profiles = pd.DataFrame({
            "name": ["fresh", "late", "never"],
            "last_entry_at": pd.to_datetime(["2026-11-15 09:00", "2026-11-13 09:00", None]),
        })
        result = freshness.with_freshness(profiles, self.NOW)
        self.assertEqual(result["is_stale"].tolist(), [False, True, True])
        self.assertAlmostEqual(result["hours_since_update"].iloc[0], 3.0)
        self.assertEqual(len(freshness.with_freshness(profiles.iloc[0:0], self.NOW)), 0)


class DeviationTests(unittest.TestCase):
    def test_trend(self):
        self.assertEqual(deviations.trend([70, 70, 70, 70]), deviations.FLAT)
        self.assertEqual(deviations.trend([75, 74, 72.5, 71, 70]), deviations.DOWN)
        self.assertEqual(deviations.trend([60, 66, 72]), deviations.UP)
        self.assertEqual(deviations.trend([35.6, 35.3, 35.4, 35.0, 34.9, 34.7, 34.5]),
                         deviations.DOWN)
        self.assertEqual(deviations.trend([8, 7, 8, 9, 8, 8, 9]), deviations.FLAT)
        self.assertEqual(deviations.trend([60, 80]), deviations.UNKNOWN)
        self.assertEqual(deviations.trend([60, None, float("nan"), 80]), deviations.UNKNOWN)

    def test_zscore(self):
        self.assertAlmostEqual(deviations.zscore(80, [60, 70, 80]), 1.0)
        self.assertIsNone(deviations.zscore(80, [70, 70, 70]))
        self.assertIsNone(deviations.zscore(80, [70, 71]))

    def test_comparison_table(self):
        history_frame = pd.DataFrame({"heart_rate_bpm": [62, 70, 78, 86],
                                      "mass_kg": [75.0, 75.0, 74.9, 75.0]})
        table = deviations.comparison_table(
            {"heart_rate_bpm": 86, "mass_kg": 75.0}, {"heart_rate_bpm": 62, "mass_kg": 75.0},
            history_frame, keys=("heart_rate_bpm", "mass_kg", "spo2_pct")).set_index("metric")
        self.assertEqual(table.loc["heart_rate_bpm", "change"], 24)
        self.assertAlmostEqual(table.loc["heart_rate_bpm", "change_pct"], 24 / 62 * 100)
        self.assertEqual(table.loc["heart_rate_bpm", "recent"], 74)
        self.assertEqual(table.loc["heart_rate_bpm", "trend"], deviations.UP)
        self.assertEqual(table.loc["mass_kg", "trend"], deviations.FLAT)
        self.assertTrue(pd.isna(table.loc["spo2_pct", "current"]))

    def test_changed_keys(self):
        old = {"heart_rate_bpm": 62, "vision_clear": None, "mass_kg": 75.0}
        new = {"heart_rate_bpm": 70, "vision_clear": 1, "mass_kg": 75.0}
        self.assertEqual(deviations.changed_keys(new, old), {"heart_rate_bpm", "vision_clear"})
        self.assertEqual(deviations.changed_keys(new, None), set())


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.entries = pd.DataFrame({
            "id": [1, 2, 3],
            "recorded_at": pd.to_datetime(["2026-11-03 08:00", "2026-11-03 20:30",
                                           "2026-11-14 09:00"]),
        })
        self.runs = pd.DataFrame({
            "id": [10, 11, 12],
            "entry_id": [1, 1, 3],
            "environment": ["earth", "orbit", "orbit"],
            "flight_day": [34, 34, 45],
            "overall_severity": [2, 1, 0],
            "diagnosed_at": pd.to_datetime(["2026-11-03 08:00", "2026-11-03 08:05",
                                            "2026-11-14 09:00"]),
        })

    def test_calendar_helpers(self):
        self.assertEqual(history.month_grid(2026, 11)[0], [0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(history.shift_month(2026, 12, 1), (2027, 1))
        self.assertEqual(history.shift_month(2026, 1, -1), (2025, 12))
        self.assertEqual(history.month_bounds(2026, 12),
                         (datetime(2026, 12, 1), datetime(2027, 1, 1)))

    def test_day_summary_uses_the_latest_diagnosis_of_each_entry(self):
        summary = history.day_summary(self.entries, self.runs)
        self.assertEqual(summary, {3: {"entries": 2, "severity": 1},
                                   14: {"entries": 1, "severity": 0}})
        without_runs = history.day_summary(self.entries, self.runs.iloc[0:0])
        self.assertEqual(without_runs[3], {"entries": 2, "severity": None})
        self.assertEqual(history.day_summary(self.entries.iloc[0:0], self.runs), {})

    def test_entries_on_a_day(self):
        self.assertEqual(history.entries_on(self.entries, date(2026, 11, 3))["id"].tolist(), [1, 2])
        self.assertTrue(history.entries_on(self.entries, date(2026, 11, 4)).empty)

    def test_runs_grouped_by_entry(self):
        findings = pd.DataFrame({"run_id": [10, 10, 11], "code": ["FEVER", "HYPOXEMIA", "FEVER"],
                                 "severity": [2, 1, 1], "zone": ["whole_body", "lungs", "whole_body"]})
        grouped = history.runs_by_entry(self.runs, findings)
        self.assertEqual([run["id"] for run in grouped[1]], [10, 11])
        self.assertEqual(len(grouped[1][0]["findings"]), 2)
        self.assertEqual(grouped[3][0]["findings"], [])
        self.assertEqual(grouped[1][0]["diagnosed_at"], datetime(2026, 11, 3, 8, 0))


class WorkoutTests(unittest.TestCase):
    def setUp(self):
        days = ["2026-10-30", "2026-11-01", "2026-11-03", "2026-11-05", "2026-11-08",
                "2026-11-10", "2026-11-12", "2026-11-13", "2026-11-14"]
        status = ["done"] * 7 + ["not_scheduled", "done"]
        self.frame = pd.DataFrame({"day": pd.to_datetime(days), "status": status})

    def test_reminder_until_answered(self):
        self.assertTrue(workouts.needs_reminder(None))
        self.assertFalse(workouts.needs_reminder(workouts.DONE))
        self.assertFalse(workouts.needs_reminder(workouts.NOT_SCHEDULED))

    def test_month_marks_and_count(self):
        marks = workouts.month_marks(self.frame, 2026, 11)
        self.assertEqual(marks[13], workouts.NOT_SCHEDULED)
        self.assertEqual(marks[14], workouts.DONE)
        self.assertNotIn(30, marks)
        self.assertEqual(workouts.done_in_month(self.frame, 2026, 11), 7)
        self.assertEqual(workouts.month_marks(self.frame.iloc[0:0], 2026, 11), {})

    def test_weekly_average(self):
        self.assertEqual(workouts.weekly_average(self.frame, date(2026, 11, 15)), 2.0)
        self.assertEqual(workouts.weekly_average(self.frame.iloc[0:0], date(2026, 11, 15)), 0.0)


class CoordinationTests(unittest.TestCase):
    def payload(self, distances):
        return {"id": 1, "distances": distances, "radius_px": 30, "interval_ms": 1000 / 30,
                "duration_s": len(distances) / 30}

    def test_score_is_the_share_of_time_on_target(self):
        result = coordination.summarize(self.payload([5.0] * 60 + [45.0] * 30 + [-1] * 30))
        self.assertEqual(result.score_pct, 50)
        self.assertEqual((result.on_target_s, result.total_s), (2.0, 4.0))
        self.assertEqual(result.longest_hold_s, 2.0)
        self.assertEqual(result.median_distance_px, 5.0)

    def test_edges(self):
        self.assertEqual(coordination.summarize(self.payload([30.0])).score_pct, 100)
        self.assertEqual(coordination.summarize(self.payload([30.1])).score_pct, 0)
        nothing = coordination.summarize(self.payload([-1, -1]))
        self.assertEqual((nothing.score_pct, nothing.median_distance_px), (0, None))

    def test_longest_run(self):
        hits = coordination.on_target([1, 1, 99, 1, 1, 1, 99], 30)
        self.assertEqual(coordination.longest_run(hits), 3)

    def test_junk_is_rejected(self):
        for bad in ({}, self.payload([]), self.payload(["x"]), self.payload([1.0, float("nan")]),
                    {**self.payload([1.0]), "radius_px": 0}, {"distances": "junk"}):
            with self.assertRaises(ValueError):
                coordination.summarize(bad)


class UnitTests(unittest.TestCase):
    def test_glucose_round_trip(self):
        self.assertAlmostEqual(units.glucose_from_mmol(5.0, units.MG_DL), 90.08)
        self.assertAlmostEqual(units.glucose_to_mmol(90.08, units.MG_DL), 5.0)
        self.assertEqual(units.glucose_to_mmol(5.0, units.MMOL_L), 5.0)


class CoordinationProgressTests(unittest.TestCase):
    @staticmethod
    def entries(rows):
        return pd.DataFrame({
            "recorded_at": pd.to_datetime([r[0] for r in rows]),
            "source": [r[1] for r in rows],
            "coordination_pct": [r[2] for r in rows]})

    def test_only_saved_tests_count(self):
        frame = self.entries([("2026-11-01", "baseline", 90), ("2026-11-02", "game", 70),
                              ("2026-11-03", "manual", 70), ("2026-11-04", "game", 80)])
        result = coordination.progress(frame)
        self.assertEqual(list(result.series["score"]), [70, 80])
        self.assertEqual((result.best, result.latest), (80, 80))

    def test_trend_is_last_tests_against_first_tests(self):
        scores = [50, 60, 70, 80, 90, 100]
        frame = self.entries([(f"2026-11-{i + 1:02d}", "game", v) for i, v in enumerate(scores)])
        result = coordination.progress(frame)
        self.assertEqual((result.mean_first, result.mean_last, result.change), (60.0, 90.0, 30.0))

    def test_no_tests_means_no_progress(self):
        self.assertIsNone(coordination.progress(self.entries([("2026-11-01", "baseline", 90)])))
        self.assertIsNone(coordination.progress(pd.DataFrame()))


class ExportTests(unittest.TestCase):
    def test_metrics_table_has_time_and_every_metric(self):
        from data import catalog
        entries = pd.DataFrame([{"recorded_at": pd.Timestamp("2026-11-15 08:30:05"),
                                 "environment": "mars", "source": "manual",
                                 **{key: 1.0 for key in catalog.KEYS}, "id": 7}])
        table = export.metrics_table(entries)
        self.assertEqual(list(table.columns), ["recorded_at", "environment", "source",
                                               *catalog.KEYS])
        self.assertEqual(table.loc[0, "recorded_at"], "2026-11-15 08:30:05")

    def test_diagnoses_table_keeps_runs_without_findings(self):
        runs = pd.DataFrame({"id": [1, 2], "entry_id": [1, 1], "environment": ["mars", "moon"],
                             "flight_day": [10, 10], "overall_severity": [2, 0],
                             "diagnosed_at": pd.to_datetime(["2026-11-15 09:00:00"] * 2),
                             "entry_recorded_at": pd.to_datetime(["2026-11-15 08:30:00"] * 2)})
        found = pd.DataFrame({"run_id": [1], "code": ["TACHYCARDIA"], "severity": [2],
                              "zone": ["heart"]})
        table = export.diagnoses_table(runs, found, lambda code: f"Suspected {code}")
        self.assertEqual(len(table), 2)
        self.assertEqual(table.loc[0, "diagnosis"], "Suspected TACHYCARDIA")
        self.assertEqual(table.loc[1, "diagnosis"], "")

    def test_csv_starts_with_byte_order_mark(self):
        data = export.to_csv(pd.DataFrame({"a": ["Підозра"]}))
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertIn("Підозра".encode("utf-8"), data)


if __name__ == "__main__":
    unittest.main()
