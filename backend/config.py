"""Runtime configuration for the N06/E2 backend."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP_ID = "N06"
PREFIX = f"ce339/{GROUP_ID}/e2"
BROKER = os.environ.get("MQTT_HOST", "test.mosquitto.org")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
DB_PATH = os.environ.get("DB_PATH", str(ROOT / "artifacts" / "iot.db"))
TTL = int(os.environ.get("COMMAND_TTL", "15"))
LIVE_TTL = 45
RETRY_INTERVAL = 1
SUB_TELE = PREFIX + "/+/telemetry"
SUB_STATUS = PREFIX + "/+/status"
SUB_ACK = PREFIX + "/+/ack"
MODES = ("normal", "imbalance", "loose")
SOURCES = ("synthetic", "mpu6050")
if TTL <= 0 or not 1 <= PORT <= 65535:
    raise ValueError("COMMAND_TTL must be positive and MQTT_PORT must be valid")
