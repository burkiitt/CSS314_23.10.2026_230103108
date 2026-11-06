# Task 12 — Gustafson model with communication cost

Normalize ideal parallel runtime for the scaled problem to `s+p=1`, where `s=α` and `p=1-α`. The equivalent serial execution of the useful computation takes `s+Pp`. Now let `C(P)≥0` be communication and synchronization wall time on the P-processor machine, measured in the same normalized time units. The actual parallel runtime is `1+C(P)`, giving

`S_C(P) = [s+Pp]/[1+C(P)] = [α+(1-α)P]/[1+C(P)]`.

This extension assumes C(P) is overhead not already included in `s` or `p`; otherwise it would be double-counted. It also assumes the added communication does not change the useful-work numerator. If communication replaces useful work or changes load balance, the numerator and α need to be remeasured.

Examples, with constants expressed in normalized runtime units:

- Logarithmic cost `C(P)=c log(P)`: `S_C(P)≈(1-α)P/[c log(P)]` for large P. Speedup continues to grow, but sublinearly, and efficiency tends to zero like `(1-α)/[c log(P)]`.
- Surface-like cost `C(P)=c√P`: `S_C(P)≈(1-α)√P/c`; speedup is sublinear and efficiency tends to zero like `(1-α)/(c√P)`.
- Constant cost `C(P)=c`: speedup remains asymptotically linear with slope `(1-α)/(1+c)`.

These are illustrative asymptotics, not universal communication laws. For a particular topology and algorithm, measure or model message latency, bytes transferred, synchronization frequency, and overlap, then substitute that cost into C(P).
