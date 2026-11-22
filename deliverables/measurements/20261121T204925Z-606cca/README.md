# Short Wokwi CLI integration diagnostic

Run ID is UTC; local date is 2026-11-22 (Asia/Ho_Chi_Minh).
Unchanged ESP32 firmware was locally built and executed through official Wokwi CLI 0.29.1.
Source/tool snapshot: `da66910`; source/build/tool hashes are in [manifest](manifest.json).

This diagnostic uses `--mode-seconds 1 --wall-timeout 300` to fit the API connection limit.
It does **not** satisfy the required 60 device seconds per mode. The longer attempt and its
connection-limit finding remain documented [separately](../20261121T203825Z-0af0d6/README.md).

| Measurement | Observed result |
| --- | --- |
| Unique stored windows | 15, covering normal/imbalance/loose inputs |
| Serialized REST commands | 10/10 done ACKs plus matching new-mode windows |
| Successful backend ACK latency range | 871.833–1180.456 ms |
| Successful backend ACK latency median | 1056.005 ms |
| Observer-received messages / payload bytes | 48 / 9,176 B |
| Measured acquisition range | 701.9880–1000.4560 Hz |
| Capture wall duration, including build | 146.914 s |

[Sampling](sampling.csv), [commands](commands.csv), and [traffic](traffic.csv) preserve validated
synthetic measurements in provisional g. Latency uses persisted backend ACK receipt minus command
creation. Receiver cadence differs from device uptime; totals count received payloads, including
retries/retained replay, and exclude protocol overhead. Model readiness remains false and
predictions null; input modes are not diagnostic labels.

Result is CAPTURED_PENDING_REVIEW for this shortened schedule. Missed timer notifications
increased and remain a Dat follow-up. The public saved-source link and browser dashboard/control
checks were not run successfully; this CLI diagnostic makes no claim that a saved web project
matches or that dashboard clicks were verified. No physical, ML parity, FFT or reduction claim.

Only safe CSVs, provenance and this summary are published. Raw logs, database, build binaries,
profiles and token files remain ignored/private. Human PR review and full-duration evidence remain pending.
