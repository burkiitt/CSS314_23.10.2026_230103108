#!/usr/bin/env python3
"""Summarize benchmark runs, fit Gustafson's serial fraction, and plot scaling."""
import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


def read_data(path):
    groups = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            groups[int(row["workers"])].append(float(row["wall_seconds"]))
    if not groups:
        raise ValueError("input CSV contains no benchmark rows")
    return {n: (statistics.mean(v), statistics.stdev(v) if len(v) > 1 else 0.0, len(v)) for n, v in groups.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="benchmarks/results.csv")
    p.add_argument("--plot", default="plots/scaling_comparison.pdf")
    p.add_argument("--summary", default="benchmarks/summary.csv")
    args = p.parse_args()
    data = read_data(args.input)
    # Weak-scaling efficiency: E(N)=T(1)/T(N) = alpha + (1-alpha)/N.
    # Fit 1-E(N)=alpha*(1-1/N) through the origin by least squares.
    base = data[min(data)][0]
    points = [(1 - 1 / n, 1 - (base / mean)) for n, (mean, _, _) in data.items() if n != min(data)]
    denom = sum(x * x for x, _ in points)
    alpha = min(1.0, max(0.0, sum(x * y for x, y in points) / denom)) if denom else 0.0
    summary = Path(args.summary)
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["workers", "mean_seconds", "stddev_seconds", "runs", "speedup", "standard_error_speedup"])
        for n, (mean, sd, runs) in sorted(data.items()):
            speedup = base / mean
            w.writerow([n, f"{mean:.9f}", f"{sd:.9f}", runs, f"{speedup:.6f}", f"{(sd/math.sqrt(runs))/mean*speedup:.6f}"])
    print(f"Observed serial fraction alpha = {alpha:.6f}")
    print(f"Wrote summary: {summary}")
    ns = sorted(data)
    xmax = max(ns)
    dense = [1 + i * (xmax - 1) / 300 for i in range(301)]
    measured = [base / data[n][0] for n in ns]
    errors = [(data[n][1] / math.sqrt(data[n][2])) / data[n][0] * measured[i] for i, n in enumerate(ns)]
    # Emit a self-contained vector PDF using only the Python standard library.
    # Plot coordinates and canvas size are in PDF points.
    W, H = 720, 460
    left, right, bottom, top = 75, 690, 65, 405
    ymax = max(1.0, xmax * 1.08, max(measured[i] + errors[i] for i in range(len(ns))) * 1.08)
    def xy(x, y): return left + (x-1)/(xmax-1 or 1)*(right-left), bottom + y/ymax*(top-bottom)
    commands = ["1 w 0.15 0.15 0.15 RG", f"{left} {bottom} m {right} {bottom} l {right} {top} l S"]
    for tick in range(0, int(ymax)+1, max(1, int(ymax)//6)):
        _, yy = xy(1, tick); commands += ["0.88 0.88 0.88 RG", f"{left} {yy:.2f} m {right} {yy:.2f} l S", "0.15 0.15 0.15 RG", f"BT /F1 9 Tf 42 {yy-3:.2f} Td ({tick}) Tj ET"]
    commands += ["BT /F1 10 Tf 300 28 Td (Worker processes) Tj ET", "BT /F1 10 Tf 12 240 Td (Speedup) Tj ET", "BT /F1 14 Tf 230 432 Td (Weak-scaling speedup) Tj ET"]
    colors = [(0.25,0.25,0.25),(0.05,0.35,0.75),(0.8,0.2,0.15)]
    curves = [(dense, dense, colors[0]), (dense, [alpha+(1-alpha)*n for n in dense], colors[1]), (dense, [1/(alpha+(1-alpha)/n) for n in dense], colors[2])]
    for xs, ys, (r,g,b) in curves:
        coords = [xy(x,y) for x,y in zip(xs,ys)]
        commands.append(f"{r} {g} {b} RG 1.8 w")
        commands.append(f"{coords[0][0]:.2f} {coords[0][1]:.2f} m " + " ".join(f"{x:.2f} {y:.2f} l" for x,y in coords[1:]) + " S")
    r,g,b = (0.1,0.55,0.25); commands.append(f"{r} {g} {b} RG 1 w")
    for i,n in enumerate(ns):
        x,y=xy(n,measured[i]); _,lo=xy(n,max(0,measured[i]-errors[i])); _,hi=xy(n,measured[i]+errors[i])
        commands += [f"{x:.2f} {lo:.2f} m {x:.2f} {hi:.2f} l S", f"{x-3:.2f} {lo:.2f} m {x+3:.2f} {lo:.2f} l S", f"{x-3:.2f} {hi:.2f} m {x+3:.2f} {hi:.2f} l S", f"{x-2.5:.2f} {y-2.5:.2f} 5 5 re f"]
    labels=["Ideal linear speedup",f"Gustafson fit (alpha={alpha:.3f})","Amdahl (same alpha)","Measured (+/- standard error)"]
    legend_colors=[colors[0],colors[1],colors[2],(0.1,0.55,0.25)]
    for i,(label,(r,g,b)) in enumerate(zip(labels,legend_colors)):
        yy=top-18-i*16; commands += [f"{r} {g} {b} RG 2 w {right-180} {yy+3} m {right-160} {yy+3} l S",f"0 0 0 rg BT /F1 9 Tf {right-154} {yy} Td ({label}) Tj ET"]
    content="\n".join(commands).encode("ascii")
    objs=[b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode(), b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length "+str(len(content)).encode()+b" >>\nstream\n"+content+b"\nendstream"]
    pdf=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
    for i,obj in enumerate(objs,1): offsets.append(len(pdf)); pdf += f"{i} 0 obj\n".encode()+obj+b"\nendobj\n"
    xref=len(pdf); pdf += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]: pdf += f"{off:010d} 00000 n \n".encode()
    pdf += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(args.plot).parent.mkdir(parents=True, exist_ok=True)
    Path(args.plot).write_bytes(pdf)
    print(f"Wrote plot: {args.plot}")


if __name__ == "__main__": main()
