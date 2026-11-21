# Partial Wokwi CLI integration capture

Run ID is UTC; local date is 2026-11-22 (Asia/Ho_Chi_Minh).
Source: unchanged ESP32 firmware built locally and executed through Wokwi CLI 0.29.1.
Code snapshot: `c632512`; complete source/build/tool hashes are in [manifest](manifest.json).
This is provisional synthetic normal-mode input in g. Model readiness is false and predictions
are null throughout. No physical-kit, trained-model, FFT or traffic-reduction claim is made.

| Measurement | Observed result |
| --- | --- |
| Unique stored windows | 37, all normal input |
| Span between first/last device completions | 36.017 s |
| Measured acquisition range | 696.9847–1000.479 Hz |
| Cumulative missed timer notifications at final window | 331 |
| Successful commands | 1 of the requested ten-command exercise |
| Successful backend ACK latency | 1931.258 ms |
| Observer-received messages / payload bytes | 46 / 13,753 B, including status/command/ACK traffic |
| Wall runtime after CLI launch | 308.541 s |

[Sampling](sampling.csv), [commands](commands.csv), and [traffic](traffic.csv) preserve the
measurement conventions in the [reporting spec](../../../docs/reporting.md). Receiver cadence and
device uptime differ; payload totals exclude MQTT/TCP/Wi-Fi overhead. Successful command latency
uses the backend's persisted updated-minus-created timestamps, not observer ACK receipt time.

The CLI reported its five-minute API connection limit and disconnected before 60 device seconds
or the remaining modes/commands could be captured. Result is BLOCKED, not complete acceptance.
Dat follow-up: investigate simulation throughput and missed notifications, then choose any
firmware tuning within the required sampling range and bandwidth constraints on Dat's own track.

The in-app web editor accepted support files, but starter-file replacement stalled on its
confirmation dialog. No E2 saved-source URL was verified. Dashboard navigation occurred after
the capture backend stopped and returned connection refused; visual/control evidence is pending.
CLI execution does not establish that a saved web project ran these same sources.

Only schema-validated synthetic CSVs, safe provenance and this summary are published. Raw Serial,
observer traces, SQLite, build files, browser drafts and the private token remain outside tracked
evidence. Human PR review and all remaining course gates are still required.
