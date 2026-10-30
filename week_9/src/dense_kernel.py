import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from salt import get_student_params

try:
    from numba import njit
except ImportError:
    def njit(function):
        return function


@njit
def naive(a, b, m):
    c = np.zeros((m, m), dtype=np.float64)
    for i in range(m):
        for j in range(m):
            for k in range(m):
                c[i, j] += a[i, k] * b[k, j]
    return c


@njit
def interchanged(a, b, m):
    c = np.zeros((m, m), dtype=np.float64)
    for i in range(m):
        for k in range(m):
            value = a[i, k]
            for j in range(m):
                c[i, j] += value * b[k, j]
    return c


def measure(function, a, b, m):
    times = []
    result = None
    for _ in range(3):
        start = time.perf_counter_ns()
        result = function(a, b, m)
        times.append(time.perf_counter_ns() - start)
    return result, statistics.median(times)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    params = get_student_params(args.student_id)
    n = params["N"]
    m = n // 2
    rng = np.random.default_rng(params["seed"])
    a = rng.random((n, n), dtype=np.float64)
    b = rng.random((n, n), dtype=np.float64)
    naive(a, b, 2)
    interchanged(a, b, 2)
    baseline, naive_time = measure(naive, a, b, m)
    improved, interchanged_time = measure(interchanged, a, b, m)
    result = {
        "student_id": args.student_id,
        "N": n,
        "M": m,
        "naive_median_time_ns": int(naive_time),
        "interchanged_median_time_ns": int(interchanged_time),
        "speedup": naive_time / interchanged_time,
        "max_abs_error": float(np.max(np.abs(baseline - improved))),
    }
    output = Path(__file__).resolve().parent.parent / "results" / "loop_interchange.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
