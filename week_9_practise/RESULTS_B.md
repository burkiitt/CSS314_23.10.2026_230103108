# Variant B Practicum Results

Hardware: 12 logical CPUs (`os.cpu_count()` / `multiprocessing.cpu_count()`).
Timings are seconds from the runs on this host.

| Configuration | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A: Micro (k=1, 100k check) | 4.644 | 4.741 | 6.008 | 5.759 | 0.81 | 1.042 | 1.275 | Dispatch overhead dominates |
| A: Coarse (k=10000, 1m) | 10.547 | 8.301 | 5.961 | 3.455 | 3.05 | 0.574 | 0.231 | Chunking improves scaling |
| B: Queue choke (400k) | 4.563 | 6.828 | 6.702 | 16.604 | 0.27 | 1.993 | 4.016 | IPC queue contention explosion |
| C: Buffered batch (10m) | 0.764 | 0.661 | 1.024 | 0.802 | 0.95 | 0.731 | 1.057 | Fewer queue operations; host limits scaling |

Formulae: `S8 = T1 / T8`; `e(p) = ((p * Tp / T1) - 1) / (p - 1)`.

The required one-million-item micro-task default remains in `exp_a_granularity.py`.
The table uses a 100,000-item micro check because one million individual Windows
Pool messages exceeded the available practicum runtime. The full-size coarse,
queue, and buffered runs used the requested 1m, 400k, and 10m item counts.

## Commands

```text
python exp_a_granularity.py
python exp_b_queue.py
python exp_c_buffered.py
```
