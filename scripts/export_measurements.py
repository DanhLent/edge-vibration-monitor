"""Export one dedicated capture run without opening its SQLite database for writing."""
import argparse
from collections import Counter
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3

from backend.codec import decode_telemetry

SAMPLING_FIELDS = (
    "run_id", "device_id", "source", "mode", "boot_id", "window_id", "fs_hz",
    "sample_count", "window_duration_us", "actual_hz", "missed_samples", "sensor_ok",
    "rms", "peak", "crest_factor", "model_ready", "prediction", "ts", "uptime_ms",
    "backend_received_at", "observer_received_at", "payload_bytes", "window_id_delta",
    "device_cadence_ms", "backend_cadence_ms", "observer_cadence_ms",
)
COMMAND_FIELDS = (
    "run_id", "device_id", "id", "mode", "created", "expires_at", "updated", "state",
    "result", "successful_latency_ms", "observed_transmissions", "ack_boot_id",
    "ack_observer_received_at", "first_new_mode_window_id",
)
TRAFFIC_FIELDS = ("run_id", "kind", "retained", "valid", "messages", "payload_bytes", "mqtt_dup_messages")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def database_rows(path, table):
    if not path.exists():
        return []
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        order = "received_at,id" if table == "telemetry" else "created,id"
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}")]


def export_run(directory, output=None):
    directory = Path(directory)
    output = Path(output) if output else directory / "measurements"
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((directory / "run.json").read_text())
    run_id, device = manifest["run_id"], manifest["device_id"]
    events = []
    if (directory / "mqtt.jsonl").exists():
        events = [json.loads(line) for line in (directory / "mqtt.jsonl").read_text().splitlines()]
    messages = [event for event in events if event["event"] == "message"]
    observed = {}
    for event in messages:
        if event["kind"] == "telemetry" and event["valid"] and not event["retained"]:
            value = event["message"]
            observed.setdefault((value["boot_id"], value["window_id"]), event)
    sampling, previous = [], {}
    findings = set(manifest.get("findings", []))
    for stored in database_rows(directory / "backend.db", "telemetry"):
        if stored["device_id"] != device:
            findings.add("Unexpected device in dedicated backend database")
            continue
        value = decode_telemetry(stored["payload"].encode())
        # Public evidence is limited to the explicitly selected synthetic baseline.
        if value["source"] != "synthetic" or value["model_ready"]:
            findings.add("Unexpected source or model readiness; window excluded from public CSV")
            continue
        event = observed.get((value["boot_id"], value["window_id"]))
        row = {key: value.get(key) for key in SAMPLING_FIELDS if key in value}
        row.update(run_id=run_id, device_id=device, backend_received_at=stored["received_at"],
                   observer_received_at=event["wall"] if event else None,
                   payload_bytes=event["payload_bytes"] if event else None)
        key = value["boot_id"]
        old = previous.get(key)
        if old and value["window_id"] > old["window_id"] and value["mode"] == old["mode"]:
            row["window_id_delta"] = value["window_id"] - old["window_id"]
            row["device_cadence_ms"] = (value["uptime_ms"] - old["uptime_ms"]) % (1 << 32)
            row["backend_cadence_ms"] = (stored["received_at"] - old["backend_received_at"]) * 1000
            if event and old.get("observer_received_at") is not None:
                row["observer_cadence_ms"] = (event["wall"] - old["observer_received_at"]) * 1000
        if old is None or value["window_id"] > old["window_id"]:
            previous[key] = row
        sampling.append(row)
        if value["actual_hz"] < 200:
            findings.add("Dat: measured acquisition below 200 Hz")
        if not value["sensor_ok"]:
            findings.add("Dat: sensor health fault in synthetic window")
        if old and value["missed_samples"] > old["missed_samples"]:
            findings.add("Dat: missed timer notifications increased")
        if event is None:
            findings.add("Stored window missing from observer capture")
    commands = []
    for command in database_rows(directory / "backend.db", "commands"):
        if command["device_id"] != device:
            continue
        transmissions = [e for e in messages if e["kind"] == "cmd" and e["valid"]
                         and e["message"]["id"] == command["id"] and not e["retained"]]
        acks = [e for e in messages if e["kind"] == "ack" and e["valid"] and not e["retained"]
                and e["message"]["id"] == command["id"] and e["message"]["result"] == "done"
                and e["message"]["mode"] == command["mode"]
                and command["created"] <= e["wall"] < command["expires_at"]
                and e["message"]["boot_id"] == manifest.get("boot_id")]
        successful = command["state"] == "done" and command["result"] == "done"
        ack = acks[0] if acks and successful else None
        attempt = next((item for item in manifest.get("attempts", []) if item.get("id") == command["id"]), {})
        windows = [r for r in sampling if r["mode"] == command["mode"]
                   and ack and r["boot_id"] == ack["message"]["boot_id"]
                   and r["window_id"] > attempt.get("before_window_id", 0)
                   and r["backend_received_at"] >= command["updated"]]
        row = {key: command.get(key) for key in COMMAND_FIELDS if key in command}
        row.update(run_id=run_id, successful_latency_ms=(command["updated"] - command["created"]) * 1000
                   if successful else None, observed_transmissions=len(transmissions),
                   ack_boot_id=ack["message"]["boot_id"] if ack else None,
                   ack_observer_received_at=ack["wall"] if ack else None,
                   first_new_mode_window_id=windows[0]["window_id"] if windows else None)
        commands.append(row)
    counts, sizes, duplicates = Counter(), Counter(), Counter()
    for event in messages:
        key = event["kind"], event["retained"], event["valid"]
        counts[key] += 1
        sizes[key] += event["payload_bytes"]
        duplicates[key] += event["dup"]
    traffic = [dict(run_id=run_id, kind=k[0], retained=k[1], valid=k[2], messages=counts[k],
                    payload_bytes=sizes[k], mqtt_dup_messages=duplicates[k]) for k in sorted(counts)]
    write_csv(output / "sampling.csv", SAMPLING_FIELDS, sampling)
    write_csv(output / "commands.csv", COMMAND_FIELDS, commands)
    write_csv(output / "traffic.csv", TRAFFIC_FIELDS, traffic)
    manifest.update(findings=sorted(findings), stored_windows=len(sampling), commands=len(commands),
                    observed_messages=len(messages), observed_payload_bytes=sum(sizes.values()),
                    observer_connections=[{key: event[key] for key in ("event", "wall", "monotonic")}
                                          for event in events if event["event"] in ("connect", "disconnect")],
                    file_sha256={name: sha256(output / name) for name in ("sampling.csv", "commands.csv", "traffic.csv")})
    write_json(output / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = export_run(args.run_directory, args.output)
    print(f"Exported {result['stored_windows']} windows and {result['commands']} commands; {result['result']}")


if __name__ == "__main__":
    main()
