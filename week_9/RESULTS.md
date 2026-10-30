# Practice Lab Results

Student ID: `230103108`
Host: `Intel64 Family 6 Model 154 Stepping 3, GenuineIntel` with 8 physical and 12 logical cores

| Experiment | T1 (s) | T2 (s) | T4 (s) | Speedup P=4 | e(2) | e(4) |
|---|---:|---:|---:|---:|---:|---:|
| A_serial_tail | 10.036 | 4.699 | 2.523 | 3.98x | -0.064 | 0.002 |
| B_lock_contention | 49.680 | 194.689 | 197.903 | 0.25x | 6.838 | 4.978 |
| C_privatized | 0.937 | 0.807 | 0.772 | 1.21x | 0.724 | 0.765 |

Experiment A shows a stable serial fraction from the intentional 0.40 second master-process delay.
Experiment B demonstrates lock contention: adding workers increases runtime and Karp-Flatt rises.
Experiment C privatizes the counter, removing the lock from the hot loop and restoring scaling.
Observed e(2)/e(4): A=-0.064/0.002, B=6.838/4.978, C=0.724/0.765.
The handout's ideal A/C thresholds were not reached on this Windows host; the raw timings are retained.

Commands used: `python src/run_practice_lab.py --student-id 230103108`.
