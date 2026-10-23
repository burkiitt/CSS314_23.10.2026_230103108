import os
import platform
import threading
import time

import numpy as np
from numba import njit


SIZES = [100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]
A = 1.25
B = -0.75


@njit(nogil=True)
def _vector_operation(x: np.ndarray, y: np.ndarray, start: int, end: int) -> None:
    for index in range(start, end):
        y[index] = A * x[index] + B


def _serial_time(x: np.ndarray, y: np.ndarray, size: int) -> float:
    start_ns = time.perf_counter_ns()
    _vector_operation(x, y, 0, size)
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def _parallel_time(x: np.ndarray, y: np.ndarray, size: int, worker_count: int) -> float:
    block_size = (size + worker_count - 1) // worker_count

    def worker(start: int, end: int) -> None:
        _vector_operation(x, y, start, end)

    threads = []
    for worker_id in range(worker_count):
        start = worker_id * block_size
        end = min(start + block_size, size)
        threads.append(threading.Thread(target=worker, args=(start, end)))

    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def _crossover_ranges(results: list[tuple[int, float, float]]) -> list[str]:
    ranges = []
    for previous, current in zip(results, results[1:]):
        previous_size, previous_serial, previous_parallel = previous
        current_size, current_serial, current_parallel = current
        was_slower = previous_parallel >= previous_serial
        is_faster = current_parallel < current_serial
        if was_slower and is_faster:
            ranges.append(f"{previous_size} < N <= {current_size}")
    return ranges


def main() -> None:
    worker_count = os.cpu_count() or 1
    max_size = max(SIZES)
    x = np.arange(max_size, dtype=np.float64) / max_size
    y = np.empty_like(x)

    # Compile the native kernel before collecting benchmark timings.
    _vector_operation(x, y, 0, 1)

    results = []
    for size in SIZES:
        serial_ms = _serial_time(x, y, size)
        parallel_ms = _parallel_time(x, y, size, worker_count)
        results.append((size, serial_ms, parallel_ms))

    print(f"OS: {platform.platform()}")
    print(f"CPU model: {platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown')}")
    print(f"Logical worker threads: {worker_count}")
    print(f"Operation: y[i] = {A} * x[i] + ({B})")
    print()
    print("N          Serial (ms)    Parallel (ms)    Parallel/Serial")
    print("---------  -------------  ---------------  ----------------")
    for size, serial_ms, parallel_ms in results:
        print(f"{size:9d}  {serial_ms:13.3f}  {parallel_ms:15.3f}  {parallel_ms / serial_ms:16.3f}")

    ranges = _crossover_ranges(results)
    print()
    if ranges:
        print("Crossover range where parallel changes from slower to faster:")
        for crossover in ranges:
            print(f"  {crossover}")
    else:
        print("Crossover range where parallel changes from slower to faster:")
        print("  No crossover observed in the tested N values")


if __name__ == "__main__":
    main()
