import math
import os
import platform
import threading
import time

import numpy as np
from numba import njit


ELEMENT_COUNT = 30_000_000


@njit(nogil=True)
def _kernel_copy(source: np.ndarray, destination: np.ndarray, start: int, end: int) -> None:
    for index in range(start, end):
        destination[index] = source[index]


@njit(nogil=True)
def _kernel_compute(source: np.ndarray, destination: np.ndarray, start: int, end: int) -> None:
    for index in range(start, end):
        value = source[index]
        destination[index] = math.sin(value) * math.cos(value) + math.tan(value)


def _benchmark(kernel, source: np.ndarray, destination: np.ndarray, worker_count: int) -> float:
    chunk_size = (ELEMENT_COUNT + worker_count - 1) // worker_count

    def worker(start: int, end: int) -> None:
        kernel(source, destination, start, end)

    threads = []
    for worker_id in range(worker_count):
        start = worker_id * chunk_size
        end = min(start + chunk_size, ELEMENT_COUNT)
        threads.append(threading.Thread(target=worker, args=(start, end)))

    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def _run_kernel(kernel, source: np.ndarray, destination: np.ndarray, worker_counts: list[int]):
    timings = []
    for worker_count in worker_counts:
        elapsed_ms = _benchmark(kernel, source, destination, worker_count)
        speedup = timings[0][1] / elapsed_ms if timings else 1.0
        timings.append((worker_count, elapsed_ms, speedup, speedup / worker_count))
    return timings


def _print_results(title: str, results: list[tuple[int, float, float, float]]) -> None:
    print(title)
    print("Cores  Wall Time (ms)  Speedup  Efficiency")
    print("-----  ---------------  -------  ----------")
    for worker_count, elapsed_ms, speedup, efficiency in results:
        print(f"{worker_count:5d}  {elapsed_ms:15.3f}  {speedup:7.3f}  {efficiency:10.3f}")


def main() -> None:
    max_cores = os.cpu_count() or 1
    worker_counts = [1, 2, max_cores]
    source = np.linspace(-1.0, 1.0, ELEMENT_COUNT, dtype=np.float64)
    destination = np.empty_like(source)

    # Compile both native kernels before collecting benchmark timings.
    _kernel_copy(source, destination, 0, 1)
    _kernel_compute(source, destination, 0, 1)

    copy_results = _run_kernel(_kernel_copy, source, destination, worker_counts)
    compute_results = _run_kernel(_kernel_compute, source, destination, worker_counts)

    copy_efficiency = copy_results[-1][3]
    compute_efficiency = compute_results[-1][3]
    if copy_efficiency < compute_efficiency:
        diagnosis = (
            "Kernel A (Vector copy) stalled in scaling due to memory-channel saturation; "
            "its all-core scaling efficiency was lower than Kernel B."
        )
    else:
        diagnosis = (
            "Kernel B (sin/cos/tan compute) stalled in scaling more than the copy kernel "
            "on this run; its all-core scaling efficiency was lower."
        )

    print(f"OS: {platform.platform()}")
    print(f"CPU model: {platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown')}")
    print(f"Elements per kernel: {ELEMENT_COUNT}")
    print(f"Worker counts: {worker_counts}")
    print()
    _print_results("Kernel A: Memory-Bound Vector Copy (B[i] = A[i])", copy_results)
    print()
    _print_results("Kernel B: Compute-Bound Trigonometric Operation", compute_results)
    print()
    print(f"All-core copy efficiency: {copy_efficiency:.3f}")
    print(f"All-core compute efficiency: {compute_efficiency:.3f}")
    print(f"Scaling diagnosis: {diagnosis}")


if __name__ == "__main__":
    main()
