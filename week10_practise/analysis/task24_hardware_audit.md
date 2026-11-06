# Task 24: Hardware audit and observed deviations

## Recorded environment

- CPU reported by the host Windows processor registry: Intel Core i5-12450H, 12th Gen (Alder Lake-H), 8 physical cores (4 Performance + 4 Efficient) and 12 logical processors. The benchmark's `os.cpu_count()` also reported 12. This is the host-visible logical count; a managed environment may schedule fewer CPU resources than the host exposes.
- Intel lists 12 MB Intel Smart Cache (L3) and support for up to two memory channels. These are processor capabilities. L1/L2 sizes and the installed RAM channel population could not be read in this environment, so they are not inferred here. [Intel processor specifications](https://www.intel.com/content/www/us/en/products/sku/132222/intel-core-i512450h-processor-12m-cache-up-to-4-40-ghz/specifications.html)
- Windows management queries for cache and memory returned access denied. The available host information does not establish whether the OS exposes multiple NUMA nodes. No NUMA placement was configured or measured.
- The benchmark ran on 2026-11-06 using Python's `ProcessPoolExecutor`, 300,000 integer-loop iterations per process, five repetitions at each worker count from 1 to 12. Each repetition includes process-pool startup and shutdown.

## Observations

The average runtime was 0.225 s at one worker and 0.213 s at two workers; it increased to 0.743 s at twelve. The 5-worker measurements were especially noisy (mean 1.332 s, standard deviation 0.685 s). The least-squares estimate from the mean runtimes is `alpha_observed = 0.622` under the fit described in the root README and `benchmarks/fit_gustafson.py`.

These results are far from ideal weak scaling. Process creation, Python interpreter overhead, CPU scheduling, and contention are significant compared with the short per-process job. The noisy 5-worker group suggests transient host load or scheduling variation. This dataset does not contain temperature, clock-frequency, power, or affinity telemetry, so thermal throttling cannot be established as the cause. Likewise, there is no NUMA topology/placement evidence to attribute a change to NUMA boundaries. The CPU has a hybrid core design; scheduling workers across Performance and Efficient cores can also change throughput.

Treat the fitted fraction as an empirical summary of this machine, runtime, workload size, and measurement session. Increase the work per worker and repeat under controlled conditions before drawing architectural conclusions. For a serious hardware audit, record actual installed DIMM/channel configuration, OS-visible cache topology and NUMA nodes, CPU affinity, temperature and effective clocks alongside each run.
