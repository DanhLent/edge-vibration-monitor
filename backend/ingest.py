"""MQTT ingestion and bounded command retries, adapted from TH4."""
import json
import threading
import time
import uuid
from collections import deque

import paho.mqtt.client as mqtt

from . import config
from .codec import DEVICE_ID, decode_ack, decode_status, decode_telemetry


class Ingestor:
    def __init__(self, db, publish=None):
        self.db = db
        self.publish = publish or self._mqtt_publish
        self.cli = None
        self.connected = threading.Event()
        self.subscribed = threading.Event()
        self.lock = threading.RLock()
        self.n_msg = 0
        self.n_bad = 0
        self.payload_bytes = 0
        self.log = deque(maxlen=30)

    def note(self, message):
        with self.lock:
            self.log.appendleft(f"{time.strftime('%H:%M:%S')} {message}")

    def handle(self, topic, payload, received_at=None, retained=False):
        received_at = time.time() if received_at is None else received_at
        parts = topic.split("/")
        try:
            if len(parts) != 5 or "/".join(parts[:3]) != config.PREFIX or not DEVICE_ID.fullmatch(parts[3]):
                raise ValueError("invalid topic")
            device_id, kind = parts[3:]
            if kind == "telemetry":
                if retained:
                    raise ValueError("telemetry must not be retained")
                message = decode_telemetry(payload)
                self.db.insert_telemetry(device_id, message, received_at)
                with self.lock:
                    self.n_msg += 1
                    self.payload_bytes += len(payload)
            elif kind == "status":
                if not payload:
                    return True
                self.db.set_status(device_id, decode_status(payload), received_at, retained)
            elif kind == "ack":
                if retained:
                    raise ValueError("acknowledgments must not be retained")
                message = decode_ack(payload)
                command = self.db.get_command(message["id"])
                device = self.db.device(device_id, received_at)
                if command and command["device_id"] == device_id and device and device["boot_id"] == message["boot_id"]:
                    result = message["result"]
                    if result == "done" and message["mode"] != command["mode"]:
                        result = "bad_mode"
                    state = self.db.complete_command(message["id"], result, received_at)
                    self.note(f"Command {message['id']}: {state}")
            else:
                raise ValueError("unsupported topic kind")
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
            with self.lock:
                self.n_bad += 1
            return False
        return True

    def send_command(self, device_id, cid, mode, expires_at):
        message = {"schema_version": 1, "id": cid, "action": "set_mode", "mode": mode, "exp": int(expires_at)}
        self.publish(f"{config.PREFIX}/{device_id}/cmd", json.dumps(message, separators=(",", ":")))

    def retry_pending(self, now=None):
        now = time.time() if now is None else now
        self.db.expire_commands(now)
        if not self.connected.is_set() or not self.subscribed.is_set():
            return
        for command in self.db.claim_retries(now):
            try:
                self.send_command(command["device_id"], command["id"], command["mode"], command["expires_at"])
            except (RuntimeError, OSError, ValueError) as exc:
                self.note(f"Command retry deferred: {type(exc).__name__}")

    def _mqtt_publish(self, topic, payload):
        if self.cli is None or not self.connected.is_set() or not self.subscribed.is_set():
            raise RuntimeError("MQTT broker disconnected or unsubscribed")
        info = self.cli.publish(topic, payload, qos=1, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(mqtt.error_string(info.rc))

    def start(self):
        def on_connect(client, userdata, flags, reason, properties):
            if not reason.is_failure:
                self.db.reset_presence()
                code, _ = client.subscribe([(config.SUB_TELE, 0), (config.SUB_STATUS, 1), (config.SUB_ACK, 0)])
                if code == mqtt.MQTT_ERR_SUCCESS:
                    self.connected.set()
            self.note(f"MQTT connection: {reason}")

        def on_subscribe(client, userdata, mid, reasons, properties):
            if reasons and all(not reason.is_failure for reason in reasons):
                self.subscribed.set()

        def on_message(client, userdata, message):
            try:
                self.handle(message.topic, message.payload, retained=message.retain)
            except Exception as exc:
                with self.lock:
                    self.n_bad += 1
                self.note(f"Ingestion failed: {type(exc).__name__}")

        def on_disconnect(client, userdata, flags, reason, properties):
            self.connected.clear()
            self.subscribed.clear()
            self.db.reset_presence()
            self.note(f"MQTT disconnected: {reason}")

        self.cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ce339-N06-backend-{uuid.uuid4().hex[:8]}")
        self.cli.on_connect = on_connect
        self.cli.on_subscribe = on_subscribe
        self.cli.on_message = on_message
        self.cli.on_disconnect = on_disconnect
        self.cli.reconnect_delay_set(min_delay=1, max_delay=10)
        self.cli.connect_async(config.BROKER, config.PORT, keepalive=30)
        self.cli.loop_start()

    def stop(self):
        if self.cli:
            self.cli.disconnect()
            self.cli.loop_stop()
        self.connected.clear()
        self.subscribed.clear()
