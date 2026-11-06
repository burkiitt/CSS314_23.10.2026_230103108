# Task 07 — Maximum tolerable serial fraction

Gustafson speedup is `S(P)=P-α(P-1)`. Require `S(P)≥S_min`, with P=8192 and `S_min=7500`:

`8192 - α(8191) ≥ 7500`

`α(8191) ≤ 692`

`α ≤ 692/8191 ≈ 0.0844829691`.

Therefore the maximum serial fraction under this ideal model is approximately **8.4483%**. At that boundary the predicted speedup is exactly 7500. Any communication overhead included outside α would consume additional performance margin.
