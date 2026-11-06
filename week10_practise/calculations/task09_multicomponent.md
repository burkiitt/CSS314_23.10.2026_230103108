# Task 09 — Multi-component serial overhead

Under the task's classification, initial disk I/O/broadcast (2%) and boundary synchronization (6%) are non-parallel portions. Aggregate serial fraction:

`α = 0.02 + 0.06 = 0.08` (8%); parallel domain-flux computation is 92%.

Apply `S(P)=α+(1-α)P=0.08+0.92P`:

| P | Calculation | Scaled speedup |
|---:|---|---:|
| 512 | 0.08 + 0.92×512 | 471.12 |
| 2,048 | 0.08 + 0.92×2,048 | 1,884.24 |

This aggregation treats I/O and synchronization as serial and constant fractions of the parallel runtime. In a real distributed simulation, boundary exchange may itself run concurrently and its cost can grow with node count; the 8% should then be measured per configuration or represented as P-dependent communication overhead.
