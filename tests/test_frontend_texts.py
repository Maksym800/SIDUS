import re
import string
import unittest
from pathlib import Path

from backend.analytics import flight
from data import catalog
from frontend import body_map, engine_help, i18n

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


class TextTests(unittest.TestCase):
    def test_every_text_exists_in_both_languages(self):
        for key, pair in i18n.TEXTS.items():
            with self.subTest(key=key):
                self.assertEqual(len(pair), len(i18n.LANGUAGES))
                self.assertTrue(all(text.strip() for text in pair))
                self.assertEqual(placeholders(pair[0]), placeholders(pair[1]))

    def test_every_metric_can_be_shown(self):
        for metric in catalog.METRICS:
            self.assertIn(f"metric.{metric.key}", i18n.TEXTS)
            self.assertIn(f"group.{metric.group}", i18n.TEXTS)
            if metric.unit:
                self.assertIn(f"unit.{metric.unit}", i18n.TEXTS)
            if metric.kind in (catalog.CHOICE, catalog.FLAG):
                for code in metric.choices:
                    self.assertIn(f"option.{metric.key}.{code}", i18n.TEXTS)

    def test_environments_zones_stages_and_severities_have_names(self):
        expected = [f"env.{code}" for code in catalog.ENVIRONMENTS]
        expected += [f"zone.{zone}" for zone in body_map.ZONES]
        expected += [f"severity.{level}" for level in (0, 1, 2)]
        expected += [f"stage.{stage}" for stage in
                     (flight.PREFLIGHT, flight.ADAPTATION, flight.MAIN, flight.LONG_DURATION)]
        expected += [f"history.source.{source}" for source in catalog.SOURCES]
        for key in expected:
            self.assertIn(key, i18n.TEXTS)

    def test_calendar_names(self):
        for language in i18n.LANGUAGES:
            self.assertEqual(len(i18n.MONTHS[language]), 12)
            self.assertEqual(len(i18n.MONTHS_IN_DATES[language]), 12)
            self.assertEqual(len(i18n.WEEKDAYS[language]), 7)

    def test_every_text_id_used_in_the_code_exists(self):
        used = set()
        for source in FRONTEND.rglob("*.py"):
            used.update(re.findall(r"""\bt\(\s*["']([a-z_.0-9]+)["']""", source.read_text("utf-8")))
        self.assertTrue(used, "no text ids found; has the code layout changed?")
        self.assertEqual(sorted(key for key in used if key not in i18n.TEXTS), [])


class EngineHelpTests(unittest.TestCase):
    def test_every_system_has_all_its_texts(self):
        for key in engine_help._INSTALL:
            for prefix in ("engine.os.", "engine.step_install.", "engine.step_restart."):
                with self.subTest(key=key, prefix=prefix):
                    self.assertIn(prefix + key, i18n.TEXTS)

    def test_detected_system_is_known(self):
        self.assertIn(engine_help.system(), engine_help._INSTALL)


class BodyMapTests(unittest.TestCase):
    def test_every_zone_has_a_marker_inside_the_picture(self):
        for zone, layout in body_map.ZONE_LAYOUT.items():
            for x, y in layout["points"]:
                with self.subTest(zone=zone):
                    self.assertTrue(0 < x < 100 and 0 < y < 100)

    def test_anatomy_picture_is_present_and_transparent(self):
        path = body_map.image_path()
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "anatomy.png")
        self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(path.read_bytes()[25], 6)


if __name__ == "__main__":
    unittest.main()
