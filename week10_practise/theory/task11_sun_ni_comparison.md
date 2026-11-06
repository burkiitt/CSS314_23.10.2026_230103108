# Task 11 — Gustafson and Sun–Ni memory-bounded speedup

## Different scaling constraints

Gustafson's simplified fixed-time model scales workload to use P processors while keeping parallel wall time approximately fixed. With parallel-run serial fraction α, its speedup is `S_G(P)=α+(1-α)P`.

Sun and Ni's memory-bounded model instead asks how performance changes when aggregate memory capacity grows. In a homogeneous cluster with M bytes per node, P nodes supply roughly `PM` bytes. If an algorithm's maximum workload supported by memory M is `W=g(M)`, a memory-bounded scaled problem can grow as `W*(P)=g(PM)`. The growth need not be linear in P; it depends on the algorithm's data representation and memory requirement. The full Sun–Ni formulation also accounts for workload parallelism, allocation and communication. In their simplified two-part case, memory-bounded speedup contains fixed-size/Amdahl and fixed-time/Gustafson behavior as special cases.

## When Gustafson can misestimate throughput

Gustafson can **overestimate** achievable throughput when the new work causes communication, synchronization, serial I/O, load imbalance, or memory-bandwidth pressure to grow with P; when per-node memory is insufficient; or when the workload does not expose enough independent parallelism. Assuming constant α and perfect parallel work in those settings is optimistic.

It can **underestimate** useful throughput when added memory enables an algorithmic change or larger data set whose useful work grows faster than the simple fixed-work-per-node model, when larger instances reuse setup costs or amortize fixed overhead, or when the target metric rewards increased resolution/accuracy rather than raw speedup. This is not a guarantee of superlinear processor speedup: it means Gustafson's linear workload assumption may fail to capture the value of memory-enabled work.

## Practical distinction

Use Gustafson when the constraint is roughly fixed turnaround time and compute capacity is the limiting resource. Use Sun–Ni reasoning when the application is memory-bound and aggregate memory capacity determines the largest feasible problem. In either case, measure effective capacity, communication, and algorithm-specific `g(M)` rather than assuming workload scales exactly with processor count.

**Reference:** X.-H. Sun and L. M. Ni, “Scalable Problems and Memory-Bounded Speedup,” *Journal of Parallel and Distributed Computing*, 19 (1993), 27–37. [Paper copy](https://www.cs.iit.edu/~scs/psfiles/Sun_and_Ni_JPDC1993.pdf); [publication record and abstract](https://grc.iit.edu/gnosis/publications/sun-1993-scalable-problems-ec6f).
