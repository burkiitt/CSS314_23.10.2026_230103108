import argparse
import ctypes
import multiprocessing as mp
import statistics
import time
from pathlib import Path


K = 5_000_000
PROCESSES = (1, 2, 4, 8)


def unpadded_worker(values, worker, iterations):
    for _ in range(iterations):
        values[worker] += 1


def padded_worker(values, worker, iterations):
    index = worker * 8
    for _ in range(iterations):
        values[index] += 1


def privatized_worker(values, worker, iterations):
    total = 0
    for _ in range(iterations):
        total += 1
    values[worker] = total


def run(strategy, workers, iterations, repeats=3):
    context = mp.get_context("spawn")
    times = []
    total = 0
    for _ in range(repeats):
        size = workers * 8 if strategy == "padded" else workers
        values = context.Array(ctypes.c_int64, size, lock=False)
        target = {"unpadded": unpadded_worker,
                  "padded": padded_worker,
                  "privatized": privatized_worker}[strategy]
        processes = [context.Process(target=target, args=(values, worker, iterations))
                     for worker in range(workers)]
        start = time.perf_counter_ns()
        for process in processes:
            process.start()
        for process in processes:
            process.join()
        times.append(time.perf_counter_ns() - start)
        total = sum(values[worker * 8 if strategy == "padded" else worker]
                    for worker in range(workers))
    return int(statistics.median(times)), total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=K)
    args = parser.parse_args()
    result_rows = []
    all_measurements = {}
    for strategy in ("unpadded", "padded", "privatized"):
        measurements = {}
        for workers in PROCESSES:
            elapsed, total = run(strategy, workers, args.iterations)
            measurements[workers] = elapsed
            result_rows.append([strategy, workers, args.iterations, elapsed, total, "", ""])
        all_measurements[strategy] = measurements
        first = measurements[1]
        for row in result_rows:
            if row[0] == strategy:
                row[5] = measurements[row[1]] and first / measurements[row[1]]
                row[6] = ((row[1] * measurements[row[1]] / first) - 1) / (row[1] - 1) \
                    if row[1] > 1 else ""

    unpadded_first = all_measurements["unpadded"][1]
    padded_first = all_measurements["padded"][1]
    for row in result_rows:
        p = row[1]
        unpadded_e = ((p * all_measurements["unpadded"][p] / unpadded_first) - 1) / (p - 1) if p > 1 else ""
        padded_e = ((p * all_measurements["padded"][p] / padded_first) - 1) / (p - 1) if p > 1 else ""
        row.extend([p, unpadded_e, padded_e])

    output = Path(__file__).resolve().parent.parent / "results" / "false_sharing_karp_flatt.tsv"
    header = "strategy\tprocesses\titerations\ttime_ns\ttotal_count\tspeedup\tkarp_flatt\tp\te_unpadded\te_padded\n"
    output.write_text(header + "\n".join("\t".join(map(str, row)) for row in result_rows) + "\n",
                      encoding="utf-8")
    print(output)


if __name__ == "__main__":
    mp.freeze_support()
    main()
