# Hardware, acquisition, and Wokwi

Lead: Dat. Shared feature definitions and JSON behavior live in [interfaces](interfaces.md).

| Component | Connection |
| --- | --- |
| MPU6050 | SDA 21, SCL 22, 3.3 V, GND, AD0 to GND; address 0x68 |
| Mode button | GPIO 18 to GND; INPUT_PULLUP, 30 ms debounce |
| Normal / imbalance / loose LEDs | GPIO 25 / 26 / 27 through individual 220 Ω resistors to anodes; cathodes to GND |

Use one ESP32 DevKit C v4 and the supplied diagram. OLED is deferred.
The IMU is configured for ±2 g, 1 kHz output, provisional 184 Hz accelerometer bandwidth, and
400 kHz I2C. Confirm bandwidth against Nyquist before lowering the acquisition rate. A failed
configuration remains a sensor fault until reboot; physical read failures discard partial windows.

`config.h` defaults to Wokwi-GUEST and synthetic input. The sensor is still read on sampling ticks
in synthetic mode so health remains visible. Synthetic features remain available during sensor
failure but must stay labeled synthetic. Physical mode never substitutes synthetic data.
Normal and imbalance use a 25 Hz sine with provisional amplitudes 0.10 g and 0.40 g. Loose input
uses a 0.20 g sine, a 0.10 g second harmonic, and 0.80 g / 3 ms impulses every 100 ms. These are
uncalibrated test waveforms; the mode button and dashboard choose inputs, not diagnostic labels.

An ESP timer wakes a dedicated FreeRTOS sampling task at nominal 1 kHz. Networking/button service
runs in the Arduino task. Backlog is counted, not reconstructed. Windows use actual elapsed time
and reset on mode changes. Only the latest completed snapshot is retained for publishing.
Initialization failures are surfaced through sensor/sampling health. The trained model is unavailable.

## Wokwi verification gate

Copy `firmware/` into an ESP32 Arduino Wokwi project with sketch.ino as the main sketch, the supplied
diagram.json and libraries.txt. Run at least 60 seconds in each input mode; record actual rates,
window durations/counts, missed timer notifications, sensor health, and MQTT behavior in CSV.
Exercise button bounce, dashboard commands, clock synchronization, and broker reconnects. Validate
captured device JSON with the backend codec and check current mode does not revert on an old window.
State whether readings are synthetic or physical. A compiled sketch and host tests are not runtime evidence.

## Physical-kit gate

Copy `config.local.h.example` to ignored `config.local.h`, set credentials and EVM_USE_SYNTHETIC=false,
and rebuild. Confirm official TH5 axis/units/preprocessing first. Verify IMU initialization, rate,
mounting/orientation, zero-motion/DC behavior, disconnection faults, and physical signal limits.
Capture hardware evidence and classify limitations before claiming physical diagnosis accuracy.
Keep raw uniformly sampled signals and timing evidence for FFT evaluation; frames with sampling
gaps require an explicit handling policy and cannot silently be treated as uniformly sampled data.
