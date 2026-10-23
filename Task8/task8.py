import os
import platform
import threading
import time

import numpy as np
from numba import njit


MATRIX_SIZE = 1_024


@njit(nogil=True)
def _matmul_naive(
    matrix_a: np.ndarray,
    matrix_b: np.ndarray,
    result: np.ndarray,
    row_start: int,
    row_end: int,
) -> None:
    size = matrix_a.shape[0]
    for row in range(row_start, row_end):
        for inner in range(size):
            value = matrix_a[row, inner]
            for column in range(size):
                result[row, column] += value * matrix_b[inner, column]


@njit(nogil=True)
def _matmul_tiled(
    matrix_a: np.ndarray,
    matrix_b: np.ndarray,
    result: np.ndarray,
    row_start: int,
    row_end: int,
    tile_size: int,
) -> None:
    size = matrix_a.shape[0]
    for row_block in range(row_start, row_end, tile_size):
        for inner_block in range(0, size, tile_size):
            for column_block in range(0, size, tile_size):
                row_limit = min(row_block + tile_size, row_end)
                inner_limit = min(inner_block + tile_size, size)
                column_limit = min(column_block + tile_size, size)
                for row in range(row_block, row_limit):
                    for inner in range(inner_block, inner_limit):
                        value = matrix_a[row, inner]
                        for column in range(column_block, column_limit):
                            result[row, column] += value * matrix_b[inner, column]


def _benchmark(kernel, matrix_a, matrix_b, tile_size=None):
    worker_count = os.cpu_count() or 1
    result = np.zeros((MATRIX_SIZE, MATRIX_SIZE), dtype=np.float64)
    rows_per_worker = (MATRIX_SIZE + worker_count - 1) // worker_count

    def worker(row_start: int, row_end: int) -> None:
        if tile_size is None:
            kernel(matrix_a, matrix_b, result, row_start, row_end)
        else:
            kernel(matrix_a, matrix_b, result, row_start, row_end, tile_size)

    threads = []
    for worker_id in range(worker_count):
        row_start = worker_id * rows_per_worker
        row_end = min(row_start + rows_per_worker, MATRIX_SIZE)
        threads.append(threading.Thread(target=worker, args=(row_start, row_end)))

    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    return elapsed_ms, result


def main() -> None:
    matrix_a = np.full((MATRIX_SIZE, MATRIX_SIZE), 1.0, dtype=np.float64)
    matrix_b = np.full((MATRIX_SIZE, MATRIX_SIZE), 0.5, dtype=np.float64)
    worker_count = os.cpu_count() or 1

    # Compile all kernels before timing the full matrix multiplication.
    warmup_a = np.ones((2, 2), dtype=np.float64)
    warmup_b = np.ones((2, 2), dtype=np.float64)
    warmup_c = np.zeros((2, 2), dtype=np.float64)
    _matmul_naive(warmup_a, warmup_b, warmup_c, 0, 2)
    _matmul_tiled(warmup_a, warmup_b, warmup_c, 0, 2, 2)

    benchmarks = [
        ("Non-tiled", None, _matmul_naive),
        ("Tiled 16x16", 16, _matmul_tiled),
        ("Tiled 64x64", 64, _matmul_tiled),
    ]
    results = []
    reference = None
    for name, tile_size, kernel in benchmarks:
        elapsed_ms, result = _benchmark(kernel, matrix_a, matrix_b, tile_size)
        if reference is None:
            reference = result
        error = float(np.max(np.abs(result - reference)))
        results.append((name, tile_size, elapsed_ms, error))

    baseline_ms = results[0][2]
    print(f"OS: {platform.platform()}")
    print(f"CPU model: {platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown')}")
    print(f"Matrix: {MATRIX_SIZE} x {MATRIX_SIZE}")
    print(f"CPU worker threads: {worker_count}")
    print("Execution path: CPU fallback (CUDA runtime unavailable)")
    print()
    print("Geometry       Tile Size  Runtime (ms)  Speedup vs Non-tiled  Max Error")
    print("-------------  ---------  ------------  -------------------  ---------")
    for name, tile_size, elapsed_ms, error in results:
        tile_label = "-" if tile_size is None else str(tile_size)
        print(f"{name:13s}  {tile_label:9s}  {elapsed_ms:12.3f}  {baseline_ms / elapsed_ms:19.3f}  {error:9.3e}")


if __name__ == "__main__":
    main()
