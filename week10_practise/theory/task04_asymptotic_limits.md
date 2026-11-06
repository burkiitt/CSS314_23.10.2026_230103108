# Task 04 — Asymptotic efficiency

## Gustafson

With serial fraction `α`,

`S_G(P)=α+(1-α)P` and `E_G(P)=S_G(P)/P=(1-α)+α/P`.

Taking the limit,

`lim(P→∞) E_G(P) = 1-α`,

because `α/P → 0`. Under constant α, efficiency therefore approaches the parallel fraction rather than zero. This result depends on weak scaling and excludes increasing overhead.

## Amdahl

For fixed-size scaling,

`S_A(P)=1/[α+(1-α)/P]`, so `E_A(P)=1/[αP+(1-α)]`.

If `α>0`, the denominator grows without bound and `lim(P→∞) E_A(P)=0`; speedup itself approaches `1/α`. If `α=0`, both models give ideal speedup P and efficiency 1. This contrast is due to the different workload scaling assumptions, not an algebraic inconsistency.
