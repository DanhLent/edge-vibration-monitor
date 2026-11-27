# Wokwi FFT extension evidence

The local advanced build computes a centered 1,000-point FFT and both TH5
X-axis spectral bands. The mandatory RMS/peak tree remains selectable. The
official raw comparison used 60 one-second windows in private ESP32 QEMU.
All 120 band powers matched NumPy. Maximum relative error was 0.000067%.
Independent Wokwi C inference parity was 6,018/6,018. The private ESP32
emulator agreed on all 7,794 held-out and threshold probes.

The [runtime observation](runtime-observation.json) uses 48 complete Serial
rows across the three calibrated synthetic modes. All recorded predictions
matched the intended class. This capture ran the raw publication build.
Its first transform included initialization. It provides transform timing in
simulated device microseconds. The [profiling CSV](fft-runtime-observation.csv)
includes only synthetic data. The FFT-capable event build used 20,040 more
bytes of static RAM and 6,212 more bytes of flash than the time-domain build.
The transform arrays use 16,000 bytes and two sample buffers use 4,000 bytes.

## Locked split results

| Split | Always normal | Mandatory tree | FFT tree |
| --- | ---: | ---: | ---: |
| Temporal | 0.2820 | 0.3557 | 0.7591 |
| Random by burst | 0.2921 | 0.5331 | 0.7986 |

The values are macro F1. Temporal loose-mount recall was 1,080/1,080.
The FFT tree still classified 1,439 temporal normal windows as imbalance.
The official dataset is simulated. Physical-kit timing and generalization
remain to be measured.

The separate [1 kHz notification benchmark](timed-notifications.csv)
reported zero missed notifications over each 12-second phase. The timed
acquisition task was active during both phases. The FFT phase performed
12 transforms of 47.195 ms each, including the final transform beyond
the nominal 12-second boundary. This isolates timer scheduling from I²C.
The integrated virtual-frame capture measured a 53.117 ms warm median.

## Live Wokwi integration

The [dashboard run](../../dashboard/wokwi-fft/README.md) correlated Apply,
MQTT ACK, spectral history, and a newer same-boot FFT prediction. The
[event run](event.json) captured two predicted class changes and a 60-second
feature heartbeat over 82.437 device seconds, with 4,783 received payload
bytes including status, commands, and ACKs.

The raw run reached the end of the same three-command schedule but lost
some Serial fields in browser collection. The [conservative comparison](raw-traffic-lower-bound.json)
counts only 140 distinct observed raw batches after warmup. At least
72,380 raw payload bytes were captured in at most 94 device seconds.
Even with that longer envelope and all raw-side control traffic omitted,
the observed raw payload rate was at least **13.27×** the event rate.
A fresh, fully automated paired raw run remains open.
