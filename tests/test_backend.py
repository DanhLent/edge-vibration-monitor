import json
import math
from pathlib import Path
import tempfile
import time
import unittest

from fastapi.testclient import TestClient
from backend import config
from backend.api import create_app
from backend.db import DB
from backend.ingest import Ingestor

FIXTURES = json.loads((Path(__file__).parent / "fixtures/interfaces.json").read_text())


def telemetry(**changes):
    return {**FIXTURES["telemetry"], "ts": int(time.time()), **changes}


def status(**changes):
    return {**FIXTURES["status"], **changes}


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.published = []
        self.app = create_app(":memory:", start_mqtt=False, publish=lambda *args: self.published.append(args))
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.ing = self.app.state.ing
        self.db = self.app.state.db
        self.ing.connected.set()
        self.ing.subscribed.set()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def seed(self, device="esp32-01", now=None, **changes):
        return self.ing.handle(f"{config.PREFIX}/{device}/telemetry", json.dumps(telemetry(**changes)).encode(), now)

    def online(self, now=None, retained=False, **changes):
        return self.ing.handle(f"{config.PREFIX}/esp32-01/status", json.dumps(status(**changes)).encode(), now, retained)

    def command(self, mode="loose"):
        return self.client.post("/api/v1/devices/esp32-01/commands", json={"action": "set_mode", "mode": mode})

    def ack(self, cid, now=None, retained=False, device="esp32-01", **changes):
        message = {**FIXTURES["ack"], "id": cid, **changes}
        return self.ing.handle(f"{config.PREFIX}/{device}/ack", json.dumps(message).encode(), now, retained)

    def test_storage_history_and_missing_model(self):
        self.assertTrue(self.seed(now=100))
        self.assertTrue(self.seed(now=101, window_id=2, rms=0.3, peak=0.6))
        latest = self.client.get("/api/v1/devices/esp32-01/latest").json()
        self.assertEqual(latest["rms"], 0.3)
        self.assertIsNone(latest["prediction"])
        self.assertFalse(latest["model_ready"])
        response = self.client.get("/api/v1/devices/esp32-01/telemetry?from=100&to=101&field=peak")
        self.assertEqual(response.json(), [{"t": 100.0, "v": 0.4}, {"t": 101.0, "v": 0.6}])

    def test_bad_messages_do_not_break_recovery(self):
        bad_messages = [b"{", b"[]"] + [json.dumps(telemetry(**changes)).encode() for changes in (
            {"rms": math.nan}, {"prediction": "normal"}, {"sample_count": 0},
            {"source": "mpu6050", "mode": "normal"}, {"fs_hz": True}, {"crest_factor": 999},
            {"actual_hz": 0}, {"actual_hz": 900}, {"window_duration_us": 0},
            {"schema_version": True}, {"schema_version": 2}, {"boot_id": "bad"}, {"extra": 1})]
        for payload in bad_messages:
            self.assertFalse(self.ing.handle(f"{config.PREFIX}/esp32-01/telemetry", payload))
        self.assertTrue(self.seed())
        self.assertEqual(self.db.count(), 1)
        self.assertEqual(self.ing.n_bad, len(bad_messages))
        self.assertFalse(self.online(source="mpu6050", mode="loose"))
        self.assertFalse(self.ack("c1", result="anything"))

    def test_namespace_zero_signal_and_physical_health(self):
        payload = json.dumps(telemetry(rms=0, peak=0, crest_factor=0)).encode()
        self.assertFalse(self.ing.handle("ce339/incorrect/e2/esp32-01/telemetry", payload))
        self.assertTrue(self.ing.handle(f"{config.PREFIX}/esp32-01/telemetry", payload))
        self.assertFalse(self.seed(source="mpu6050", mode=None, sensor_ok=False))
        self.assertTrue(self.seed(window_id=2, source="mpu6050", mode=None))

    def test_deduplication_and_status_owns_current_mode(self):
        self.seed()
        self.online(mode="loose")
        self.seed()
        self.seed(window_id=2)
        self.assertEqual(self.db.count(), 2)
        self.assertEqual(self.ing.n_msg, 3)
        self.assertEqual(self.db.device("esp32-01")["mode"], "loose")
        self.assertEqual(self.db.latest("esp32-01")["mode"], "normal")
        self.seed(window_id=1, rms=0.3, peak=0.6)
        self.assertEqual(self.db.latest("esp32-01")["rms"], 0.2)

    def test_new_boot_and_old_last_will(self):
        self.seed()
        self.online(boot_id="abcdef12")
        self.assertIsNone(self.db.latest("esp32-01"))
        self.seed(boot_id="abcdef12")
        self.ing.handle(f"{config.PREFIX}/esp32-01/status", json.dumps(FIXTURES["offline"]).encode())
        self.assertEqual(self.db.device("esp32-01")["connection"], "online")
        self.assertEqual(self.db.count(), 2)

    def test_ack_can_arrive_before_command_response(self):
        self.online()
        def publish(topic, payload):
            command = json.loads(payload)
            self.assertEqual(topic, f"{config.PREFIX}/esp32-01/cmd")
            self.assertEqual(set(command), set(FIXTURES["command"]))
            self.ack(command["id"], mode=command["mode"])
            self.online(mode=command["mode"])
        self.ing.publish = publish
        response = self.command()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["state"], "done")
        self.assertEqual(self.db.device("esp32-01")["mode"], "loose")

    def test_pending_conflict_retry_identity_and_exact_expiry(self):
        self.online()
        response = self.command()
        cid = response.json()["command_id"]
        self.assertEqual(self.command().status_code, 409)
        command = self.db.get_command(cid)
        self.ing.retry_pending(command["created"] + 1.1)
        self.assertEqual(len(self.published), 2)
        self.assertEqual(self.published[0], self.published[1])
        self.ack(cid, now=command["expires_at"])
        self.assertEqual(self.db.get_command(cid)["state"], "expired")
        self.ing.retry_pending(command["expires_at"] + 1)
        self.assertEqual(len(self.published), 2)

    def test_wrong_device_retained_wrong_mode_and_late_ack(self):
        self.online()
        cid = self.command().json()["command_id"]
        self.ack(cid, device="another-device")
        self.assertFalse(self.ack(cid, retained=True))
        self.ack(cid, boot_id="abcdef12")
        self.assertEqual(self.db.get_command(cid)["state"], "pending")
        self.ack(cid, mode="normal")
        self.assertEqual(self.db.get_command(cid)["state"], "failed")
        self.ack(cid)
        self.assertEqual(self.db.get_command(cid)["state"], "failed")

    def test_publish_failure_is_persisted(self):
        self.online()
        def fail(*args):
            raise RuntimeError("broker unavailable")
        self.ing.publish = fail
        result = self.command().json()
        self.assertEqual(result["state"], "failed")
        self.assertEqual(self.db.get_command(result["command_id"])["result"], "publish_failed")

    def test_control_readiness_and_stale_presence(self):
        self.assertEqual(self.command().status_code, 404)
        self.online(retained=True)
        self.assertEqual(self.command().status_code, 409)
        self.online(clock_ready=False)
        self.assertEqual(self.command().status_code, 409)
        self.online(sampling_ok=False)
        self.assertEqual(self.command().status_code, 409)
        self.online(source="mpu6050", mode=None)
        self.assertEqual(self.command().status_code, 409)
        self.online(now=time.time() - 46)
        self.assertNotEqual(self.db.device("esp32-01")["connection"], "online")
        self.assertEqual(self.command().status_code, 409)
        self.online()
        self.assertEqual(self.db.device("esp32-01", now=time.time() + 45)["connection"], "stale")
        self.ing.handle(f"{config.PREFIX}/esp32-01/status", json.dumps(FIXTURES["offline"]).encode())
        self.assertEqual(self.command().status_code, 409)
        self.online()
        self.ing.subscribed.clear()
        self.assertEqual(self.command().status_code, 503)
        self.ing.subscribed.set()
        self.assertEqual(self.command("invalid").status_code, 422)

    def test_backend_restart_recovers_pending_without_cached_presence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "iot.db"
            db = DB(path)
            now = time.time()
            db.set_status("esp32-01", status(), now)
            db.create_command("crestart", "esp32-01", "loose", now, now + 15)
            db.close()
            db = DB(path)
            ing = Ingestor(db, publish=lambda *args: self.published.append(args))
            try:
                self.assertEqual(db.device("esp32-01")["connection"], "unknown")
                db.set_status("esp32-01", status(), time.time(), retained=True)
                self.assertEqual(db.device("esp32-01")["connection"], "unknown")
                ing.connected.set()
                ing.subscribed.set()
                ing.retry_pending(now + 2)
                self.assertEqual(json.loads(self.published[-1][1])["id"], "crestart")
            finally:
                db.close()

    def test_history_and_disconnected_dashboard(self):
        for query in ("from=nan&to=1", "from=2&to=1", "from=0&to=2&field=sql", "to=2",
                      "from=2026-11-21T00:00:00&to=2026-11-22T00:00:00"):
            self.assertEqual(self.client.get("/api/v1/devices/esp32-01/telemetry?" + query).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/devices/unknown/latest").status_code, 404)
        self.ing.connected.clear()
        self.assertFalse(self.client.get("/api/v1/stats").json()["broker_connected"])
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Model unavailable", page.text)
        self.assertIn("Waiting for a device", page.text)
