import argparse
import json
import math
import multiprocessing as mp
import time
from pathlib import Path


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def run_experiment(workers, total_chunks=16, chunk_size=2_000_000):
    start = time.perf_counter()
    time.sleep(0.40)
    with mp.Pool(processes=workers) as pool:
        pool.map(heavy_math, [chunk_size] * total_chunks)
    return time.perf_counter() - start


def metrics(times):
    t1 = times[1]
    return {"times": times, "speedups": {str(p): t1 / value for p, value in times.items()},
            "karp_flatt": {str(p): ((p * times[p] / t1) - 1) / (p - 1)
                           for p in times if p > 1}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    times = {p: run_experiment(p) for p in (1, 2, 4)}
    result = {"student_id": args.student_id, "experiment": "A_serial_tail", **metrics(times)}
    path = Path(__file__).resolve().parent.parent / "results" / "exp_a_serial.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    mp.freeze_support()
    main()
