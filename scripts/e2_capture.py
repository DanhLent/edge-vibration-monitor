"""Exercise integrated E2 firmware on Wokwi and measure received MQTT payload bytes."""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import time

import httpx

from scripts.capture_wokwi import CaptureError, Observer, ROOT, terminate
from scripts.export_measurements import sha256, write_json

TOPICS = ("raw", "telemetry", "status", "cmd", "ack")
MODES = ("normal", "imbalance", "loose")
SERIAL = re.compile(r"^E2_WINDOW,(\d+),(\d+),(\w+),(-?\d+),(\d+\.\d+),(\d+\.\d+),([01])$", re.M)


def serial_windows(path):
    if not path.exists():
        return []
    return [(int(window), int(uptime), mode, int(prediction), float(rms), float(peak), bool(int(sensor)))
            for window, uptime, mode, prediction, rms, peak, sensor in
            SERIAL.findall(path.read_text(errors="replace"))]


def summarize(events, start, stop, boot):
    counts = Counter({kind: 0 for kind in TOPICS})
    sizes = counts.copy()
    raw_batches = set()
    telemetry = []
    for event in events:
        if not start <= event["monotonic"] < stop:
            continue
        if event["event"] == "disconnect":
            raise CaptureError("Observer disconnected during the traffic interval")
        if event["event"] != "message" or event["retained"]:
            continue
        message = event.get("message")
        kind = event["kind"]
        if not event["valid"] or (message and message.get("boot_id", boot) != boot):
            raise CaptureError("Invalid or foreign message during the measurement interval")
        counts[kind] += 1
        sizes[kind] += event["payload_bytes"]
        if kind == "raw":
            raw_batches.add((message["window_id"], message["batch"]))
        elif kind == "telemetry":
            telemetry.append({key: message[key] for key in ("window_id", "uptime_ms", "mode", "prediction")})
    return {"messages_by_topic": dict(counts), "payload_bytes_by_topic": dict(sizes),
            "messages": sum(counts.values()), "payload_bytes": sum(sizes.values()),
            "unique_raw_batches": len(raw_batches), "telemetry": telemetry}


def capture(args):
    result_dir = args.output.resolve()
    result_dir.mkdir(parents=True)
    binary = args.binary.resolve()
    serial = result_dir / "serial.log"
    done = result_dir / "done"
    backend = simulator = observer = None
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment.pop("WOKWI_CLI_TOKEN", None)
    environment.update(DB_PATH=str(result_dir / "backend.db"), API_PORT=str(port))
    report = {"engine": "Wokwi web" if args.web else "Wokwi CLI", "profile": args.profile,
              "publish_mode": args.publish, "binary_sha256": sha256(binary),
              "diagram_sha256": sha256(args.diagram), "commands": [], "result": "INCOMPLETE"}
    browser = ROOT / "scripts/wokwi_browser.cjs"
    boot = None
    observer = Observer(result_dir, args.device, raw=True)

    def until(predicate, timeout, label):
        stop = time.monotonic() + timeout
        while time.monotonic() < stop:
            if simulator and simulator.poll() is not None:
                raise CaptureError("Wokwi exited before " + label)
            if boot and any(event.get("kind") == "status" and not event["retained"] and event["valid"]
                            and event.get("message") and event["message"].get("connection") == "online"
                            and event["message"]["boot_id"] != boot and event["monotonic"] >= opened
                            for event in observer.snapshot()):
                raise CaptureError("Unexpected boot on the capture topics")
            value = predicate()
            if value:
                return value
            time.sleep(.15)
        raise CaptureError("Timed out waiting for " + label)

    with (result_dir / "backend.log").open("w") as backend_log, (result_dir / "wokwi.log").open("w") as sim_log:
        try:
            backend = subprocess.Popen([sys.executable, "-m", "backend.api"], cwd=ROOT, env=environment,
                                       stdout=backend_log, stderr=subprocess.STDOUT)
            observer.start()
            with httpx.Client(base_url=url, timeout=5) as http:
                def broker_ready():
                    if not observer.ready.is_set():
                        return False
                    try:
                        return http.get("/api/v1/stats").json()["broker_subscribed"]
                    except httpx.TransportError:
                        return False

                def device():
                    return next((row for row in http.get("/api/v1/devices").json() if row["id"] == args.device), {})

                def ready():
                    row = device()
                    if not (row.get("connection") == "online" and row.get("source") == "synthetic" and
                            all(row.get(key) for key in ("clock_ready", "sampling_ok", "model_ready"))):
                        return None
                    return row

                def latest_serial():
                    rows = serial_windows(serial)
                    return rows[-1] if rows else None

                def set_mode(mode):
                    before = latest_serial()
                    response = http.post(f"/api/v1/devices/{args.device}/commands", json={"action":"set_mode", "mode":mode})
                    response.raise_for_status()
                    resource = response.json()

                    def finished():
                        latest = http.get("/api/v1/commands/" + resource["command_id"]).json()
                        return latest if latest["state"] != "pending" else None

                    ack = until(finished, 25, f"{mode} ACK")
                    if ack["state"] != "done" or ack["result"] != "done":
                        raise CaptureError(f"{mode} command did not complete")
                    report["commands"].append({"id": resource["command_id"], "mode": mode,
                                               "latency_ms": 1000 * (ack["updated"] - ack["created"])})
                    return until(lambda: (row := latest_serial()) and row[2] == mode and (not before or row[0] > before[0]) and row, 35,
                                 f"{mode} serial window")

                if args.profile != "circuit":
                    until(broker_ready, 40, "backend and observer broker subscriptions")
                opened = time.monotonic()
                if args.web:
                    console = serial.open("w")
                    try:
                        simulator = subprocess.Popen(["node", str(browser), str(binary), str(args.diagram.resolve()),
                                                      str(done), str(result_dir / "wokwi.png")],
                                                     stdout=console, stderr=sim_log, env=environment)
                    finally:
                        console.close()
                else:
                    if stat.S_IMODE(args.token_file.stat().st_mode) != 0o600:
                        raise CaptureError("Wokwi token file must have mode 600")
                    sim = result_dir / "simulation"
                    sim.mkdir()
                    shutil.copyfile(binary, sim / "firmware.bin")
                    shutil.copyfile(args.diagram, sim / "diagram.json")
                    (sim / "wokwi.toml").write_text('[wokwi]\nversion = 1\nfirmware = "firmware.bin"\n')
                    cli_environment = {**environment, "WOKWI_CLI_TOKEN": args.token_file.read_text().strip()}
                    command = [str(args.wokwi_cli.resolve()), str(sim), "--timeout", "600000",
                               "--serial-log-file", str(serial)]
                    simulator = subprocess.Popen(command, env=cli_environment,
                                                 stdout=sim_log, stderr=subprocess.STDOUT)
                    del cli_environment
                print(f"Dashboard {url}", flush=True)
                if args.profile != "circuit":
                    info = until(ready, args.startup, "trained Wokwi device readiness")
                    boot = report["boot_id"] = info["boot_id"]
                until(latest_serial, 25, "Wokwi serial windows")

                def after(start, seconds, *, windows=0):
                    return until(lambda: (row := latest_serial()) and row[1] >= start[1] + seconds * 1000
                                         and row[0] >= start[0] + windows and row,
                                 max(45, seconds * 8), f"{seconds} device seconds")

                def press_button(previous):
                    next_mode = MODES[(MODES.index(previous[2]) + 1) % len(MODES)]
                    Path(str(done) + ".button").write_text(str(previous[0]))
                    return until(lambda: (row := latest_serial()) and row[2] == next_mode and row,
                                 35, "button mode change")

                if args.profile == "traffic":
                    anchor = set_mode("normal")
                    start = time.monotonic()
                    after(anchor, 5)
                    set_mode("imbalance")
                    after(anchor, 10)
                    set_mode("loose")
                    end = after(anchor, 82)
                    report["traffic"] = summarize(observer.snapshot(), start, time.monotonic(), boot)
                    report["device_seconds"] = (end[1]-anchor[1])/1000
                    if args.publish == "raw" and report["traffic"]["unique_raw_batches"] < 320:
                        raise CaptureError("Raw capture received fewer than 320 distinct batches")
                    if args.publish == "event":
                        sent = report["traffic"]["telemetry"]
                        if (not {"imbalance", "loose"}.issubset(row["prediction"] for row in sent) or
                                not any(a["prediction"] == b["prediction"] and b["uptime_ms"]-a["uptime_ms"] >= 60000
                                        for a,b in zip(sent, sent[1:]))):
                            raise CaptureError("Event capture is missing a prediction change or feature heartbeat")
                else:
                    report["mode_evidence"] = {}
                    for mode in MODES if args.profile in ("full", "circuit") else (args.profile,):
                        if args.profile == "circuit":
                            first = latest_serial()
                            if first[2] != mode:
                                first = press_button(first)
                            if first[2] != mode:
                                raise CaptureError("Wokwi button advanced to an unexpected mode")
                        else:
                            first = set_mode(mode)
                        last = after(first, args.mode_seconds, windows=args.mode_seconds)
                        rows = [row for row in serial_windows(serial) if first[0] <= row[0] <= last[0]]
                        if (len(rows) != last[0] - first[0] + 1 or
                                any(row[2] != mode or row[3] != MODES.index(mode) or not row[6] for row in rows)):
                            raise CaptureError(f"Missing, misclassified, or unhealthy {mode} windows")
                        report["mode_evidence"][mode] = {"seconds": (last[1]-first[1])/1000, "windows":len(rows),
                                                         "rms_g":first[4], "peak_g":first[5]}
                        print(f"{mode}: {len(rows)} verified Wokwi windows", flush=True)
                    if args.dashboard:
                        capture = subprocess.run(["node", str(browser), "-", "-", "-", str(result_dir/"dashboard.png"), url, args.device],
                                                 env=environment, text=True, stdout=subprocess.PIPE, stderr=sim_log,
                                                 timeout=70, check=True)
                        report["dashboard"] = json.loads(capture.stdout)
                        screenshot_ack = http.get("/api/v1/commands/" + report["dashboard"]["id"]).json()
                        screenshot_latest = device()["latest"]
                        decision = report["dashboard"]
                        if (screenshot_ack["state"] != "done" or screenshot_ack["result"] != "done" or
                                screenshot_latest["boot_id"] != decision["boot"] or
                                screenshot_latest["window_id"] < decision["window"] or
                                screenshot_latest["prediction"] != decision["mode"]):
                            raise CaptureError("Dashboard screenshot evidence failed post-capture correlation")
                if args.button:
                    if not args.web:
                        raise CaptureError("Browser simulator required for the interactive button check")
                    changed = press_button(latest_serial())
                    button_mode = changed[2]
                    after(changed, 3)
                    if latest_serial()[2] != button_mode:
                        raise CaptureError("Button press changed mode more than once")
                    report["button"] = button_mode
                report["result"] = "PASS"
        except (CaptureError, httpx.HTTPError, OSError, subprocess.SubprocessError) as error:
            report["finding"] = str(error)
        finally:
            done.touch()
            if args.web and simulator:
                try:
                    simulator.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    pass
            terminate(simulator)
            terminate(backend)
            observer.close()
            rows = serial_windows(serial)
            with (result_dir / "windows.csv").open("w", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                writer.writerow(("window_id", "device_uptime_ms", "mode", "prediction_id", "rms_g", "peak_g", "sensor_ok"))
                writer.writerows(rows)
            write_json(result_dir / "summary.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("binary", "diagram", "output"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--wokwi-cli", type=Path, default=ROOT / ".tools/wokwi-cli")
    parser.add_argument("--token-file", type=Path, default=Path.home()/".config/ce339/wokwi_token")
    parser.add_argument("--profile", choices=("full", "circuit", "traffic", *MODES), default="full")
    parser.add_argument("--publish", choices=("event", "periodic", "raw"), default="event")
    parser.add_argument("--mode-seconds", type=int, default=60)
    parser.add_argument("--startup", type=int, default=60)
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--button", action="store_true")
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--device", default="esp32-01")
    args = parser.parse_args()
    if (args.button or args.profile == "circuit") and not args.web:
        parser.error("Button/circuit checks use the Wokwi browser")
    if args.dashboard and args.profile in ("circuit", "traffic"):
        parser.error("Dashboard checks require a live feature profile")
    raise SystemExit(capture(args))


if __name__ == "__main__":
    main()
