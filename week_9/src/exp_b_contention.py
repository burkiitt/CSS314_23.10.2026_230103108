import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path


def contended_worker(counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            counter.value += 1


def run_contended(workers, total_increments=20_000_000):
    iterations = total_increments // workers
    counter = mp.Value("i", 0, lock=False)
    lock = mp.Lock()
    processes = [mp.Process(target=contended_worker, args=(counter, lock, iterations))
                 for _ in range(workers)]
    start = time.perf_counter()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    elapsed = time.perf_counter() - start
    assert counter.value == iterations * workers
    return elapsed


def metrics(times):
    t1 = times[1]
    return {"times": times, "speedups": {str(p): t1 / value for p, value in times.items()},
            "karp_flatt": {str(p): ((p * times[p] / t1) - 1) / (p - 1)
                           for p in times if p > 1}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    times = {p: run_contended(p) for p in (1, 2, 4)}
    result = {"student_id": args.student_id, "experiment": "B_lock_contention", **metrics(times)}
    path = Path(__file__).resolve().parent.parent / "results" / "exp_b_contention.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    mp.freeze_support()
    main()
