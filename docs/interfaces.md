# E2 interface contract

Leads: Danh (backend/MQTT), Dat (firmware), Nhat (model). Review every affected lead before changing
wire fields, feature definitions, labels, or C inference. Shared examples: `tests/fixtures/interfaces.json`.
This is the first supported wire format; pre-v1 local SQLite databases must be archived before reuse.

## Topics and transport

Base: `ce339/N06/e2/esp32-01`. Backend subscriptions use `+` only for the device segment.

| Suffix | Publisher → subscriber | QoS | Retained |
| --- | --- | --- | --- |
| `/telemetry` | ESP32 → backend | 0 | No |
| `/status` | ESP32 → backend | 0; Last Will 1 | Yes |
| `/cmd` | Backend → ESP32 | 1 | No |
| `/ack` | ESP32 → backend | 0 | No |

Wokwi Public Gateway requires an Internet-reachable broker. Default: `test.mosquitto.org:1883`.
PubSubClient publishes at QoS 0; a successful publish indicates a local send, not device-side
acknowledgment or durable delivery. Application retries recover lost acknowledgments.
Telemetry and ACKs received with the retained flag are rejected. An empty status payload clears
broker retention and is ignored by ingestion.

## Telemetry

Version 1 uses the fields below. Version 2 adds the FFT fields documented after this table.
Both versions reject unknown fields. Status, commands and ACKs retain version 1. `boot_id` is eight lowercase hexadecimal digits,
generated at boot; `window_id` increases within that boot.

| Fields | Definition |
| --- | --- |
| `schema_version`, `boot_id`, `window_id` | Version 1 and measurement identity |
| `ts` | Unix seconds captured at completion; null if the device clock is unsynchronized |
| `uptime_ms` | Completion uptime in milliseconds, wrapping as uint32 after about 49.7 days |
| `window_duration_us` | Actual elapsed window duration, at least 1,000,000 µs |
| `rms`, `peak`, `crest_factor` | Nonnegative finite RMS, absolute peak, and peak/RMS; all zero for a zero signal |
| `fs_hz`, `sample_count`, `actual_hz` | Nominal rate, positive acquired count, count × 1,000,000 / duration |
| `missed_samples` | Cumulative dropped timer notifications since boot; not a count of I2C failures |
| `source`, `mode` | `synthetic` with normal/imbalance/loose; `mpu6050` with null mode |
| `sensor_ok` | All MPU6050 reads included in this window succeeded; failed physical windows are discarded |
| `model_ready`, `prediction` | False/null until validated inference; true requires a known class |

FFT-capable firmware sends telemetry schema version 2. The required `spectrum`
field contains `p1x` and `p2x` in g², plus integer `fft_us` for the transform
duration, or null when there is no reliable spectrum. Non-null bands require
1,000 samples at 1 kHz and a duration between 1,000,000 and 1,002,000 µs.
Band powers are the one-sided sums (2|X[k]|²/N²) of the centered X-axis FFT
over inclusive bins 20–30 and 45–55. `model_variant` is `fft` for an FFT tree
prediction, `baseline` for an RMS/peak prediction, and null when unavailable.
A baseline prediction may still accompany a valid measured spectrum.

Features use RMS = sqrt(sum(x²)/N), peak = max(abs(x)), crest = peak/RMS or zero at RMS zero.
Current acceleration units are **g, provisional**, from raw X-axis int16/16384. No gravity/DC removal
is applied. Synthetic waveforms are test inputs and require TH5 calibration before model validation.
Crest and measured-rate consistency use relative tolerance 1e-4 and absolute tolerance 1e-6;
peak/RMS ordering permits 1e-6 rounding tolerance.

Windows close before adding the boundary sample. Mode changes discard a partial old-mode window.
Timer backlog produces one actual read and increments missed notifications; missing samples are
never reconstructed. Timing stalls lengthen the measured window and remain visible in its rate.

The firmware retains only the latest completed window, so disconnected operation can skip intermediate
windows. Reconnects may resend the latest snapshot with its original metadata. SQLite stores each
(device, boot, window) once; received payload-byte/message counters still include duplicates.
History charts use backend receipt time. Latest data is selected by window ID for the current boot.
A new boot's live status switches current identity; old-boot telemetry remains historical.

## Status and presence

Online status requires `schema_version`, `boot_id`, `connection="online"`, `source`, `mode`,
`sensor_ok`, `clock_ready`, `sampling_ok`, and `model_ready`. Health describes current state;
it is separate from a completed measurement. Failed IMU configuration stays a fault until reboot.
`sampling_ok` indicates successful task/timer initialization.

Last Will contains only version, boot ID, and `connection="offline"`. An old boot's Will cannot
mark the current boot offline. Online status is sent on connect, mode/health/clock changes, and
at 15-second intervals. Live presence becomes stale after 45 seconds without a fresh status or
unique telemetry window. Cached retained online status never establishes freshness. Backend
startup/reconnect invalidates previous live observations until a fresh message arrives.

API connection states: `online`, `offline`, `unknown` (cached/no observation this connection),
`stale` (live observation aged out). Telemetry does not overwrite status-owned current mode or health.

## Commands and acknowledgments

```json
{"schema_version":1,"id":"cfixture","action":"set_mode","mode":"loose","exp":1795300000}
```

IDs contain 1–15 ASCII letters, digits, underscores, or hyphens. Expiry is uint32 Unix seconds.
Only synthetic sources accept `set_mode`; first execution requires a synchronized clock and
`now < exp`. The API allows one pending command per device and defaults to a 15-second TTL.

Persist before publish. Retry every second with the same ID, mode, action, and expiry while pending
and before expiry. Restarted backends recover unexpired pending commands from SQLite. Initial
publication failure persists a failed command; transient retry failures remain pending until expiry.

ACK fields: `schema_version`, `boot_id`, `id`, `result`, `mode`. Results are `done`, `bad`,
`expired`, `clock`, or `unsupported`. Only `done` includes the applied mode; other results use null.
Match the target device/current boot/ID, and require the applied mode to match the command.
Retained, late, wrong-device, and terminal-command ACKs cannot turn a command into success.
Backend deadline comparison is `received_at >= exp`.

Firmware remembers the last eight results in RAM. Duplicates replay the original result without
execution, including after expiry; backend deadlines still apply. Reboots clear this cache, but
absolute `set_mode` assignment remains idempotent. This does not claim exactly-once execution.
ACK and status buffers are independent; the supported API serializes commands per device.

`done` confirms assignment of the requested input mode. Acquisition resets on its next tick, and
measurements for the new mode arrive after a complete window. It does not confirm a diagnosis.

## REST

- `GET /api/v1/devices`: current state, readiness, live/measurement times, current boot's latest window.
- `GET /api/v1/devices/{id}/latest`: latest current-boot window or 404.
- `GET /api/v1/devices/{id}/telemetry?from=&to=&field=`: receipt-time series; Unix seconds or timezone-aware ISO timestamps; fields `rms`, `peak`, `crest_factor`, `p1x`, and `p2x`. Spectral history omits windows without a spectrum.
- `POST /api/v1/devices/{id}/commands`: `{ "action":"set_mode", "mode":"loose" }`; 202 with command ID/state/expiry after persistence. Initial publish failure remains a 202 failed resource.
- `GET /api/v1/commands/{id}` and `/api/v1/commands`: persisted lifecycle; reads expire overdue commands.
- `GET /api/v1/stats`: stored windows, received telemetry messages/payload bytes, rejected messages, broker state, and logs.

Command preconditions: known device (otherwise 404), connected/subscribed backend (503), fresh
online synthetic source with ready clock and sampling (409), valid input (422), no pending command (409).
Latency for successful commands is backend ACK receipt minus command creation; expiry/failure duration
is not a successful control latency. Stats are session counters, not a completed traffic experiment.

## C inference

`firmware/model.h` has C++ linkage guards and declares:

```c
bool model_is_ready(void);
int8_t model_predict(float rms, float peak);
```

Inputs are float32 RMS and absolute peak, in that order; crest factor is excluded. Class IDs:
-1 unavailable, 0 normal/green, 1 imbalance/yellow, 2 loose/red. Model readiness comes from one
implementation. The initial stub always returns false/-1; all diagnosis LEDs remain off.
Read [ML gates](ml.md) before replacing it. A model is enabled only after official-data alignment,
faithful threshold export, and recorded actual ESP32/Python parity.
