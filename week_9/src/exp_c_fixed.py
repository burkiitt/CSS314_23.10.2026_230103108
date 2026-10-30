import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path


def private_worker(iterations):
    local_sum = 0
    for _ in range(iterations):
        local_sum += 1
    return local_sum


def run_privatized(workers, total_increments=20_000_000):
    iterations = total_increments // workers
    start = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        values = pool.map(private_worker, [iterations] * workers)
    elapsed = time.perf_counter() - start
    assert sum(values) == iterations * workers
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
    times = {p: run_privatized(p) for p in (1, 2, 4)}
    result = {"student_id": args.student_id, "experiment": "C_privatized", **metrics(times)}
    path = Path(__file__).resolve().parent.parent / "results" / "exp_c_fixed.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    mp.freeze_support()
    main()
