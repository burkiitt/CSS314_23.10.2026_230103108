import os
import platform
import threading
import time

import numpy as np
import psutil
from numba import njit


INCREMENTS_PER_THREAD = 50_000_000


@njit(nogil=True)
def _increment_unpadded(shared_counts: np.ndarray, index: int, increments: int) -> None:
    for _ in range(increments):
        shared_counts[index] += 1


@njit(nogil=True)
def _increment_local(shared_counts: np.ndarray, index: int, increments: int) -> None:
    local_count = 0
    for _ in range(increments):
        local_count += 1
    shared_counts[index] = local_count


def _run_threads(worker, shared_counts: np.ndarray, worker_count: int) -> float:
    threads = [
        threading.Thread(
            target=worker,
            args=(shared_counts, index, INCREMENTS_PER_THREAD),
            name=f"worker-{index}",
        )
        for index in range(worker_count)
    ]

    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def main() -> None:
    physical_cores = psutil.cpu_count(logical=False) or max(1, (os.cpu_count() or 1) // 2)

    # Compile both native loops before timing the benchmarks.
    warmup = np.zeros(1, dtype=np.int64)
    _increment_unpadded(warmup, 0, 1)
    _increment_local(warmup, 0, 1)

    shared_counts = np.zeros(physical_cores, dtype=np.int64)
    unpadded_ms = _run_threads(_increment_unpadded, shared_counts, physical_cores)
    unpadded_total = int(shared_counts.sum())

    shared_counts.fill(0)
    local_ms = _run_threads(_increment_local, shared_counts, physical_cores)
    local_total = int(shared_counts.sum())

    ratio = unpadded_ms / local_ms if local_ms else float("inf")

    print(f"OS: {platform.platform()}")
    print(f"CPU model: {platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown')}")
    print(f"Physical worker threads: {physical_cores}")
    print(f"Increments per thread: {INCREMENTS_PER_THREAD}")
    print("Implementation: Numba native nogil loops in Python threads")
    print()
    print("Version              Wall Time (ms)    Total Increments")
    print("-------------------  ---------------  -----------------")
    print(f"Unpadded Shared      {unpadded_ms:15.3f}  {unpadded_total:17d}")
    print(f"Padded/Local         {local_ms:15.3f}  {local_total:17d}")
    print()
    print(f"Execution ratio (Unpadded / Padded-Local): {ratio:.3f}x")


if __name__ == "__main__":
    main()
