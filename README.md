# QCM Frequency Monitor

ESP32 firmware for counting a QCM clock signal, plus a Python desktop application
for plotting the measured frequency and its change over time.

## Project layout

- [`src/`](src/README.md): ESP32 firmware.
- [`python/`](python/README.md): Python serial monitor and plotter.

## Quick start

1. Connect the QCM clock output to GPIO 27 on the ESP32. Make sure the signal
   voltage is compatible with the ESP32 input.
2. Build and upload the firmware with PlatformIO:

   ```sh
   pio run
   pio run --target upload
   ```

3. Open a serial monitor at 115200 baud, or start the Python plotter described
   in [`python/README.md`](python/README.md).

The firmware samples pulses every 100 ms and reports the total over a rolling
one-second window (10 measurements per second).
