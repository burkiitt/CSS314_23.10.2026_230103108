"""Experiment C: batch local results before crossing the IPC boundary."""

import multiprocessing as mp
import time


def buffered_worker(out_queue: mp.Queue, items_per_worker: int,
                    batch_size: int = 10_000) -> None:
    buffer = []
    for i in range(items_per_worker):
        buffer.append(i % 7)
        if len(buffer) >= batch_size:
            out_queue.put(sum(buffer))
            buffer.clear()
    if buffer:
        out_queue.put(sum(buffer))
    out_queue.put(None)


def run_buffered(workers: int, total_items: int = 10_000_000,
                 batch_size: int = 10_000) -> tuple[float, int]:
    queue = mp.Queue()
    items_per_worker = total_items // workers
    processes = [
        mp.Process(
            target=buffered_worker,
            args=(queue, items_per_worker, batch_size),
        )
        for _ in range(workers)
    ]
    start = time.perf_counter()
    for process in processes:
        process.start()

    total_sum = 0
    active = workers
    while active:
        value = queue.get()
        if value is None:
            active -= 1
        else:
            total_sum += value

    for process in processes:
        process.join()
    queue.close()
    queue.join_thread()
    return time.perf_counter() - start, total_sum


def main() -> None:
    timings = {}
    checksum = None
    for p in (1, 2, 4, 8):
        timings[p], checksum = run_buffered(p)
        print(f"P={p:2d} | Time={timings[p]:8.3f}s | checksum={checksum}")

    baseline = timings[1]
    print("\nBuffered aggregation analysis")
    for p in (2, 4, 8):
        speedup = baseline / timings[p]
        karp_flatt = ((p * timings[p] / baseline) - 1) / (p - 1)
        print(f"P={p:2d} | Speedup={speedup:6.2f}x | Karp-Flatt e={karp_flatt:7.3f}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
