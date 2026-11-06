# Task 03 — Serial-fraction frame of reference

The apparent paradox comes from comparing fractions defined against different workloads.

In Amdahl's fixed-size model, let a fixed job require serial work `S` and parallelizable work `Q`. On one processor its runtime is `S+Q`; the measured serial fraction is `s_A=S/(S+Q)`. With P processors and ideal parallel work division, runtime is `S+Q/P`, so

`S_A(P) = (S+Q)/(S+Q/P) = 1/[s_A+(1-s_A)/P]`.

Here the serial work remains fixed while total work is fixed. Its share of *parallel runtime* becomes `S/(S+Q/P)`, which rises toward 1 as P grows. This is why a fixed serial segment eventually dominates a fixed job.

For Gustafson scaling, normalize the observed P-processor run to time 1. Let serial runtime on that machine be `α` and parallel runtime be `1-α`. The equivalent serial execution of the scaled workload takes `α+P(1-α)`. Thus `S_G(P)=α+P(1-α)`. The serial time is measured as a share of the parallel run; the parallel work, and hence the reference serial workload, grows with P.

There is no claim that a fixed serial operation disappears. Its *fraction of the expanded total work* becomes smaller because the parallel work grows. Meanwhile its fraction of the parallel wall time is held at α by the scaling premise. Amdahl's `s_A` and Gustafson's `α` cannot generally be substituted for each other without specifying the workload and measurement frame. If communication or coordination grows with P, α itself may no longer remain constant and Gustafson's ideal formula must be extended.
