# Task 02 — Deriving scaled speedup

Let one run on `P` processors take normalized parallel wall time `T_P = s+p=1`, where `s` is serial time and `p` is parallel time on the P-processor machine. Assume ideal division of the parallel work, no communication or imbalance, and the same serial portion in the scaled job.

1. During one unit of parallel wall time, the serial part consumes `s` units of processor time. The parallel part consumes `p` units on each of P processors.
2. Therefore, the total amount of work represented by the run, measured in single-processor time units, is `W_1 = s + Pp`. The parallel part takes P times its observed wall time on one processor because it was divided evenly across P processors.
3. The parallel execution time is `T_P=s+p=1`. Speedup against executing that same expanded workload serially is therefore `S(P)=W_1/T_P=s+Pp`.
4. Since `s+p=1`, substitute `p=1-s`: `S(P)=s+P(1-s)=P-s(P-1)`.
5. Writing the serial fraction as `α=s`, this is `S(P)=P-α(P-1)=α+(1-α)P`.

At `P=1`, speedup is 1. At `α=0`, it is ideal linear speedup `P`; at `α=1`, it is 1. The derivation is an ideal scaled-work model. Communication, synchronization, and processor inefficiency would add parallel runtime and reduce the measured speedup.
