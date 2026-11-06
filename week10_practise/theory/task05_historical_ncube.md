# Task 05 — Gustafson's 1024-processor hypercube results

## Historical reconstruction

Gustafson, Montry, and Benner's 1988 paper, *Development of Parallel Methods for a 1024-Processor Hypercube*, reports three full-scale scientific applications: wave mechanics, fluid dynamics, and structural analysis. The platform was a 1024-processor MIMD hypercube at Sandia. They describe algorithmic methods to keep serial and communication overhead small while varying both processor count and problem size.

The paper reports measured speedups of **502–637× for fixed-size problems** and **1009–1020× for scaled problems with fixed problem size per processor**. The latter reaches roughly the processor count because increasing the ensemble also increases total problem size. It is therefore not a claim that a fixed serial workload vanished, nor that every 1024-processor job ran exactly 1024 times faster.

The sheet's 0.4% serial fraction is a useful illustration: under Amdahl's ideal formula, `S_A(1024)=1/[0.004+0.996/1024]≈203.2`, an upper bound for that fixed-size model. Under Gustafson's formula, `S_G(1024)=0.004+0.996×1024≈1020`, consistent with the reported scaled range. These are model calculations; the paper's application-specific measurements should not be represented as all having exactly α=0.004.

The experiment made the workload definition visible: fixed problem size yields the conventional speedup; fixed work per processor measures scaled speedup. Problem expansion does not break Amdahl's result. It answers a different, practically important question: how much larger a scientific problem can be handled in about the same time on a larger machine.

## Source

- Gustafson, J. L., Montry, G. R., and Benner, R. E. (1988), “Development of Parallel Methods for a 1024-Processor Hypercube,” *SIAM Journal on Scientific and Statistical Computing*, 9(4), 609–638. [Author-hosted paper copy](https://rsim.cs.illinois.edu/arch/qual_papers/systems/6.pdf).
