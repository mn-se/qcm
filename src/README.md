# ESP32 Firmware

The PlatformIO firmware in [`qcm_plotter.cpp`](qcm_plotter.cpp) counts rising
edges from the QCM signal on GPIO 27 using the ESP32 pulse counter (PCNT).

## Build and upload

From the project root:

```sh
pio run
pio run --target upload
pio device monitor --baud 115200
```

The serial output is sent at 115200 baud. The firmware collects pulses in
100 ms intervals, maintains a 10-sample (one-second) rolling window, and prints
the pulse total, frequency in Hz, and difference from 10 MHz ten times per
second.

Check that the signal is connected to GPIO 27 and uses an ESP32-compatible
logic level. The PlatformIO board and framework settings are in
[`../platformio.ini`](../platformio.ini).
