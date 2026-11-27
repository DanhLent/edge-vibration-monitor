"""v1 and v2 interoperability for spectral telemetry and history."""
import json
from pathlib import Path
import unittest

from backend.codec import decode_telemetry
from backend.db import DB

FIXTURE = json.loads((Path(__file__).parent / "fixtures/interfaces.json").read_text())["telemetry"]


def advanced(**changes):
    return {**FIXTURE, "window_id": 2, "schema_version": 2, "prediction": "normal",
            "model_ready": True, "model_variant": "fft",
            "spectrum": {"p1x": .008, "p2x": .001, "fft_us": 50000}, **changes}


class SpectrumTests(unittest.TestCase):
    def test_mixed_history(self):
        db = DB(":memory:")
        self.addCleanup(db.close)
        for index, message in enumerate((FIXTURE, advanced(), advanced(
                window_id=3, model_variant="baseline", spectrum=None))):
            self.assertTrue(db.insert_telemetry("esp32-test", decode_telemetry(json.dumps(message).encode()), index))
        self.assertEqual(db.history("esp32-test", 0, 5, "p1x"), [{"t": 1, "v": .008}])
        self.assertEqual(db.history("esp32-test", 0, 5, "p2x"), [{"t": 1, "v": .001}])
        self.assertEqual(len(db.history("esp32-test", 0, 5)), 3)
        self.assertEqual(db.latest("esp32-test")["model_variant"], "baseline")
        with self.assertRaises(ValueError):
            db.history("esp32-test", 0, 5, "NOT_SQL")

    def test_invalid_fft_shapes_and_values(self):
        for changes in (
            {"spectrum": None}, {"model_variant": "foreign"}, {"sample_count": 999, "actual_hz": 999},
            {"spectrum": {"p1x": .5, "p2x": 0, "fft_us": 4}},
            {"spectrum": {"p1x": 0, "p2x": float("nan"), "fft_us": 4}},
            {"spectrum": {"p1x": .008, "p2x": .001, "fft_us": True}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                decode_telemetry(json.dumps(advanced(**changes)).encode())
