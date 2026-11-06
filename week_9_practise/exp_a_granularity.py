"""Experiment A: compare very fine tasks with amortized chunks."""

import math
import multiprocessing as mp
import time


def collatz_steps(n: int) -> int:
    steps = 0
    while n > 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def run_granularity(workers: int, total_items: int = 1_000_000,
                    chunk_size: int = 1) -> tuple[float, int]:
    numbers = range(1, total_items + 1)
    start = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        results = pool.map(collatz_steps, numbers, chunksize=chunk_size)
    return time.perf_counter() - start, sum(results)


def main() -> None:
    workers = [1, 2, 4, 8]
    for chunk_size, label in ((1, "Micro (k=1)"), (10_000, "Coarse (k=10000)")):
        print(f"\n{label}")
        timings = {}
        checksum = None
        for p in workers:
            elapsed, checksum = run_granularity(p, chunk_size=chunk_size)
            timings[p] = elapsed
            print(f"P={p:2d} | Time={elapsed:8.3f}s | checksum={checksum}")
        baseline = timings[1]
        for p in workers[1:]:
            speedup = baseline / timings[p]
            karp_flatt = ((p * timings[p] / baseline) - 1) / (p - 1)
            print(f"P={p:2d} | Speedup={speedup:6.2f}x | Karp-Flatt e={karp_flatt:7.3f}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
