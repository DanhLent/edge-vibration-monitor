import argparse
import csv
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import paho.mqtt.client as mqtt

from backend import config
from backend.api import create_app
from backend.db import DB
from backend.ingest import Ingestor
from scripts.capture_wokwi import Observer, decode_message, safe_url
from scripts.export_measurements import export_run, sha256, write_json
from tests.test_backend import FIXTURES, status, telemetry
from tests.test_mqtt_integration import LocalBroker


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        write_json(self.directory / "run.json", dict(run_id="software-peer-test", device_id="esp32-01",
                   source="software-peer synthetic", result="INCOMPLETE", boot_id="1234abcd", attempts=[], findings=[]))

    def tearDown(self):
        self.temporary.cleanup()

    def rows(self, name):
        with (self.directory / "measurements" / name).open() as stream:
            return list(csv.DictReader(stream))

    def test_bytes_duplicates_retained_and_full_windows(self):
        db = DB(self.directory / "backend.db")
        ingestor = Ingestor(db)
        observer = Observer(self.directory, "esp32-01")
        topic = config.PREFIX + "/esp32-01/telemetry"
        values = [telemetry(window_id=1, uptime_ms=1000), telemetry(window_id=2, uptime_ms=2000)]
        payload = json.dumps(values[0], indent=2).encode()
        observer.record(topic, payload, wall=100, monotonic=10)
        ingestor.handle(topic, payload, received_at=100.1)
        observer.record(topic, payload, dup=True, wall=100.5, monotonic=10.5)
        ingestor.handle(topic, payload, received_at=100.6)
        observer.record(topic, payload, retained=True, wall=100.7, monotonic=10.7)
        ingestor.handle(topic, payload, received_at=100.8, retained=True)
        observer.record(topic, b"invalid", wall=100.9, monotonic=10.9)
        ingestor.handle(topic, b"invalid", received_at=100.9)
        second = json.dumps(values[1]).encode()
        observer.record(topic, second, wall=102, monotonic=12)
        ingestor.handle(topic, second, received_at=102.2)
        observer.close()
        db.close()
        before = sha256(self.directory / "backend.db")
        result = export_run(self.directory)
        self.assertEqual(sha256(self.directory / "backend.db"), before)
        self.assertEqual(result["stored_windows"], 2)
        self.assertEqual(result["observed_messages"], 5)
        self.assertEqual(result["observed_payload_bytes"], 3 * len(payload) + len(second) + 7)
        rows = self.rows("sampling.csv")
        self.assertEqual(int(rows[0]["payload_bytes"]), len(payload))
        self.assertEqual(float(rows[1]["device_cadence_ms"]), 1000)
        self.assertEqual(float(rows[1]["observer_cadence_ms"]), 2000)
        self.assertAlmostEqual(float(rows[1]["backend_cadence_ms"]), 2100)
        self.assertEqual(sum(int(row["mqtt_dup_messages"]) for row in self.rows("traffic.csv")), 1)

    def test_latency_uses_persisted_backend_result_and_failures_stay_blank(self):
        db = DB(self.directory / "backend.db")
        observer = Observer(self.directory, "esp32-01")
        for cid, created, end, result in [("cdone", 100, 100.25, "done"), ("cfailed", 101, 101.5, "clock"),
                                          ("cexpired", 102, 117, "expired")]:
            db.create_command(cid, "esp32-01", "loose", created, created + 15)
            db.complete_command(cid, result, end)
        ack = json.dumps({**FIXTURES["ack"], "id": "cdone"}).encode()
        observer.record(config.PREFIX + "/esp32-01/ack", ack, wall=100.4, monotonic=3)
        observer.close()
        db.close()
        export_run(self.directory)
        rows = self.rows("commands.csv")
        self.assertEqual(float(rows[0]["successful_latency_ms"]), 250)
        self.assertEqual(rows[0]["ack_observer_received_at"], "100.4")
        self.assertEqual(rows[1]["successful_latency_ms"], "")
        self.assertEqual(rows[2]["successful_latency_ms"], "")

    def test_cadence_does_not_cross_modes_or_boots_and_wraps_uptime(self):
        db = DB(self.directory / "backend.db")
        for index, value in enumerate([
            telemetry(window_id=1, uptime_ms=(1 << 32) - 500),
            telemetry(window_id=2, uptime_ms=500),
            telemetry(window_id=3, uptime_ms=1500, mode="loose"),
            telemetry(window_id=1, uptime_ms=1000, boot_id="8765abcd"),
        ]):
            db.insert_telemetry("esp32-01", value, 100 + index)
        db.close()
        export_run(self.directory)
        rows = self.rows("sampling.csv")
        self.assertEqual(rows[1]["device_cadence_ms"], "1000")
        self.assertEqual(rows[2]["device_cadence_ms"], "")
        self.assertEqual(rows[3]["device_cadence_ms"], "")

    def test_incomplete_run_exports_headers_without_creating_database(self):
        result = export_run(self.directory)
        self.assertEqual(result["result"], "INCOMPLETE")
        self.assertEqual(result["stored_windows"], 0)
        self.assertFalse((self.directory / "backend.db").exists())
        self.assertEqual(self.rows("sampling.csv"), [])
        self.assertEqual(self.rows("commands.csv"), [])
        self.assertNotIn(b"\r", (self.directory / "measurements" / "sampling.csv").read_bytes())

    def test_public_url_and_command_validation(self):
        self.assertEqual(safe_url("https://wokwi.com/projects/123"), "https://wokwi.com/projects/123")
        for url in ["https://wokwi.com/projects/123?token=private", "https://other.example/projects/123"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                safe_url(url)
        with self.assertRaises(ValueError):
            decode_message("cmd", json.dumps({**FIXTURES["command"], "private": "excluded"}).encode(), False)

    def test_local_mqtt_retry_is_counted_and_backend_ack_is_correlated(self):
        broker = LocalBroker().start()
        device = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ce339-n06-capture-test-peer")
        topic = config.PREFIX + "/esp32-01/"
        transmissions = []
        device.on_connect = lambda c, u, f, r, p: c.subscribe(topic + "cmd", 1)
        def on_command(client, userdata, message):
            command = json.loads(message.payload)
            transmissions.append(command)
            if len(transmissions) == 1:
                return
            client.publish(topic + "ack", json.dumps({**FIXTURES["ack"], "id": command["id"], "mode": command["mode"]}))
            client.publish(topic + "status", json.dumps(status(mode=command["mode"])), retain=True)
            client.publish(topic + "telemetry", json.dumps(telemetry(window_id=2, uptime_ms=2000, mode=command["mode"])))
        device.on_message = on_command
        observer = None
        try:
            with patch.object(config, "BROKER", "127.0.0.1"), patch.object(config, "PORT", broker.port):
                observer = Observer(self.directory, "esp32-01")
                observer.start()
                self.assertTrue(observer.ready.wait(5))
                device.connect("127.0.0.1", broker.port, 15)
                device.loop_start()
                app = create_app(self.directory / "backend.db")
                with TestClient(app) as client:
                    self.assertTrue(app.state.ing.subscribed.wait(5))
                    device.publish(topic + "status", json.dumps(status()), retain=True).wait_for_publish(5)
                    device.publish(topic + "telemetry", json.dumps(telemetry())).wait_for_publish(5)
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        row = app.state.db.device("esp32-01")
                        if row and row["clock_ready"]:
                            break
                        time.sleep(.01)
                    response = client.post("/api/v1/devices/esp32-01/commands", json={"action": "set_mode", "mode": "loose"})
                    self.assertEqual(response.status_code, 202)
                    cid = response.json()["command_id"]
                    deadline = time.monotonic() + 6
                    while time.monotonic() < deadline:
                        command = client.get("/api/v1/commands/" + cid).json()
                        if command["state"] == "done" and app.state.db.count() == 2:
                            break
                        time.sleep(.01)
                    self.assertEqual(command["state"], "done")
                observer.close()
                observer = None
            result = export_run(self.directory)
            self.assertEqual(result["stored_windows"], 2)
            row = self.rows("commands.csv")[0]
            self.assertGreaterEqual(int(row["observed_transmissions"]), 2)
            self.assertGreater(float(row["successful_latency_ms"]), 0)
            self.assertEqual(row["ack_boot_id"], "1234abcd")
            self.assertEqual(row["first_new_mode_window_id"], "2")
        finally:
            if observer:
                observer.close()
            device.disconnect()
            device.loop_stop()
            broker.stop()


if __name__ == "__main__":
    unittest.main()
