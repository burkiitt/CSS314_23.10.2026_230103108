"""Experiment B: show contention caused by one IPC Queue put per item."""

import multiprocessing as mp
import time


def queue_worker(out_queue: mp.Queue, items_per_worker: int) -> None:
    for i in range(items_per_worker):
        out_queue.put(i % 7)


def run_queue_benchmark(workers: int, total_items: int = 400_000) -> float:
    queue = mp.Queue()
    items_per_worker = total_items // workers
    processes = [
        mp.Process(target=queue_worker, args=(queue, items_per_worker))
        for _ in range(workers)
    ]
    start = time.perf_counter()
    for process in processes:
        process.start()

    for _ in range(items_per_worker * workers):
        queue.get()

    for process in processes:
        process.join()
    queue.close()
    queue.join_thread()
    return time.perf_counter() - start


def main() -> None:
    timings = {p: run_queue_benchmark(p) for p in (1, 2, 4, 8)}
    baseline = timings[1]
    print("\nQueue contention")
    for p, elapsed in timings.items():
        speedup = baseline / elapsed
        if p == 1:
            print(f"P={p:2d} | Time={elapsed:8.3f}s")
        else:
            karp_flatt = ((p * elapsed / baseline) - 1) / (p - 1)
            print(
                f"P={p:2d} | Time={elapsed:8.3f}s | Speedup={speedup:6.2f}x "
                f"| Karp-Flatt e={karp_flatt:7.3f}"
            )


if __name__ == "__main__":
    mp.freeze_support()
    main()
