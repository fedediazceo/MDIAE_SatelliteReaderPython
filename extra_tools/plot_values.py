#!/usr/bin/env python3
# Author: Federico Jose Diaz

import argparse
import csv
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def read_t_v(path, delimiter, data_percentage):
    rows = []
    with open(path, newline="") as f:
        r = csv.reader(f, delimiter=delimiter)
        for row in r:
            if not row or row[0].strip().startswith("#"):
                continue
            try:
                voltage = float(row[0].strip())
                t_str = row[1].strip()
                t = datetime.fromisoformat(t_str)
                rows.append((t, voltage))
            except (ValueError, IndexError):
                continue
    
    rows = rows[:min(len(rows), int(len(rows) * data_percentage / 100))]
    return rows


def plot_v(rows, out_png=None, show=False, data_percentage=100.0):
    if not rows:
        print("No valid rows to plot", file=sys.stderr)
        return 1

    ts = [t for t, _ in rows]
    voltage = [c for _, c in rows]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.scatter(
        ts,
        voltage,
        s=4,                 
        alpha=0.6,            
        edgecolors="none",
        rasterized=True,      
        label="voltage (V)",
    )

    locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Sensor Voltage over Time")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()

    base, ext = os.path.splitext(out_png)
    out_png = f"{base}_{int(data_percentage)}{ext}"

    if out_png:
        plt.savefig(out_png, dpi=120)
        print(f"Saved {out_png}")
    if show or not out_png:
        plt.show()
    return 0


def main():
    ap = argparse.ArgumentParser(description="plot sensor voltage from CSV")
    ap.add_argument("--csv", help="input CSV path")
    ap.add_argument("-o", "--out", help="output PNG path (if omitted, shows the plot)")
    ap.add_argument("--show", action="store_true", help="show an interactive window")
    ap.add_argument("--delimiter", help="select the delimiter used in the CSV file", default=",")
    ap.add_argument("--data-percentage", help="only plot a \% of values (for large files)", type=float, default=100.0)
    
    args = ap.parse_args()

    if args.data_percentage <= 0 or args.data_percentage > 100:
        ap.error("data-percentage must be in the range (0, 100]")

    rows = read_t_v(args.csv, delimiter=args.delimiter, data_percentage=args.data_percentage)
    sys.exit(plot_v(rows, args.out, args.show, data_percentage=args.data_percentage))


if __name__ == "__main__":
    main()