# Gustafson's Law: parallel computing practice

Small, runnable practice repository for weak scaling, measurements, a least-squares fit, and a scaling plot. The benchmark uses Python's standard library and one process per worker; the plot is a vector PDF created without plotting dependencies.

## Contents

- [Run the benchmark](#run-the-benchmark)
- [Mathematical model](#mathematical-model)
- [Results and interpretation](#results-and-interpretation)
- [When weak scaling is useful](#when-weak-scaling-is-useful)
- [Repository artifact index](#repository-artifact-index)
- [Earlier practice tasks](#earlier-practice-tasks)

## Run the benchmark

Requires Python 3.9 or later. No package installation or compilation is needed.

From the repository root:

```powershell
python benchmarks/weak_scale_bench/benchmark.py --max-workers 12 --iterations-per-worker 300000 --repeats 5 --output benchmarks/results.csv
python benchmarks/fit_gustafson.py --input benchmarks/results.csv --plot plots/scaling_comparison.pdf --summary benchmarks/summary.csv
```

Use the host's available logical processor count for `--max-workers` (the default is `os.cpu_count()`). The benchmark runs every count from 1 through that maximum. For a quicker sample across selected counts, add, for example, `--workers 1 2 4 8 12`; every requested count still gets the selected number of repetitions. Increase `--iterations-per-worker` for longer, steadier measurements. Each worker receives exactly that many loop iterations.

The CSV is raw per-run wall time. `fit_gustafson.py` groups runs, writes mean and sample standard deviation to `benchmarks/summary.csv`, estimates alpha from group means, and writes the requested vector PDF. The plot's measured error bars show standard error of the mean, converted to speedup units. Outputs are overwritten on each run.

## Mathematical model

For a fixed-size problem, Amdahl's law gives speedup

`S_A(N) = 1 / (alpha + (1-alpha)/N)`.

For weak scaling, Gustafson's law scales the parallel work with processor count and gives

`S_G(N) = alpha + (1-alpha)N = N - alpha(N-1)`,

where `N` is the worker count and `alpha` is the serial fraction. Ideal linear speedup is `S(N)=N`, corresponding to `alpha=0`. The model is a simplifying estimate: communication, scheduling, synchronization, and resource contention can all lower measured speedup.

This benchmark keeps per-worker work fixed. For each worker count, the script measures elapsed wall time `T(N)` and computes empirical speedup as `T(1)/T(N)`. The fit uses the weak-scaling efficiency identity

`E(N) = S(N)/N = 1 - alpha(1-1/N)`.

Let `x_i=1-1/N_i` and `y_i=1-T(1)/T(N_i)`. The least-squares fit constrained through the origin is `alpha = sum(x_i*y_i)/sum(x_i*x_i)`, clipped to the physical interval `[0,1]`. This simple estimator treats the one-worker mean as the baseline; it does not model uncertainty in that baseline or systematic process startup cost.

## Results and interpretation

The checked-in dataset was collected on 2026-11-06 on a host exposing 12 logical processors. It contains five independent runs at each count from 1 to 12, with 300,000 iterations per worker. The fitted observed serial fraction was approximately `0.622`. Mean runtime rose from `0.225 s` at one worker to `0.743 s` at twelve; there was no sustained speedup. Short jobs and process-pool setup cost materially affect these timings, and the 5-worker data was unusually variable. See the [hardware audit](analysis/task24_hardware_audit.md) for the recorded CPU information and measurement limits.

Do not treat this alpha as a universal program constant. It describes this experiment's Python workload, runtime, machine and session. For better estimates, increase per-worker work, control background load, and collect more repetitions together with temperature, frequency, affinity, memory-channel and NUMA information.

## When weak scaling is useful

Design around weak scaling when a real application grows its total problem with available compute: larger simulations, more particles or grid cells, higher-resolution data, or more independent requests. Keep work per worker approximately stable, minimize communication and global synchronization, and measure the actual end-to-end output rate as the system grows.

Use Amdahl-style fixed-size analysis when the workload size stays constant and the question is how quickly the same job finishes. In both cases, keep serial setup, data movement, synchronization, and resource limits in the measurement; a theoretical curve is a guide, not a performance promise.

## Repository artifact index

| Path | Purpose |
| --- | --- |
| `theory/task01_scaling_models.md`–`theory/task05_historical_ncube.md` | Scaling foundations, derivation, serial-fraction comparison, limits, and historical case. |
| `calculations/task06_parametric_table.md`–`calculations/task10_memory_growth.md` | Parametric speedup, serial-overhead tolerance, model comparison, phase fractions, and memory limits. |
| `theory/task11_sun_ni_comparison.md`–`theory/task12_communication_penalty.md` | Memory-bounded speedup and communication-penalty extension. |
| `benchmarks/weak_scale_bench/benchmark.py` | Process-based weak-scaling benchmark; defaults to worker counts 1 through host logical concurrency. |
| `benchmarks/results.csv` | Raw measurements: 12 worker configurations × 5 runs. |
| `benchmarks/fit_gustafson.py` | Summary statistics, least-squares alpha fit, and vector PDF generation. |
| `benchmarks/summary.csv` | Derived mean, standard deviation, speedup and speedup standard error. |
| `plots/scaling_comparison.pdf` | Ideal, Gustafson, Amdahl and measured speedup with standard error bars. |
| `analysis/task24_hardware_audit.md` | Hardware record, observed deviations, and evidence limitations. |
| `README.md` | This repository guide and task artifact index. |

## Task sheet coverage

Answer files are present for Tasks 01–12 and 22–25. The task sheet text for Tasks 13–21 was not included in the materials received so far; their questions and answers are not guessed. Add those files and index entries when their prompts are available.
