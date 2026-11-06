# Task 06 — Speedup and efficiency at α = 0.04

Use `S(P)=α+(1-α)P=0.04+0.96P` and `E(P)=S(P)/P=0.96+0.04/P`.

| P | Calculation for S(P) | Scaled speedup | Efficiency |
|---:|---|---:|---:|
| 16 | 0.04 + 0.96×16 | 15.40 | 0.962500 (96.2500%) |
| 64 | 0.04 + 0.96×64 | 61.48 | 0.960625 (96.0625%) |
| 256 | 0.04 + 0.96×256 | 245.80 | 0.960156 (96.0156%) |
| 1,024 | 0.04 + 0.96×1,024 | 983.08 | 0.960039 (96.0039%) |
| 4,096 | 0.04 + 0.96×4,096 | 3,932.20 | 0.960010 (96.0010%) |
| 16,384 | 0.04 + 0.96×16,384 | 15,728.68 | 0.960002 (96.0002%) |

Efficiency approaches `1-α=0.96` from above as P grows, while speedup grows almost linearly. This constant-efficiency conclusion assumes α stays at 4% and omits growing communication, synchronization, and memory costs.
