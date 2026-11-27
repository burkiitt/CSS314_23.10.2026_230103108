# SECTION 0: LOCAL OPENMP ENVIRONMENT & DETERMINISTIC SEED HARNESS
import os
os.environ["NUMBA_THREADING_LAYER"] = "omp"  # Force native OpenMP runtime (libgomp / iomp)

import time, hashlib, json
import numpy as np
import numba as nb
from numba import njit, prange, set_num_threads, get_num_threads, get_thread_id

STUDENT_NAME = "Seidaly Burkit"  # <-- Enter your full name
STUDENT_ID = 230103108  # <-- Enter your numeric Student ID

assert isinstance(STUDENT_ID, int) and STUDENT_ID > 0, "Set a valid numeric STUDENT_ID!"
assert (os.cpu_count() or 1) >= 4, "Local multi-core CPU (>=4 logical cores) required; no Colab!"

# Trigger OpenMP layer initialization and verify backend
@njit(parallel=True)
def _omp_probe():
	acc = 0
	for i in prange(64):
		acc += get_thread_id() + 1
	return acc

_ = _omp_probe()
assert nb.threading_layer() == "omp", f"Expected 'omp' layer, got {nb.threading_layer()}"

rng = np.random.default_rng(STUDENT_ID)

# Student-specific OpenMP parameters
N_T1 = 4_000_000 + (STUDENT_ID % 991) * 1024
BINS_T1 = 48 + (STUDENT_ID % 17)
ITERS_T2 = 35_000_000 + (STUDENT_ID % 503) * 10_000
PAD_STRIDE = 8 + (STUDENT_ID % 5) * 8  # >= 8 int64 slots (>= 64 bytes cache-line isolation)
ROWS_T3 = 12_000 + (STUDENT_ID % 257) * 16
SKEW_MOD = 37 + (STUDENT_ID % 19)
GRID_H = 384 + (STUDENT_ID % 4) * 32
GRID_W = 512 + (STUDENT_ID % 5) * 32
OMEGA_SOR = np.float64(1.72 + (STUDENT_ID % 11) * 0.015)

data_t1 = rng.integers(0, BINS_T1, size=N_T1, dtype=np.int32)
weights_t1 = rng.uniform(0.25, 2.50, size=N_T1).astype(np.float64)

print(f"Backend: {nb.threading_layer()} | Logical Cores: {os.cpu_count()} | Student: {STUDENT_ID}")
