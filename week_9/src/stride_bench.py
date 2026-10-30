import argparse
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
def reduce_stride(data, stride):
    total = 0.0
    for index in range(0, data.size, stride):
        total += data[index]
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    params = get_student_params(args.student_id)
    data = np.ones(params["buffer_elements"], dtype=np.float64)
    rows = []
    for stride in (1, 2, 4, 8, 16, 32, 64, 128):
        total = 0.0
        for _ in range(5):
            total = reduce_stride(data, stride)
        times = []
        touched = (data.size + stride - 1) // stride
        for _ in range(5):
            start = time.perf_counter_ns()
            total = reduce_stride(data, stride)
            times.append(time.perf_counter_ns() - start)
        median = statistics.median(times)
        rows.append((stride, touched, int(median), median / touched, median / touched, total))

    output = Path(__file__).resolve().parent.parent / "results" / "stride_results.tsv"
    output.write_text(
        "stride\telements_touched\tmedian_time_ns\tns_per_element\tlatency_ns\tchecksum\n"
        + "\n".join("\t".join(map(str, row)) for row in rows)
        + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
