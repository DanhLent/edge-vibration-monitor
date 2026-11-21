import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from backend.codec import decode_ack, decode_status, decode_telemetry

ROOT = Path(__file__).resolve().parents[1]


class FirmwareTests(unittest.TestCase):
    def test_c_stub_and_window_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="ce339-sampling-") as directory:
            folder = Path(directory)
            obj = folder / "model.o"
            subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-iquote", str(ROOT / "firmware"),
                            "-c", str(ROOT / "firmware/model.c"), "-o", str(obj)], check=True)
            c_test = folder / "model_test"
            subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-iquote", str(ROOT / "firmware"),
                            str(ROOT / "tests/model_test.c"), str(obj), "-o", str(c_test)], check=True)
            subprocess.run([str(c_test)], check=True)
            cpp_test = folder / "sampling_test"
            subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-iquote", str(ROOT / "firmware"),
                            str(ROOT / "tests/sampling_test.cpp"), str(ROOT / "firmware/sampling.cpp"),
                            str(ROOT / "firmware/features.cpp"), str(obj), "-o", str(cpp_test)], check=True)
            subprocess.run([str(cpp_test)], check=True)

    def test_real_firmware_json_and_command_parser(self):
        include = Path(os.environ.get("ARDUINOJSON_INCLUDE", ROOT / ".tools/arduino-user/libraries/ArduinoJson/src"))
        self.assertTrue((include / "ArduinoJson.h").is_file(), "Install ArduinoJson 7.4.3 and set ARDUINOJSON_INCLUDE")
        fixtures = json.loads((ROOT / "tests/fixtures/interfaces.json").read_text())
        with tempfile.TemporaryDirectory(prefix="ce339-protocol-") as directory:
            for synthetic in (True, False):
                binary = Path(directory) / ("synthetic" if synthetic else "physical")
                subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-iquote", str(ROOT / "firmware"),
                                "-I", str(include), "-DEVM_USE_SYNTHETIC=" + str(synthetic).lower(),
                                str(ROOT / "tests/protocol_test.cpp"), str(ROOT / "firmware/protocol.cpp"),
                                str(ROOT / "firmware/model.c"), "-o", str(binary)], check=True)
                result = subprocess.run([str(binary), str(ROOT / "tests/fixtures/interfaces.json")],
                                        check=True, text=True, capture_output=True)
                payloads = [line.encode() for line in result.stdout.splitlines()]
                self.assertEqual(len(payloads), 4)
                expected_telemetry = {**fixtures["telemetry"]}
                expected_status = {**fixtures["status"]}
                if not synthetic:
                    expected_telemetry.update(source="mpu6050", mode=None)
                    expected_status.update(source="mpu6050", mode=None)
                self.assertEqual(decode_telemetry(payloads[0]), expected_telemetry)
                self.assertEqual(decode_status(payloads[1]), expected_status)
                self.assertEqual(decode_ack(payloads[2]), fixtures["ack"])
                self.assertEqual(decode_status(payloads[3]), fixtures["offline"])

    def test_features_against_analytic_signals(self):
        with tempfile.TemporaryDirectory(prefix="ce339-features-") as directory:
            output = Path(directory) / "features_test"
            subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fmax-errors=3",
                            "-iquote", str(ROOT / "firmware"), str(ROOT / "tests/features_test.cpp"),
                            str(ROOT / "firmware/features.cpp"), "-o", str(output)], check=True)
            subprocess.run([str(output)], check=True)

    def test_wiring_matches_firmware(self):
        diagram = json.loads((ROOT / "firmware/diagram.json").read_text())
        config = (ROOT / "firmware/config.h").read_text()
        pins = dict(re.findall(r"(SDA_PIN|SCL_PIN|BUTTON_PIN|GREEN_LED|YELLOW_LED|RED_LED)\s*=\s*(\d+)", config))
        edges = {frozenset(connection[:2]) for connection in diagram["connections"]}
        for pin, endpoint in (("SDA_PIN", "imu:SDA"), ("SCL_PIN", "imu:SCL"), ("BUTTON_PIN", "mode:1.l")):
            self.assertIn(frozenset(("esp:" + pins[pin], endpoint)), edges)
        for i, (pin, color) in enumerate((("GREEN_LED", "green"), ("YELLOW_LED", "yellow"), ("RED_LED", "red"))):
            self.assertIn(frozenset(("esp:" + pins[pin], f"r{i}:1")), edges)
            self.assertIn(frozenset((f"r{i}:2", f"{color}:A")), edges)
            resistor = next(part for part in diagram["parts"] if part["id"] == f"r{i}")
            self.assertEqual(resistor["attrs"]["value"], "220")
        self.assertEqual({part["type"] for part in diagram["parts"]},
                         {"board-esp32-devkit-c-v4", "wokwi-mpu6050", "wokwi-pushbutton", "wokwi-led", "wokwi-resistor"})
