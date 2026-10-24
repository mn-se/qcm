# Python Serial Plotter

The [`qcm_plotter/`](qcm_plotter/) application reads the ESP32's serial output
and displays the measured frequency and frequency shift in a live graph.

## Requirements

- Python 3.12 or later
- `matplotlib`
- `pyserial`

Install the runtime dependencies:

```sh
python -m pip install matplotlib pyserial
```

## Run

From this directory:

```sh
python qcm_plotter/main.py --port COM5
```

Replace `COM5` with the serial port used by the ESP32. The default baud rate is
115200. Close other applications using the port, including a serial monitor,
before starting the plotter.

Options:

```text
-p, --port PORT          Serial port (default: COM5)
-b, --baud BAUD          Baud rate (default: 115200)
-o, --output CSV_PATH    Save readings to a CSV file (default: do not save)
-z, --zero-points COUNT  Initial readings for baseline calibration (default: 10)
-w, --window-sec SECONDS Time range shown in the graph (default: 60)
```

For example, to plot a COM port and save readings:

```sh
python qcm_plotter/main.py --port COM5 --output measurements.csv
```

The CSV output file is created or overwritten when logging starts. See
[`qcm_plotter/README.md`](qcm_plotter/README.md) for details about the
application.
