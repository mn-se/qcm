import argparse
import csv
import re
import sys
import time
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial

# ==================== 引数解析 ====================
parser = argparse.ArgumentParser(description="QCM Sensor Real-Time Monitor")
parser.add_argument(
    "-p", "--port", type=str, default="COM5", help="Serial COM port (default: COM5)"
)
parser.add_argument(
    "-b", "--baud", type=int, default=115200, help="Baud rate (default: 115200)"
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default=None,
    help="Output CSV file path. Default is no save.",
)
parser.add_argument(
    "-z",
    "--zero-points",
    type=int,
    default=10,
    help="Number of initial sampling points for zero-point calibration.",
)
parser.add_argument(
    "-w",
    "--window-sec",
    type=int,
    default=60,
    help="Display time window on graph in seconds (default: 60s).",
)
args = parser.parse_args()

COM_PORT = args.port
BAUD_RATE = args.baud
CSV_FILENAME = args.output
ZERO_POINTS = args.zero_points
DISPLAY_TIME_SEC = args.window_sec  # 画面に表示する時間幅（秒）

# 10Hz（1秒に10点）でも余裕を持って保持できるようバッファサイズを拡張 (例: 600秒分)
MAX_BUFFER_POINTS = DISPLAY_TIME_SEC * 10 * 10

# ==================== 変数・状態の初期化 ====================
time_data = deque(maxlen=MAX_BUFFER_POINTS)
freq_mhz_data = deque(maxlen=MAX_BUFFER_POINTS)
delta_f_data = deque(maxlen=MAX_BUFFER_POINTS)

raw_freq_history = []
baseline_freq = None
csv_file = None
csv_writer = None

if CSV_FILENAME:
    try:
        csv_file = open(CSV_FILENAME, mode="w", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            ["Elapsed_Time_s", "Raw_Freq_Hz", "Raw_Delta_f_Hz", "Zero_Adjusted_Delta_f_Hz"]
        )
        print(f"[INFO] Logging data to CSV: {CSV_FILENAME}")
    except Exception as e:
        print(f"[ERROR] Failed to open CSV file: {e}")
        sys.exit(1)

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"[INFO] Connected to {COM_PORT} at {BAUD_RATE} baud.")
except Exception as e:
    print(f"[ERROR] Could not open serial port {COM_PORT}: {e}")
    if csv_file:
        csv_file.close()
    sys.exit(1)

start_time = time.time()

# ==================== グラフ初期設定 ====================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.canvas.manager.set_window_title("QCM Sensor Real-Time Monitor")

(line_delta,) = ax1.plot([], [], "r-", lw=1.5, label="Zero-Adjusted Delta_f (Hz)")
ax1.set_ylabel("Delta_f [Hz]")
title_text = (
    f"QCM Frequency Shift (Zero Calibrating: {ZERO_POINTS} pts...)"
    if ZERO_POINTS > 0
    else "QCM Frequency Shift"
)
ax1.set_title(title_text)
ax1.grid(True)
ax1.legend(loc="upper right")

(line_freq,) = ax2.plot([], [], "b-", lw=1.5, label="Raw Frequency (MHz)")
ax2.set_xlabel("Time [s]")
ax2.set_ylabel("Frequency [MHz]")
ax2.set_title("Absolute Frequency")
ax2.grid(True)
ax2.legend(loc="upper right")

ax1.ticklabel_format(useOffset=False, style="plain")
ax2.ticklabel_format(useOffset=False, style="plain")


def parse_line(line):
    match = re.search(r"Freq:\s*([\d\.]+)\s*Hz\s*\|\s*Delta_f:\s*([+\-\d\.]+)\s*Hz", line)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def update(frame):
    global baseline_freq

    while ser.in_waiting > 0:
        try:
            raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
            freq, raw_delta_f = parse_line(raw_line)

            if freq is not None and 9000000 <= freq <= 11000000:
                current_time = time.time() - start_time

                # ゼロ点調整処理
                if ZERO_POINTS > 0 and baseline_freq is None:
                    raw_freq_history.append(freq)
                    count = len(raw_freq_history)
                    ax1.set_title(f"QCM Frequency Shift (Zero Calibration: {count}/{ZERO_POINTS})")

                    if count >= ZERO_POINTS:
                        baseline_freq = sum(raw_freq_history) / len(raw_freq_history)
                        ax1.set_title(f"QCM Frequency Shift (Zero-Point: {baseline_freq:.2f} Hz)")
                        print(f"[INFO] Zero-point calibrated at: {baseline_freq:.2f} Hz")

                        for i in range(len(delta_f_data)):
                            delta_f_data[i] = (freq_mhz_data[i] * 1000000.0) - baseline_freq

                adj_delta_f = (freq - baseline_freq) if baseline_freq is not None else raw_delta_f

                time_data.append(current_time)
                freq_mhz_data.append(freq / 1000000.0)
                delta_f_data.append(adj_delta_f)

                if csv_writer:
                    csv_writer.writerow(
                        [f"{current_time:.2f}", f"{freq:.2f}", f"{raw_delta_f:.2f}", f"{adj_delta_f:.2f}"]
                    )
                    csv_file.flush()

        except Exception as e:
            print(f"[ERROR] Read error: {e}")

    if time_data:
        line_delta.set_data(time_data, delta_f_data)
        line_freq.set_data(time_data, freq_mhz_data)

        # X軸範囲を設定（表示時間幅 DISPLAY_TIME_SEC に正確に追従）
        latest_time = time_data[-1]
        x_min = max(0.0, latest_time - DISPLAY_TIME_SEC)
        x_max = max(float(DISPLAY_TIME_SEC), latest_time)
        ax1.set_xlim(x_min, x_max)
        ax2.set_xlim(x_min, x_max)

        # Y軸範囲（現在画面内にあるデータのみから可動域を計算）
        # スライドアウトした過去のデータで軸範囲が狂わないようにフィルタリング
        visible_deltas = [
            d for t, d in zip(time_data, delta_f_data) if t >= x_min
        ]
        visible_freqs = [
            f for t, f in zip(time_data, freq_mhz_data) if t >= x_min
        ]

        if visible_deltas:
            d_min, d_max = min(visible_deltas), max(visible_deltas)
            d_margin = max(20.0, (d_max - d_min) * 0.2)
            ax1.set_ylim(d_min - d_margin, d_max + d_margin)

        if visible_freqs:
            f_min, f_max = min(visible_freqs), max(visible_freqs)
            f_margin = max(0.00005, (f_max - f_min) * 0.2)
            ax2.set_ylim(f_min - f_margin, f_max + f_margin)

    return line_delta, line_freq


ani = FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)

plt.tight_layout()
try:
    plt.show()
finally:
    ser.close()
    if csv_file:
        csv_file.close()
        print(f"[INFO] CSV file saved and closed: {CSV_FILENAME}")
    print("[INFO] Serial port closed.")