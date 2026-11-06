# Task 01 — Strong scaling vs. weak scaling

## Two different questions

**Amdahl (1967)** asks: how much faster can the *same fixed job* finish if more processors are assigned? If the serial share is `s`, the workload does not grow with processor count `P`. Its idealized speedup is

`S_A(P) = 1 / (s + (1-s)/P)`.

As `P → ∞`, the input dimension and total work remain fixed: `W(P)=W(1)`. Each processor receives less parallel work. The serial part imposes the ceiling `1/s`.

**Gustafson (1988)** asks: how much more useful work can finish in roughly the same wall-clock time as processors are added? The parallel workload grows with `P`, often keeping work per processor approximately constant. For a one-dimensional workload measure, `W(P) ∝ P`; for a d-dimensional grid, a common idealized scaling is that its volume grows as `P` and its side length as `P^(1/d)`. The exact geometric dimension depends on the application, not the law itself.

If the serial fraction measured during a P-processor run is `α`, normalized parallel runtime is `α+(1-α)=1`, and the corresponding serial processor would perform `α+(1-α)P` units of work. Thus `S_G(P)=α+(1-α)P`.

## Why the names differ

Strong scaling holds problem size fixed and asks how execution time falls as processors increase. Weak scaling holds per-processor work approximately fixed, so total problem size grows, and asks how much work fits in a roughly fixed time. Gustafson's model is often called fixed-time or scaled speedup; real applications may still see runtime rise due to communication, memory limits, or load imbalance.

The divergence is physical as well as mathematical: Amdahl allocates more compute to a fixed finite job; Gustafson uses the added compute to resolve a larger domain, more particles, or finer resolution. They answer different workload questions rather than contradict one another.
