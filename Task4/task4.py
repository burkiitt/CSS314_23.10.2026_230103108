import queue
import threading
import time


ITEM_COUNT = 1_000
WORKER_COUNT = 4
DYNAMIC_CHUNK_SIZE = 1


def _process_item(item: int) -> None:
    time.sleep(0.0001 * (item % 20))


def _completion_delta_ms(completion_times: list[int]) -> tuple[float, float, float]:
    first_ms = min(completion_times) / 1_000_000
    last_ms = max(completion_times) / 1_000_000
    return first_ms, last_ms, last_ms - first_ms


def _run_static() -> tuple[float, float, float]:
    completion_times: list[int] = [0] * WORKER_COUNT
    block_size = ITEM_COUNT // WORKER_COUNT

    def worker(worker_id: int, items: range) -> None:
        for item in items:
            _process_item(item)
        completion_times[worker_id] = time.perf_counter_ns()

    threads = [
        threading.Thread(
            target=worker,
            args=(worker_id, range(worker_id * block_size, (worker_id + 1) * block_size)),
            name=f"static-worker-{worker_id}",
        )
        for worker_id in range(WORKER_COUNT)
    ]
    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    first_ms, last_ms, delta_ms = _completion_delta_ms(
        [completion_time - start_ns for completion_time in completion_times]
    )
    return elapsed_ms, last_ms - first_ms, delta_ms


def _run_dynamic() -> tuple[float, float, float]:
    work_queue: queue.Queue[list[int] | None] = queue.Queue()
    completion_times: list[int] = [0] * WORKER_COUNT

    for start in range(0, ITEM_COUNT, DYNAMIC_CHUNK_SIZE):
        work_queue.put(list(range(start, min(start + DYNAMIC_CHUNK_SIZE, ITEM_COUNT))))
    for _ in range(WORKER_COUNT):
        work_queue.put(None)

    def worker(worker_id: int) -> None:
        while True:
            chunk = work_queue.get()
            try:
                if chunk is None:
                    return
                for item in chunk:
                    _process_item(item)
            finally:
                work_queue.task_done()
            
    threads = [
        threading.Thread(target=worker, args=(worker_id,), name=f"dynamic-worker-{worker_id}")
        for worker_id in range(WORKER_COUNT)
    ]
    start_ns = time.perf_counter_ns()
    for thread in threads:
        thread.start()
    work_queue.join()
    for worker_id, thread in enumerate(threads):
        thread.join()
        completion_times[worker_id] = time.perf_counter_ns()
    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    first_ms, last_ms, delta_ms = _completion_delta_ms(
        [completion_time - start_ns for completion_time in completion_times]
    )
    return elapsed_ms, last_ms - first_ms, delta_ms


def main() -> None:
    static_elapsed, static_last, static_delta = _run_static()
    dynamic_elapsed, dynamic_last, dynamic_delta = _run_dynamic()

    print(f"Items: {ITEM_COUNT}")
    print(f"Workers: {WORKER_COUNT}")
    print("Workload: sleep(0.0001 * (i % 20))")
    print()
    print("Strategy              Chunk  Total Time (ms)  Completion Delta (ms)")
    print("--------------------  -----  ---------------  ---------------------")
    print(f"Static chunks         {ITEM_COUNT // WORKER_COUNT:5d}  {static_elapsed:15.3f}  {static_delta:21.3f}")
    print(f"Dynamic work queue    {DYNAMIC_CHUNK_SIZE:5d}  {dynamic_elapsed:15.3f}  {dynamic_delta:21.3f}")
    print()
    print(f"Static completion range: 0.000 ms to {static_last:.3f} ms")
    print(f"Dynamic completion range: 0.000 ms to {dynamic_last:.3f} ms")


if __name__ == "__main__":
    main()
