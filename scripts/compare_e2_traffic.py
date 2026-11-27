"""Compare completed matched Wokwi traffic runs."""
import argparse
import csv
import json
from pathlib import Path

MODES = ("raw", "periodic", "event")


def compare(runs):
    if any(run["result"] != "PASS" or run["publish_mode"] != mode
           or run["profile"] != "traffic" for mode, run in zip(MODES, runs, strict=True)):
        raise ValueError("Expected three passing traffic runs: raw, periodic, event")
    durations = [run["device_seconds"] for run in runs]
    if max(durations) - min(durations) > 2 or min(durations) < 82:
        raise ValueError("Traffic intervals must match within two device seconds")
    if len({(run["engine"], run["diagram_sha256"]) for run in runs}) != 1:
        raise ValueError("Use the same Wokwi engine and circuit for all three runs")
    schedules = [tuple(command["mode"] for command in run["commands"]) for run in runs]
    if len(set(schedules)) != 1:
        raise ValueError("Traffic runs must use the same command schedule")
    raw_rate = runs[0]["traffic"]["payload_bytes"] / durations[0]
    table = []
    for run in runs:
        traffic, duration = run["traffic"], run["device_seconds"]
        rate = traffic["payload_bytes"] / duration
        table.append({
            "publication": run["publish_mode"], "device_seconds": duration,
            "payload_bytes": traffic["payload_bytes"], "messages": traffic["messages"],
            "payload_bytes_per_device_second": round(rate, 4),
            "raw_to_observed_ratio": round(raw_rate / rate, 4),
            "reduction_percent": round(100 * (1 - rate / raw_rate), 4),
        })
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for mode in MODES:
        parser.add_argument(mode, type=Path)
    args = parser.parse_args()
    runs = [json.loads(getattr(args, mode).read_text()) for mode in MODES]
    table = compare(runs)
    import sys
    writer = csv.DictWriter(sys.stdout, fieldnames=tuple(table[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(table)
    raise SystemExit(0 if table[-1]["raw_to_observed_ratio"] >= 10 else 2)


if __name__ == "__main__":
    main()
