# Task 08 — Amdahl vs. Gustafson at P = 128

Take `s=α=0.08`, so the parallel fraction is 0.92.

**Amdahl, fixed workload**

`S_A(128)=1/[0.08+0.92/128]`

`=1/[0.08+0.0071875]=1/0.0871875≈11.4695`.

**Gustafson, scaled workload**

`S_G(128)=0.08+0.92×128=117.84`.

Gustafson predicts about `117.84/11.4695≈10.2742` times the Amdahl speedup. Expressed as percentage increase relative to Amdahl, the discrepancy is approximately **927.42%**. Equivalently, Amdahl is about **90.27% lower** than Gustafson when the difference is measured relative to the Gustafson value.

They diverge because Amdahl distributes the same fixed parallel work over more processors, while Gustafson increases parallel work to use the additional processors in a fixed-time run. The numbers are not competing predictions for one identical workload.
