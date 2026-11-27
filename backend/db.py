"""SQLite storage for immutable windows, live status, and pending commands."""
import json
import sqlite3
import threading
import time
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry(
    id INTEGER PRIMARY KEY, device_id TEXT NOT NULL, boot_id TEXT NOT NULL, window_id INTEGER NOT NULL,
    received_at REAL NOT NULL, rms REAL NOT NULL, peak REAL NOT NULL, crest_factor REAL NOT NULL,
    payload TEXT NOT NULL, UNIQUE(device_id,boot_id,window_id));
CREATE INDEX IF NOT EXISTS ix_telemetry_device_time ON telemetry(device_id, received_at, id);
CREATE TABLE IF NOT EXISTS devices(
    id TEXT PRIMARY KEY, boot_id TEXT NOT NULL, connection TEXT NOT NULL,
    last_seen REAL, last_live_seen REAL, status_updated REAL, source TEXT, mode TEXT,
    sensor_ok INTEGER, clock_ready INTEGER, sampling_ok INTEGER, model_ready INTEGER);
CREATE TABLE IF NOT EXISTS commands(
    id TEXT PRIMARY KEY, device_id TEXT NOT NULL, action TEXT NOT NULL, mode TEXT NOT NULL,
    created REAL NOT NULL, expires_at REAL NOT NULL, state TEXT NOT NULL,
    updated REAL NOT NULL, result TEXT, last_sent REAL);
CREATE UNIQUE INDEX IF NOT EXISTS ix_one_pending_command ON commands(device_id) WHERE state='pending';
"""
FEATURES = {
    "rms": "rms", "peak": "peak", "crest_factor": "crest_factor",
    "p1x": "json_extract(payload, '$.spectrum.p1x')",
    "p2x": "json_extract(payload, '$.spectrum.p2x')",
}


class DB:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.session_started = time.time()
        self.con = sqlite3.connect(self.path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        columns = {row[1] for row in self.con.execute("PRAGMA table_info(telemetry)")}
        if columns and "boot_id" not in columns:
            self.con.close()
            raise ValueError("Pre-v1 database: archive the local database and start with a new DB_PATH")
        if self.path != ":memory:":
            self.con.execute("PRAGMA journal_mode=WAL")
        self.con.executescript(SCHEMA)
        self.con.commit()

    def close(self):
        with self.lock:
            self.con.close()

    def reset_presence(self):
        with self.lock:
            self.session_started = time.time()

    def insert_telemetry(self, device_id, message, received_at):
        with self.lock, self.con:
            inserted = self.con.execute("""
                INSERT OR IGNORE INTO telemetry(device_id,boot_id,window_id,received_at,rms,peak,crest_factor,payload)
                VALUES (?,?,?,?,?,?,?,?)
                """, (device_id, message["boot_id"], message["window_id"], received_at,
                      message["rms"], message["peak"], message["crest_factor"],
                      json.dumps(message, separators=(",", ":"), allow_nan=False))).rowcount
            if not inserted:
                return False
            device = self.con.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
            if device is None:
                self.con.execute("""
                    INSERT INTO devices(id,boot_id,connection,last_seen,last_live_seen,source,mode,sensor_ok,model_ready)
                    VALUES (?,?,'online',?,?,?,?,?,?)
                    """, (device_id, message["boot_id"], received_at, received_at,
                          message["source"], message["mode"], message["sensor_ok"], message["model_ready"]))
            elif device["boot_id"] == message["boot_id"]:
                self.con.execute("UPDATE devices SET connection='online',last_seen=?,last_live_seen=? WHERE id=?",
                                 (received_at, received_at, device_id))
                # Window mode/health are measurements; live status owns current device state.
                if device["status_updated"] is None:
                    self.con.execute("UPDATE devices SET source=?,mode=?,sensor_ok=?,model_ready=? WHERE id=?",
                                     (message["source"], message["mode"], message["sensor_ok"],
                                      message["model_ready"], device_id))
            return True

    def set_status(self, device_id, message, received_at, retained=False):
        with self.lock, self.con:
            device = self.con.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
            if message["connection"] == "offline":
                if device is None:
                    self.con.execute("INSERT INTO devices(id,boot_id,connection,status_updated) VALUES (?,?,'offline',?)",
                                     (device_id, message["boot_id"], received_at))
                elif device["boot_id"] == message["boot_id"]:
                    self.con.execute("UPDATE devices SET connection='offline',status_updated=? WHERE id=?",
                                     (received_at, device_id))
                return
            if retained and device is not None:
                return
            last_seen = device["last_seen"] if device and device["boot_id"] == message["boot_id"] else None
            self.con.execute("""
                INSERT INTO devices VALUES (?,?,'online',?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET boot_id=excluded.boot_id,connection='online',
                last_seen=excluded.last_seen,last_live_seen=excluded.last_live_seen,status_updated=excluded.status_updated,
                source=excluded.source,mode=excluded.mode,sensor_ok=excluded.sensor_ok,
                clock_ready=excluded.clock_ready,sampling_ok=excluded.sampling_ok,model_ready=excluded.model_ready
                """, (device_id, message["boot_id"], last_seen, None if retained else received_at, received_at,
                      message["source"], message["mode"], message["sensor_ok"], message["clock_ready"],
                      message["sampling_ok"], message["model_ready"]))

    def latest(self, device_id):
        with self.lock:
            row = self.con.execute("""
                SELECT t.received_at,t.payload FROM telemetry t JOIN devices d ON d.id=t.device_id AND d.boot_id=t.boot_id
                WHERE t.device_id=? ORDER BY t.window_id DESC LIMIT 1
                """, (device_id,)).fetchone()
        return {**json.loads(row["payload"]), "received_at": row["received_at"]} if row else None

    def device(self, device_id, now=None):
        now = time.time() if now is None else now
        with self.lock:
            row = self.con.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            if result["connection"] != "offline":
                seen = result["last_live_seen"]
                if seen is None or seen < self.session_started:
                    result["connection"] = "unknown"
                elif now - seen >= config.LIVE_TTL:
                    result["connection"] = "stale"
            for key in ("sensor_ok", "clock_ready", "sampling_ok", "model_ready"):
                result[key] = None if result[key] is None else bool(result[key])
            return result

    def devices(self):
        with self.lock:
            ids = [row[0] for row in self.con.execute("SELECT id FROM devices ORDER BY id")]
            return [{**self.device(device_id), "latest": self.latest(device_id)} for device_id in ids]

    def history(self, device_id, start, end, field="rms", limit=5000):
        if field not in FEATURES:
            raise ValueError("field must be rms, peak, crest_factor, p1x, or p2x")
        expression = FEATURES[field]
        with self.lock:
            rows = self.con.execute(
                f"""SELECT received_at AS t,{expression} AS v FROM telemetry
                WHERE device_id=? AND received_at BETWEEN ? AND ? AND {expression} IS NOT NULL
                ORDER BY received_at,id LIMIT ?""",
                (device_id, start, end, limit)).fetchall()
        return [dict(row) for row in rows]

    def count(self, since=0):
        with self.lock:
            return self.con.execute("SELECT COUNT(*) FROM telemetry WHERE received_at>=?", (since,)).fetchone()[0]

    def create_command(self, cid, device_id, mode, now, expires_at):
        with self.lock, self.con:
            self.expire_commands(now)
            try:
                self.con.execute("INSERT INTO commands VALUES (?,?,'set_mode',?,?,?,'pending',?,NULL,?)",
                                 (cid, device_id, mode, now, expires_at, now, now))
            except sqlite3.IntegrityError as exc:
                raise ValueError("A command is already pending for this device") from exc

    def get_command(self, cid):
        with self.lock:
            row = self.con.execute("SELECT * FROM commands WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None

    def complete_command(self, cid, result, now):
        with self.lock, self.con:
            command = self.get_command(cid)
            if command is None:
                return None
            if command["state"] != "pending":
                return command["state"]
            expired = now >= command["expires_at"] or result == "expired"
            state = "expired" if expired else ("done" if result == "done" else "failed")
            self.con.execute("UPDATE commands SET state=?,updated=?,result=? WHERE id=?",
                             (state, now, ("late:" + result) if now >= command["expires_at"] else result, cid))
            return state

    def expire_commands(self, now):
        with self.lock, self.con:
            return self.con.execute("UPDATE commands SET state='expired',updated=?,result='expired' WHERE state='pending' AND expires_at<=?",
                                    (now, now)).rowcount

    def claim_retries(self, now):
        with self.lock, self.con:
            rows = self.con.execute("SELECT * FROM commands WHERE state='pending' AND expires_at>? AND last_sent<=?",
                                    (now, now - config.RETRY_INTERVAL)).fetchall()
            self.con.executemany("UPDATE commands SET last_sent=? WHERE id=?", [(now, row["id"]) for row in rows])
            return [dict(row) for row in rows]

    def commands(self):
        with self.lock:
            return [dict(row) for row in self.con.execute("SELECT * FROM commands ORDER BY created DESC LIMIT 50")]
