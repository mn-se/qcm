# QCM Plotter

This desktop application reads frequency measurements from the ESP32 over a
serial connection and plots the absolute frequency and frequency shift in
real time. It can optionally write readings to a CSV file.

## Requirements

- Python 3.12 or later
- `matplotlib`
- `pyserial`

Install the dependencies with:

```sh
python -m pip install matplotlib pyserial
```

## Usage

From this directory:

```sh
python main.py --port COM5
```

Set `--port` to the serial port for the ESP32. The default port is `COM5` and
the default baud rate is 115200. Close any other program connected to the same
serial port before starting.

Optional arguments:

- `-p`, `--port`: serial port (default: `COM5`)
- `-b`, `--baud`: baud rate (default: `115200`)
- `-o`, `--output`: CSV output path; if omitted, no CSV is written
- `-z`, `--zero-points`: number of initial readings used for baseline
  calibration (default: `10`; set to `0` to disable calibration)
- `-w`, `--window-sec`: graph time range in seconds (default: `60`)

Example:

```sh
python main.py --port COM5 --output measurements.csv --window-sec 120
```

The CSV file is created or overwritten when the program starts. Its columns
are elapsed time, raw frequency, raw frequency shift, and baseline-adjusted
frequency shift.