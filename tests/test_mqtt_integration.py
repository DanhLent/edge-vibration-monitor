import asyncio
import json
import logging
import socket
import threading
import time
import unittest
from unittest.mock import patch

from amqtt.broker import Broker
from fastapi.testclient import TestClient
import paho.mqtt.client as mqtt

from backend import config
from backend.api import create_app
from tests.test_backend import FIXTURES, status, telemetry

logging.getLogger("amqtt").setLevel(logging.ERROR)


class LocalBroker:
    def __init__(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.error = None
        self.broker = None
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        asyncio.set_event_loop(self.loop)
        async def start():
            self.broker = Broker({"listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{self.port}"}},
                                  "plugins": {"amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True}}})
            await self.broker.start()
        try:
            self.loop.run_until_complete(start())
            self.ready.set()
            self.loop.run_forever()
        except Exception as exc:
            self.error = exc
            self.ready.set()
        finally:
            self.loop.close()

    def start(self):
        self.thread.start()
        if not self.ready.wait(10):
            raise RuntimeError("Local broker startup timed out")
        if self.error:
            raise self.error
        return self

    def stop(self):
        if self.broker and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broker.shutdown(), self.loop).result(timeout=10)
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=10)


class MqttIntegrationTests(unittest.TestCase):
    def test_telemetry_control_ack_and_disconnect(self):
        broker = LocalBroker().start()
        device = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ce339-n06-verification-peer")
        subscribed = threading.Event()
        def on_connect(client, userdata, flags, reason, properties):
            client.subscribe(f"{config.PREFIX}/esp32-01/cmd", qos=1)
        device.on_connect = on_connect
        device.on_subscribe = lambda *args: subscribed.set()
        received_commands = []
        applied = []
        cached = {}
        def on_message(client, userdata, message):
            command = json.loads(message.payload)
            received_commands.append(command)
            if command["id"] not in cached:
                applied.append(command["mode"])
                cached[command["id"]] = {**FIXTURES["ack"], "id": command["id"], "mode": command["mode"]}
                return  # Deliberately lose the first ACK after applying the command.
            client.publish(f"{config.PREFIX}/esp32-01/ack", json.dumps(cached[command["id"]]), qos=0, retain=False)
            client.publish(f"{config.PREFIX}/esp32-01/status", json.dumps(status(mode=command["mode"])), qos=0, retain=True)
        device.on_message = on_message
        try:
            device.connect("127.0.0.1", broker.port, 15)
            device.loop_start()
            self.assertTrue(subscribed.wait(5))
            device.publish(f"{config.PREFIX}/esp32-01/status", json.dumps(status()), qos=0, retain=True).wait_for_publish(5)
            with patch.object(config, "BROKER", "127.0.0.1"), patch.object(config, "PORT", broker.port):
                app = create_app(":memory:")
                with TestClient(app) as client:
                    self.assertTrue(app.state.ing.subscribed.wait(5))
                    deadline = time.monotonic() + 5
                    while app.state.db.device("esp32-01") is None and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(app.state.db.device("esp32-01")["connection"], "unknown")
                    self.assertEqual(client.post("/api/v1/devices/esp32-01/commands",
                                                 json={"action": "set_mode", "mode": "loose"}).status_code, 409)
                    device.publish(f"{config.PREFIX}/esp32-01/status", json.dumps(status()), qos=0, retain=True).wait_for_publish(5)
                    device.publish(f"{config.PREFIX}/esp32-01/telemetry",
                                   json.dumps(telemetry()), qos=0).wait_for_publish(5)
                    deadline = time.monotonic() + 5
                    while app.state.db.count() == 0 and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(app.state.db.count(), 1)
                    self.assertIsNone(client.get("/api/v1/devices/esp32-01/latest").json()["prediction"])
                    response = client.post("/api/v1/devices/esp32-01/commands",
                                           json={"action": "set_mode", "mode": "loose"})
                    self.assertEqual(response.status_code, 202)
                    cid = response.json()["command_id"]
                    deadline = time.monotonic() + 5
                    while app.state.db.get_command(cid)["state"] == "pending" and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(app.state.db.get_command(cid)["state"], "done")
                    deadline = time.monotonic() + 5
                    while app.state.db.device("esp32-01")["mode"] != "loose" and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(applied, ["loose"])
                    self.assertGreaterEqual(len(received_commands), 2)
                    self.assertEqual(received_commands[0], received_commands[1])
                    self.assertEqual(client.get("/api/v1/devices").json()[0]["mode"], "loose")
                    app.state.ing.stop()
                    self.assertFalse(client.get("/api/v1/stats").json()["broker_connected"])
                    app.state.ing.start()
                    self.assertTrue(app.state.ing.subscribed.wait(5))
                    self.assertNotEqual(app.state.db.device("esp32-01")["connection"], "online")
                    device.publish(f"{config.PREFIX}/esp32-01/status", json.dumps(status(mode="loose")), qos=0, retain=True).wait_for_publish(5)
                    device.publish(f"{config.PREFIX}/esp32-01/telemetry", json.dumps(telemetry()), qos=0).wait_for_publish(5)
                    deadline = time.monotonic() + 5
                    while app.state.ing.n_msg < 2 and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(app.state.db.count(), 1)
                    self.assertEqual(app.state.db.device("esp32-01")["mode"], "loose")
        finally:
            device.disconnect()
            device.loop_stop()
            broker.stop()
