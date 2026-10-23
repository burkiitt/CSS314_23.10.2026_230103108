import atexit
import math
import multiprocessing as mp
import os
import platform
import random
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import shared_memory


STUDENT_ID = 230103108
ELEMENT_COUNT = 20_000_000
PARALLEL_FRACTION = 0.95

_worker_shared_memory = None
_worker_values = None


def _open_shared_memory(name: str | None, *, create: bool, size: int = 0):
    try:
        if create:
            return shared_memory.SharedMemory(name=name, create=True, size=size, track=False)
        return shared_memory.SharedMemory(name=name, create=False, track=False)
    except TypeError:
        if create:
            return shared_memory.SharedMemory(name=name, create=True, size=size)
        return shared_memory.SharedMemory(name=name, create=False)


def _initialize_worker(shared_memory_name: str) -> None:
    global _worker_shared_memory, _worker_values
    _worker_shared_memory = _open_shared_memory(shared_memory_name, create=False)
    _worker_values = memoryview(_worker_shared_memory.buf).cast("d")
    atexit.register(_cleanup_worker)


def _cleanup_worker() -> None:
    global _worker_shared_memory, _worker_values
    if _worker_values is not None:
        _worker_values.release()
        _worker_values = None
    if _worker_shared_memory is not None:
        _worker_shared_memory.close()
        _worker_shared_memory = None


def _sum_range(bounds: tuple[int, int]) -> float:
    start, end = bounds
    subtotal = 0.0
    for index in range(start, end):
        subtotal += _worker_values[index]
    return subtotal


def _generate_shared_array() -> shared_memory.SharedMemory:
    shared = _open_shared_memory(
        None,
        create=True,
        size=ELEMENT_COUNT * 8,
    )
    values = memoryview(shared.buf).cast("d")
    generator = random.Random(STUDENT_ID)
    for index in range(ELEMENT_COUNT):
        values[index] = generator.random()
    values.release()
    return shared


def _benchmark(worker_count: int, shared_memory_name: str) -> float:
    chunk_size = math.ceil(ELEMENT_COUNT / worker_count)
    bounds = [
        (start, min(start + chunk_size, ELEMENT_COUNT))
        for start in range(0, ELEMENT_COUNT, chunk_size)
    ]
    context = mp.get_context("spawn")
    start_ns = time.perf_counter_ns()
    with ProcessPoolExecutor(
        max_workers=worker_count,
        mp_context=context,
        initializer=_initialize_worker,
        initargs=(shared_memory_name,),
    ) as executor:
        partial_sums = list(executor.map(_sum_range, bounds))
    _ = math.fsum(partial_sums)
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def main() -> None:
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"CPU model: {platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER', 'Unknown')}")
    max_cores = os.cpu_count() or 1
    print(f"Logical cores: {max_cores}")
    print(f"Array elements: {ELEMENT_COUNT}")
    print("Parallel implementation: worker processes with shared float64 memory")
    print(f"Amdahl parallel fraction: {PARALLEL_FRACTION:.2f}")
    print()
    print("Cores | Wall Time (ms) | Speedup | Amdahl Upper Bound")
    print("------|-----------------|---------|-------------------")

    worker_counts = [1, 2, 4, max_cores, max_cores * 2]
    shared = _generate_shared_array()
    try:
        timings = []
        for worker_count in worker_counts:
            timings.append(_benchmark(worker_count, shared.name))

        baseline_ms = timings[0]
        for worker_count, elapsed_ms in zip(worker_counts, timings):
            speedup = baseline_ms / elapsed_ms
            amdahl_upper_bound = 1 / ((1 - PARALLEL_FRACTION) + PARALLEL_FRACTION / worker_count)
            print(
                f"{worker_count:5d} | {elapsed_ms:15.3f} | {speedup:7.3f} | "
                f"{amdahl_upper_bound:17.3f}"
            )
    finally:
        shared.close()
        shared.unlink()


if __name__ == "__main__":
    mp.freeze_support()
    main()
