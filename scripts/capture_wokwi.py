"""Capture unchanged E2 firmware through official Wokwi CLI and a fresh backend."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
import uuid

import httpx
import paho.mqtt.client as mqtt

from backend import codec, config
from scripts.export_measurements import export_run, sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


class CaptureError(Exception):
    """An unmet runtime gate with a safe, fixed diagnostic message."""


def decode_message(kind, payload, retained):
    if kind in ("telemetry", "ack") and retained:
        raise ValueError("retained message")
    if kind == "status" and not payload:
        return None
    decoders = {"telemetry": codec.decode_telemetry, "status": codec.decode_status, "ack": codec.decode_ack}
    if kind in decoders:
        return decoders[kind](payload)
    value = json.loads(payload)
    codec.require_keys(value, ("schema_version", "id", "action", "mode", "exp"))
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1
            or not isinstance(value["id"], str) or not codec.COMMAND_ID.fullmatch(value["id"])
            or value["action"] != "set_mode" or value["mode"] not in config.MODES
            or type(value["exp"]) is not int or not 0 <= value["exp"] < 1 << 32 or retained):
        raise ValueError("invalid command")
    return value


class Observer:
    def __init__(self, directory, device_id):
        self.base = f"{config.PREFIX}/{device_id}"
        self.stream = (Path(directory) / "mqtt.jsonl").open("x")
        self.lock = threading.Lock()
        self.events = []
        self.ready = threading.Event()
        self.cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ce339-N06-capture-{uuid.uuid4().hex[:12]}")
        self.cli.on_connect = self.on_connect
        self.cli.on_subscribe = self.on_subscribe
        self.cli.on_disconnect = self.on_disconnect
        self.cli.on_message = lambda c, u, m: self.record(m.topic, m.payload, m.qos, m.retain, m.dup)

    def append(self, event):
        with self.lock:
            self.events.append(event)
            self.stream.write(json.dumps(event, allow_nan=False) + "\n")
            self.stream.flush()

    def snapshot(self):
        with self.lock:
            return list(self.events)

    def on_connect(self, client, userdata, flags, reason, properties):
        self.append(dict(event="connect", wall=time.time(), monotonic=time.monotonic(), failed=reason.is_failure))
        if not reason.is_failure:
            client.subscribe([(self.base + "/" + kind, 1) for kind in ("telemetry", "status", "ack", "cmd")])

    def on_subscribe(self, client, userdata, mid, reasons, properties):
        if reasons and all(not reason.is_failure for reason in reasons):
            self.ready.set()

    def on_disconnect(self, client, userdata, flags, reason, properties):
        self.ready.clear()
        self.append(dict(event="disconnect", wall=time.time(), monotonic=time.monotonic()))

    def record(self, topic, payload, qos=0, retained=False, dup=False, wall=None, monotonic=None):
        if topic not in [self.base + "/" + kind for kind in ("telemetry", "status", "ack", "cmd")]:
            return
        kind = topic.rsplit("/", 1)[1]
        event = dict(event="message", kind=kind, wall=time.time() if wall is None else wall,
                     monotonic=time.monotonic() if monotonic is None else monotonic,
                     payload_bytes=len(payload), qos=qos, retained=bool(retained), dup=bool(dup), valid=False)
        try:
            event["message"] = decode_message(kind, payload, retained)
            event["valid"] = True
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
            pass  # Preserve invalid-message byte counts without recording arbitrary payload text.
        self.append(event)

    def start(self):
        self.cli.reconnect_delay_set(1, 10)
        self.cli.connect_async(config.BROKER, config.PORT, 30)
        self.cli.loop_start()

    def close(self):
        self.cli.disconnect()
        self.cli.loop_stop()
        self.stream.close()


def terminate(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def executable(path):
    found = shutil.which(str(path))
    if not found:
        raise CaptureError("Required executable missing; provide its explicit path")
    return found


def safe_url(value):
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "wokwi.com" or not parsed.path.startswith("/projects/") or not parsed.path[10:].isdigit() or parsed.query or parsed.fragment:
        raise argparse.ArgumentTypeError("Use a public https://wokwi.com/projects/<id> URL without query parameters")
    return value


def capture(args):
    directory = ROOT / "artifacts" / "wokwi" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
    directory.mkdir(parents=True)
    manifest = dict(run_id=directory.name, device_id="esp32-01", source="Wokwi CLI synthetic",
                    units="g, provisional", model_ready=False, result="INCOMPLETE", started_at=time.time(),
                    code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    wokwi_url=args.wokwi_url, mode_seconds=args.mode_seconds, wall_timeout_s=args.wall_timeout,
                    checks={"build": "NOT RUN", "runtime": "NOT RUN", "mode_capture": "NOT RUN",
                            "commands": "NOT RUN", "dashboard": "NOT RUN", "public_source": "NOT RUN"},
                    clock_definitions={"command_latency": "backend updated minus created, milliseconds, successful only",
                                       "device_cadence": "completion uptime delta, milliseconds, same boot/mode",
                                       "receipt_cadence": "independent receiver wall clock delta, milliseconds",
                                       "traffic": "subscriber-received MQTT payload bytes; excludes wire overhead"},
                    attempts=[], findings=[])
    observer = backend = simulator = None
    handles = []
    deadline = time.monotonic() + args.wall_timeout
    boot_id = None

    def save():
        write_json(directory / "run.json", manifest)

    def windows(mode=None):
        unique = {}
        for event in observer.snapshot():
            value = event.get("message")
            if (event["event"] == "message" and event["kind"] == "telemetry" and event["valid"]
                    and not event["retained"] and value["boot_id"] == boot_id
                    and value["source"] == "synthetic" and not value["model_ready"]
                    and (mode is None or value["mode"] == mode)):
                unique.setdefault(value["window_id"], value)
        return sorted(unique.values(), key=lambda value: value["window_id"])

    def wait(predicate, stage_deadline, label):
        while time.monotonic() < min(deadline, stage_deadline):
            if simulator and simulator.poll() is not None:
                if "Connection timed out after 5 minutes" in (directory / "wokwi.log").read_text(errors="replace"):
                    raise CaptureError("Wokwi API five-minute connection limit reached; runtime acceptance incomplete")
                raise CaptureError("Wokwi stopped before runtime acceptance completed")
            if boot_id:
                for event in observer.snapshot():
                    value = event.get("message")
                    if (event["event"] == "message" and event["kind"] == "status" and event["valid"]
                            and not event["retained"] and value and value["connection"] == "online"
                            and event["wall"] >= manifest["runtime_started_at"] and value["boot_id"] != boot_id):
                        raise CaptureError("Unexpected device boot; possible reboot or shared-topic collision")
            value = predicate()
            if value:
                return value
            time.sleep(.2)
        raise CaptureError(label)

    save()
    try:
        if config.BROKER != "test.mosquitto.org" or config.PORT != 1883:
            raise CaptureError("Unchanged firmware requires test.mosquitto.org:1883; backend overrides refused")
        if (ROOT / "firmware" / "config.local.h").exists():
            raise CaptureError("Private firmware configuration present; public baseline build refused")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "firmware"], cwd=ROOT).returncode:
            raise CaptureError("Commit or discard firmware changes before measuring the public baseline")
        if subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "firmware"], cwd=ROOT):
            raise CaptureError("Untracked firmware files present; public baseline build refused")
        wokwi = executable(args.wokwi_cli)
        arduino = executable(args.arduino_cli)
        token = args.token_file.read_text().strip() if args.token_file else os.environ.get("WOKWI_CLI_TOKEN", "").strip()
        if not token:
            raise CaptureError("Wokwi token unavailable; use an ignored private file or WOKWI_CLI_TOKEN")
        manifest["versions"] = {"python": sys.version.split()[0],
                                "wokwi_cli": subprocess.check_output([wokwi, "--short-version"], text=True).strip(),
                                "arduino_cli": subprocess.check_output([arduino, "version"], text=True).strip()}
        firmware = [path for path in sorted((ROOT / "firmware").iterdir())
                    if path.suffix in (".ino", ".h", ".c", ".cpp") or path.name in ("diagram.json", "libraries.txt")]
        manifest["source_sha256"] = {path.name: sha256(path) for path in firmware}
        with (directory / "build.log").open("w") as log:
            build = subprocess.Popen([sys.executable, "scripts/check_firmware.py", "--cli", arduino], cwd=ROOT,
                                     stdout=log, stderr=subprocess.STDOUT)
            try:
                code = build.wait(timeout=max(.1, deadline - time.monotonic()))
            finally:
                terminate(build)
            if code:
                raise CaptureError("Unchanged ESP32 build failed; inspect private build log")
        manifest["checks"]["build"] = "PASS"
        simulation = directory / "simulation"
        simulation.mkdir()
        shutil.copyfile(ROOT / "firmware" / "diagram.json", simulation / "diagram.json")
        for name, source in (("firmware.bin", "sketch.ino.merged.bin"), ("firmware.elf", "sketch.ino.elf")):
            shutil.copyfile(ROOT / "artifacts" / "firmware" / source, simulation / name)
        (simulation / "wokwi.toml").write_text('[wokwi]\nversion = 1\nfirmware = "firmware.bin"\nelf = "firmware.elf"\n')
        manifest["build_sha256"] = {name: sha256(simulation / name) for name in ("firmware.bin", "firmware.elf", "diagram.json")}
        manifest["tool_sha256"] = {name: sha256(ROOT / "scripts" / name) for name in ("capture_wokwi.py", "export_measurements.py")}
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        backend_log = (directory / "backend.log").open("w")
        handles.append(backend_log)
        environment = os.environ.copy()
        environment.pop("WOKWI_CLI_TOKEN", None)
        environment.update(DB_PATH=str(directory / "backend.db"), API_PORT=str(port))
        backend = subprocess.Popen([sys.executable, "-m", "backend.api"], cwd=ROOT, env=environment,
                                   stdout=backend_log, stderr=subprocess.STDOUT)
        observer = Observer(directory, "esp32-01")
        observer.start()
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=2) as http:
            def backend_ready():
                try:
                    response = http.get("/api/v1/stats")
                    response.raise_for_status()
                    stats = response.json()
                    return stats["broker_connected"] and stats["broker_subscribed"] and observer.ready.is_set()
                except httpx.HTTPError:
                    return False
            wait(backend_ready, time.monotonic() + args.startup_timeout, "Backend or observer broker readiness timeout")
            cli_log = (directory / "wokwi.log").open("w")
            handles.append(cli_log)
            environment = os.environ.copy()
            environment["WOKWI_CLI_TOKEN"] = token
            manifest["runtime_started_at"] = time.time()
            simulator = subprocess.Popen([wokwi, str(simulation), "--timeout", "600000",
                                          "--serial-log-file", str(directory / "serial.log")],
                                         cwd=ROOT, env=environment, stdout=cli_log, stderr=subprocess.STDOUT)
            del token, environment
            print(f"Capture {directory.name}; dashboard http://127.0.0.1:{port}", flush=True)
            save()
            def ready_device():
                response = http.get("/api/v1/devices")
                response.raise_for_status()
                for device in response.json():
                    if (device["id"] == "esp32-01" and device["connection"] == "online"
                            and device["source"] == "synthetic" and device["clock_ready"] and device["sampling_ok"]):
                        fresh = any(e["event"] == "message" and e["kind"] == "status" and e["valid"]
                                    and not e["retained"] and e.get("message") and e["message"].get("connection") == "online"
                                    and e["message"]["boot_id"] == device["boot_id"]
                                    and e["wall"] >= manifest["runtime_started_at"] for e in observer.snapshot())
                        if fresh and not device["model_ready"]:
                            return device
                return None
            device = wait(ready_device, time.monotonic() + args.startup_timeout,
                          "Fresh synthetic device clock/sampling readiness timeout; Dat runtime follow-up")
            boot_id = manifest["boot_id"] = device["boot_id"]
            manifest["checks"]["runtime"] = "PASS"
            save()
            for index in range(10):
                mode = config.MODES[index % 3]
                wait(ready_device, time.monotonic() + args.startup_timeout, "Device control readiness lost")
                previous = windows()
                boundary = previous[-1]["window_id"] if previous else 0
                response = http.post("/api/v1/devices/esp32-01/commands", json={"action": "set_mode", "mode": mode})
                attempt = dict(index=index + 1, mode=mode, http_status=response.status_code, before_window_id=boundary)
                manifest["attempts"].append(attempt)
                save()
                if response.status_code != 202:
                    raise CaptureError("REST command precondition/publication request failed")
                resource = response.json()
                attempt["id"] = resource["command_id"]
                def terminal():
                    command = http.get("/api/v1/commands/" + resource["command_id"]).json()
                    return command if command["state"] != "pending" else None
                command = wait(terminal, time.monotonic() + max(1, resource["expires_at"] - time.time()) + 2,
                               "Command terminal-state timeout")
                if command["state"] != "done" or command["result"] != "done":
                    raise CaptureError("Command failed or expired; successful latency unavailable")
                wait(lambda: any(w["window_id"] > boundary for w in windows(mode)),
                     time.monotonic() + args.startup_timeout, "New-mode completed-window timeout")
                wait(lambda: (ready_device() or {}).get("mode") == mode,
                     time.monotonic() + args.startup_timeout, "Current status mode does not match applied command")
                if index < 3:
                    start = windows(mode)[-1]["uptime_ms"]
                    wait(lambda: (windows(mode)[-1]["uptime_ms"] - start) % (1 << 32) >= args.mode_seconds * 1000,
                         deadline, "Mode capture duration timeout")
                save()
            manifest["checks"].update(mode_capture="PASS", commands="PASS")
            if args.dashboard_seconds:
                print("REST exercise complete; dashboard observation window open", flush=True)
                dashboard_until = min(deadline, time.monotonic() + args.dashboard_seconds)
                while time.monotonic() < dashboard_until:
                    time.sleep(.2)
            manifest["result"] = "CAPTURED_PENDING_REVIEW"
    except CaptureError as error:
        manifest["result"] = "BLOCKED"
        manifest["findings"].append(str(error))
    except (Exception, KeyboardInterrupt) as error:
        manifest["result"] = "INCOMPLETE"
        manifest["findings"].append("Capture interrupted: " + type(error).__name__)
    finally:
        terminate(simulator)
        terminate(backend)
        if observer:
            observer.close()
        for handle in handles:
            handle.close()
        manifest["finished_at"] = time.time()
        for key, value in manifest["checks"].items():
            if value == "NOT RUN" and key in ("build", "runtime", "mode_capture", "commands"):
                manifest["checks"][key] = "BLOCKED"
        save()
        result = export_run(directory)
    print(f"{result['result']}: {directory.relative_to(ROOT)}; {result['stored_windows']} stored windows", flush=True)
    return 0 if result["result"] == "CAPTURED_PENDING_REVIEW" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wokwi-cli", default=os.environ.get("WOKWI_CLI", str(ROOT / ".tools" / "wokwi-cli")))
    parser.add_argument("--arduino-cli", default=str(ROOT / ".tools" / "arduino-cli"))
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--wokwi-url", type=safe_url)
    parser.add_argument("--mode-seconds", type=float, default=60)
    parser.add_argument("--startup-timeout", type=float, default=120)
    parser.add_argument("--wall-timeout", type=float, default=900)
    parser.add_argument("--dashboard-seconds", type=float, default=0)
    args = parser.parse_args()
    durations = (args.mode_seconds, args.startup_timeout, args.wall_timeout, args.dashboard_seconds)
    if not all(math.isfinite(value) for value in durations) or min(durations[:3]) <= 0 or args.dashboard_seconds < 0:
        parser.error("Durations must be positive; dashboard seconds may be zero")
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    raise SystemExit(capture(args))


if __name__ == "__main__":
    main()
