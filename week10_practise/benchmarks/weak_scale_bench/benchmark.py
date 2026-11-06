#!/usr/bin/env python3
"""Process-based weak-scaling benchmark (one fixed-size job per worker)."""
import argparse
import concurrent.futures
import csv
import os
import platform
import time


def work(seed_and_iterations):
    seed, iterations = seed_and_iterations
    # Deterministic integer workload. Keep the accumulator observable by returning it.
    value = seed
    for i in range(iterations):
        value = (value * 1664525 + 1013904223 + i) & 0xFFFFFFFF
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--workers", type=int, nargs="+", help="selected worker counts; default: every count 1..max")
    parser.add_argument("--iterations-per-worker", type=int, default=300_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", default="benchmarks/results.csv")
    args = parser.parse_args()
    if min(args.max_workers, args.iterations_per_worker, args.repeats) < 1:
        parser.error("worker count, iterations, and repeats must be positive")
    counts = args.workers or list(range(1, args.max_workers + 1))
    if any(n < 1 or n > args.max_workers for n in counts):
        parser.error("each worker count must be between 1 and --max-workers")
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    fields = ["workers", "run", "iterations_per_worker", "total_iterations", "wall_seconds", "checksum", "cpu_count", "platform"]
    with open(args.output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for workers in counts:
            for run in range(1, args.repeats + 1):
                jobs = [(i + 1, args.iterations_per_worker) for i in range(workers)]
                start = time.perf_counter()
                with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                    checksum = sum(pool.map(work, jobs))
                elapsed = time.perf_counter() - start
                writer.writerow({"workers": workers, "run": run, "iterations_per_worker": args.iterations_per_worker,
                                 "total_iterations": workers * args.iterations_per_worker, "wall_seconds": f"{elapsed:.9f}",
                                 "checksum": checksum, "cpu_count": os.cpu_count() or 1, "platform": platform.platform()})
                stream.flush()
                print(f"workers={workers:>2} run={run}/{args.repeats} wall={elapsed:.6f}s", flush=True)


if __name__ == "__main__":
    main()
