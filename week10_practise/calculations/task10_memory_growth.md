# Task 10 — Memory ceiling for a 3D grid

With `K` nodes and a strict 32 GB/node cap, the aggregate memory ceiling is `M_total=32K GB`. For one stored scalar per grid point using `b` bytes per point, a cubic grid of side length N requires approximately `bN³` bytes. Thus

`N_max = floor((32K × 10^9 / b)^(1/3))` points per side (decimal GB),

or use `32×2^30` bytes per node if “GB” means GiB. In weak scaling, memory per node is constant and total memory grows linearly with K; for fixed bytes per point, the maximum global number of grid points grows as K, while the side length grows as `K^(1/3)`.

| Nodes K | Aggregate cap | Maximum grid side (symbolic) |
|---:|---:|---:|
| 64 | 2,048 GB | `floor((2.048×10^12 / b)^(1/3))` |
| 512 | 16,384 GB | `floor((1.6384×10^13 / b)^(1/3))` |

The prompt does not specify bytes per grid point, number of arrays, ghost cells, solver workspaces, or OS/runtime reservation. Consequently a unique numeric N cannot be calculated. For illustration only, if there were exactly one 8-byte value per cell and decimal GB were used, the idealized sides are `floor((2.048×10^12/8)^(1/3)) = 6,349` points (64 nodes) and `floor((1.6384×10^13/8)^(1/3)) = 12,699` points (512 nodes). Real solver limits are smaller when additional fields and halos are included. The 512-node system has 8× the aggregate memory of the 64-node system, so under these assumptions its 3D side is only 2× as large.
