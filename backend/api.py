"""FastAPI/dashboard application adapted from the TH4 backend.

Run from the project root: python -m backend.api
"""
import math
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from . import config
from .db import DB
from .ingest import Ingestor

HERE = Path(__file__).resolve().parent


class CommandIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["set_mode"]
    mode: Literal["normal", "imbalance", "loose"]


def parse_time(value):
    try:
        result = float(value)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("ISO timestamps must include a timezone")
        result = parsed.timestamp()
    if not math.isfinite(result):
        raise ValueError("time must be finite")
    return result


def create_app(db_path=None, start_mqtt=True, publish=None):
    db = DB(db_path or config.DB_PATH)
    ing = Ingestor(db, publish=publish)
    started = time.monotonic()
    stop = threading.Event()

    def service_commands():
        while not stop.wait(1):
            ing.retry_pending()

    @asynccontextmanager
    async def lifespan(app):
        if start_mqtt:
            ing.start()
        worker = threading.Thread(target=service_commands, daemon=True)
        worker.start()
        try:
            yield
        finally:
            stop.set()
            worker.join(timeout=2)
            ing.stop()
            db.close()

    app = FastAPI(title="CE339 N06 — E2 vibration monitor", lifespan=lifespan)
    app.state.db = db
    app.state.ing = ing

    @app.get("/")
    def index():
        return FileResponse(HERE / "static" / "index.html")

    @app.get("/api/v1/devices")
    def devices():
        return db.devices()

    @app.get("/api/v1/devices/{device_id}/latest")
    def latest(device_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,32}$")):
        message = db.latest(device_id)
        if message is None:
            raise HTTPException(404, "No telemetry for this device")
        return message

    @app.get("/api/v1/devices/{device_id}/telemetry")
    def telemetry(device_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,32}$"),
                  start: str | None = Query(None, alias="from"), to: str | None = None,
                  field: str = "rms", limit: int = Query(5000, ge=1, le=20000)):
        if start is None or to is None:
            raise HTTPException(400, "from and to are required")
        try:
            a, b = parse_time(start), parse_time(to)
            if b < a:
                raise ValueError("to must be at least from")
            return db.history(device_id, a, b, field, limit)
        except (ValueError, OverflowError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/v1/devices/{device_id}/commands", status_code=202)
    def post_command(body: CommandIn, device_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,32}$")):
        device = db.device(device_id)
        if device is None:
            raise HTTPException(404, "Unknown device")
        if not ing.connected.is_set() or not ing.subscribed.is_set():
            raise HTTPException(503, "MQTT broker disconnected or unsubscribed")
        if device["connection"] != "online":
            raise HTTPException(409, "Device must have fresh live presence")
        if device["source"] != "synthetic":
            raise HTTPException(409, "Simulation mode control requires a synthetic source")
        if not device["clock_ready"] or not device["sampling_ok"]:
            raise HTTPException(409, "Device clock and sampling must be ready")
        now, cid = time.time(), "c" + uuid.uuid4().hex[:14]
        expires_at = math.ceil(now + config.TTL)
        try:
            db.create_command(cid, device_id, body.mode, now, expires_at)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        try:
            ing.send_command(device_id, cid, body.mode, expires_at)
        except (RuntimeError, OSError, ValueError) as exc:
            db.complete_command(cid, "publish_failed", time.time())
            ing.note(f"Command publication failed: {type(exc).__name__}")
        command = db.get_command(cid)
        return {"command_id": cid, "state": command["state"], "expires_at": expires_at}

    @app.get("/api/v1/commands")
    def commands():
        db.expire_commands(time.time())
        return db.commands()

    @app.get("/api/v1/commands/{cid}")
    def get_command(cid: str):
        db.expire_commands(time.time())
        command = db.get_command(cid)
        if command is None:
            raise HTTPException(404, "Unknown command")
        return command

    @app.get("/api/v1/stats")
    def stats():
        with ing.lock:
            counters = {"bad_messages": ing.n_bad, "telemetry_payload_bytes": ing.payload_bytes,
                        "telemetry_messages": ing.n_msg, "log": list(ing.log)}
        return {"rows": db.count(), "messages_per_second_10s": db.count(time.time() - 10) / 10,
                **counters,
                "broker_connected": ing.connected.is_set(), "broker_subscribed": ing.subscribed.is_set(),
                "uptime_s": time.monotonic() - started,
                "config": {"group": config.GROUP_ID, "prefix": config.PREFIX, "command_ttl_s": config.TTL}}

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=int(os.environ.get("API_PORT", "8000")))
