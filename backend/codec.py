"""Validate the v1 wire contract before storage or command completion."""
import json
import math
import re

from .config import MODES, SOURCES

DEVICE_ID = re.compile(r"[A-Za-z0-9_-]{1,32}")
COMMAND_ID = re.compile(r"[A-Za-z0-9_-]{1,15}")
BOOT_ID = re.compile(r"[0-9a-f]{8}")
NUMERIC_FIELDS = ("rms", "peak", "crest_factor", "actual_hz")
INTEGER_FIELDS = ("uptime_ms", "window_id", "fs_hz", "sample_count", "missed_samples", "window_duration_us")
RESULTS = ("done", "bad", "expired", "clock", "unsupported")


def decode_object(payload):
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("message must be an object")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported schema version")
    boot = value.get("boot_id")
    if not isinstance(boot, str) or not BOOT_ID.fullmatch(boot):
        raise ValueError("boot_id must be eight lowercase hexadecimal digits")
    return value


def require_keys(value, keys):
    if set(value) != set(keys):
        raise ValueError("fields do not match the v1 contract")


def validate_source(value):
    if value["source"] not in SOURCES or value["mode"] not in (*MODES, None):
        raise ValueError("invalid source or simulation mode")
    if (value["source"] == "synthetic") != (value["mode"] is not None):
        raise ValueError("only synthetic messages have a simulation mode")


def decode_telemetry(payload):
    value = decode_object(payload)
    keys = ("schema_version", "boot_id", "ts", *INTEGER_FIELDS, *NUMERIC_FIELDS,
            "source", "mode", "prediction", "sensor_ok", "model_ready")
    require_keys(value, keys)
    for key in NUMERIC_FIELDS:
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
    for key in INTEGER_FIELDS:
        number = value[key]
        if type(number) is not int or number < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    if not 200 <= value["fs_hz"] <= 1000 or not value["sample_count"] or not value["window_id"]:
        raise ValueError("invalid sampling configuration")
    duration = value["window_duration_us"]
    if duration < 1_000_000 or value["actual_hz"] <= 0:
        raise ValueError("invalid window duration or measured rate")
    expected_rate = value["sample_count"] * 1_000_000 / duration
    if not math.isclose(value["actual_hz"], expected_rate, rel_tol=1e-4, abs_tol=1e-6):
        raise ValueError("measured rate does not match count and duration")
    ts = value["ts"]
    if ts is not None and (type(ts) is not int or ts < 0):
        raise ValueError("ts must be Unix seconds or null")
    validate_source(value)
    if type(value["sensor_ok"]) is not bool or type(value["model_ready"]) is not bool:
        raise ValueError("sensor_ok and model_ready must be boolean")
    if value["source"] == "mpu6050" and not value["sensor_ok"]:
        raise ValueError("failed physical acquisitions cannot produce valid windows")
    if value["model_ready"]:
        if value["prediction"] not in MODES:
            raise ValueError("a ready model must report a prediction")
    elif value["prediction"] is not None:
        raise ValueError("an unavailable model cannot report a prediction")
    if value["peak"] + 1e-6 < value["rms"]:
        raise ValueError("peak cannot be smaller than RMS")
    expected_crest = value["peak"] / value["rms"] if value["rms"] else 0
    if not value["rms"] and value["peak"]:
        raise ValueError("a zero RMS signal must have zero peak")
    if not math.isclose(value["crest_factor"], expected_crest, rel_tol=1e-4, abs_tol=1e-6):
        raise ValueError("crest factor does not match peak/RMS")
    return value


def decode_status(payload):
    value = decode_object(payload)
    connection = value.get("connection")
    keys = ("schema_version", "boot_id", "connection")
    if connection == "online":
        keys += ("source", "mode", "sensor_ok", "clock_ready", "sampling_ok", "model_ready")
        validate_source(value)
        for key in ("sensor_ok", "clock_ready", "sampling_ok", "model_ready"):
            if type(value[key]) is not bool:
                raise ValueError(f"{key} must be boolean")
    elif connection != "offline":
        raise ValueError("invalid connection status")
    require_keys(value, keys)
    return value


def decode_ack(payload):
    value = decode_object(payload)
    require_keys(value, ("schema_version", "boot_id", "id", "result", "mode"))
    cid = value["id"]
    if not isinstance(cid, str) or not COMMAND_ID.fullmatch(cid):
        raise ValueError("invalid command ID")
    if value["result"] not in RESULTS:
        raise ValueError("invalid acknowledgment result")
    if value["result"] == "done":
        if value["mode"] not in MODES:
            raise ValueError("done must include the applied mode")
    elif value["mode"] is not None:
        raise ValueError("failed commands have null applied mode")
    return value
