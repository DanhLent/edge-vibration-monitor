# Wokwi raw, periodic, and event traffic

Recorded November 27, 2026, with the same ESP32 circuit, 1 kHz synthetic X-axis
sample grid, and command schedule. The test uses comparable windows spanning at
least 82 simulated device seconds. Device IDs differ to isolate runs on the
public broker. Each run has its own binary hash. A successful warmup command
sets normal mode before the observed interval, followed by commands to switch
to imbalance and loose mounting.

| Publication | Device seconds | Received messages | Received payload bytes |
| --- | ---: | ---: | ---: |
| 16-bit raw batches | 82.855 | 346 | 171,019 |
| Periodic features | 82.649 | 103 | 30,810 |
| Prediction changes and heartbeat | 82.893 | 25 | 4,527 |

Normalizing by device duration gives **37.79× raw-to-event** and **97.35% less
payload**. The event subscriber received the imbalance transition, the loose
transition, and the same loose prediction exactly 60 device seconds later.
The raw subscriber received 324 distinct batches. Totals include status,
commands, and ACKs, and exclude broker retention replays and wire overhead.
The durations and counts describe Wokwi synthetic execution.

[Result CSV](traffic.csv) · [Raw](raw.json) · [Periodic](periodic.json) · [Event](event.json)

The separate [circuit run](circuit.json) used the virtual button. It recorded
61 consecutive healthy windows in each mode, spanning 60.093, 60.000, and
60.000 device seconds. Samples and every C prediction are in [the circuit
CSV](circuit-windows.csv). The virtual sample grid and real board acquisition
are separate measurements.

[Wokwi circuit with the loose-mount LED active](wokwi-loose.png).
