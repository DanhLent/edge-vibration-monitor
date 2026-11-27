# Trained Wokwi dashboard control

Captured November 27, 2026, in a fresh local browser with the backend
subscribed to the public MQTT broker and a trained Wokwi ESP32 online.
The captured Apply action changed the synthetic input to imbalance.
The backend persisted `done` for the correlated ACK in 0.993 s, and the
device published a newer window on the same boot with an imbalance
prediction. The chart shows the published RMS points.

- [Reviewed dashboard capture](dashboard.png)
- [Run and firmware hashes](summary.json)

The screenshot shows one calibrated synthetic case. See the [traffic
experiment](../../measurements/wokwi-th5-traffic/README.md) for longer captures.
