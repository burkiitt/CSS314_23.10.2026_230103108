import argparse
import csv
import json
import math
import multiprocessing as mp
import os
import statistics
import time
from pathlib import Path

import numpy as np

from salt import get_student_params


def stencil_chunk(args):
    n, start, end, repeats = args
    rows = max(1, end - start)
    values = np.ones((rows + 2, n), dtype=np.float64)
    total = 0.0
    for _ in range(repeats):
        result = (values[1:-1, 1:-1] + values[:-2, 1:-1] + values[2:, 1:-1]
                  + values[1:-1, :-2] + values[1:-1, 2:]) / 5.0
        total += float(result.sum())
    return total


def run(n, workers, repeats):
    chunks = [(n, start, min(n - 1, start + math.ceil((n - 2) / workers)), repeats)
              for start in range(1, n - 1, math.ceil((n - 2) / workers))]
    context = mp.get_context("spawn")
    start = time.perf_counter_ns()
    with context.Pool(workers) as pool:
        checksum = sum(pool.map(stencil_chunk, chunks))
    return int(time.perf_counter_ns() - start), checksum


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()
    params = get_student_params(args.student_id)
    physical = os.cpu_count() or 1
    try:
        import psutil
        physical = psutil.cpu_count(logical=False) or physical
    except ImportError:
        pass
    workers = [p for p in (1, 2, 4, 8) if p <= physical]
    n = params["N"]
    strong = {}
    weak = {}
    for p in workers:
        strong[p] = run(n, p, args.repeats)
        weak_n = math.ceil(n * math.sqrt(p))
        weak[p] = (weak_n, *run(weak_n, p, args.repeats))
    t1 = strong[1][0]
    strong_checksum = strong[1][1]
    rows = []
    for p in workers:
        elapsed, checksum = strong[p]
        speedup = t1 / elapsed
        serial = ((1 / speedup) - (1 / p)) / (1 - (1 / p)) if p > 1 else ""
        rows.append(["strong", p, n, elapsed, speedup, speedup / p * 100, serial, "", checksum, strong_checksum])
    for p in workers:
        weak_n, elapsed, checksum = weak[p]
        scaled = p * n * n * t1 / (weak_n * weak_n * elapsed)
        rows.append(["weak", p, weak_n, elapsed, "", "", "", scaled, checksum,
                     (weak_n - 2) * (weak_n - 2) * args.repeats])

    output = Path(__file__).resolve().parent.parent / "results" / "scaling_metrics.tsv"
    header = ["study", "processes", "N", "time_ns", "speedup", "efficiency_percent",
              "serial_fraction", "scaled_speedup", "checksum", "expected_checksum"]
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    profile_path = output.parent / "host_profile.json"
    host = json.loads(profile_path.read_text(encoding="utf-8"))
    stride_path = output.parent / "stride_results.tsv"
    bandwidth = None
    if stride_path.exists():
        stride_rows = list(csv.DictReader(stride_path.open(encoding="utf-8"), delimiter="\t"))
        stride_one = next((x for x in stride_rows if x["stride"] == "1"), None)
        if stride_one:
            bandwidth = 8 / float(stride_one["ns_per_element"])
    intensity = 5 / 48
    frequency = host.get("base_frequency_hz") or 0
    cores = host.get("physical_cores") or 1
    peak_flops = frequency * cores * 16
    memory_roof = (bandwidth or 0) * 1_000_000_000 * intensity
    summary = {
        "student_id": args.student_id,
        "flops_per_stencil_point": 5,
        "bytes_per_stencil_point": 48,
        "arithmetic_intensity_flops_per_byte": intensity,
        "estimated_memory_bandwidth_gb_per_second": bandwidth,
        "estimated_peak_flops_per_second": peak_flops,
        "estimated_memory_roof_flops_per_second": memory_roof,
        "regime": "memory-bandwidth bound" if memory_roof < peak_flops else "compute bound",
        "cache": host["cache"],
    }
    (output.parent / "roofline_summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                           encoding="utf-8")
    print(output)


if __name__ == "__main__":
    mp.freeze_support()
    main()
