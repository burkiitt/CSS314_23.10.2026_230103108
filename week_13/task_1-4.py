# SECTION 0: LOCAL OPENMP ENVIRONMENT & DETERMINISTIC SEED HARNESS
import os
os.environ["NUMBA_THREADING_LAYER"] = "omp"
import time, hashlib, json
import numpy as np
import numba as nb
from numba import njit, prange, set_num_threads, get_num_threads, get_thread_id

STUDENT_NAME = "Seidaly Burkit"
STUDENT_ID = 230103108
assert isinstance(STUDENT_ID, int) and STUDENT_ID > 0
assert (os.cpu_count() or 1) >= 4, "Local workstation with at least 4 logical cores required"

@njit(parallel=True)
def _omp_probe():
	acc = 0
	for i in prange(64):
		acc += get_thread_id() + 1
	return acc

_ = _omp_probe()
assert nb.threading_layer() == "omp", f"Expected omp backend, got {nb.threading_layer()}"
rng = np.random.default_rng(STUDENT_ID)
N_T1 = 4_000_000 + (STUDENT_ID % 991) * 1024
BINS_T1 = 48 + (STUDENT_ID % 17)
ITERS_T2 = 35_000_000 + (STUDENT_ID % 503) * 10_000
PAD_STRIDE = 8 + (STUDENT_ID % 5) * 8
ROWS_T3 = 12_000 + (STUDENT_ID % 257) * 16
SKEW_MOD = 37 + (STUDENT_ID % 19)
GRID_H = 384 + (STUDENT_ID % 4) * 32
GRID_W = 512 + (STUDENT_ID % 5) * 32
OMEGA_SOR = np.float64(1.72 + (STUDENT_ID % 11) * 0.015)
data_t1 = rng.integers(0, BINS_T1, size=N_T1, dtype=np.int32)
weights_t1 = rng.uniform(0.25, 2.50, size=N_T1).astype(np.float64)
print(f"Backend: {nb.threading_layer()} | Logical cores: {os.cpu_count()} | Student: {STUDENT_ID}")

# ============================================================================== 
# TASK 1: RACE-CONDITION FORENSICS & THREAD-PRIVATE HISTOGRAM REDUCTION
# ==============================================================================

# TASK 1 STARTER: UNSAFE CONCURRENT ACCUMULATION
@njit(parallel=True)
def buggy_hist_omp(indices, weights, num_bins):
	hist = np.zeros(num_bins, dtype=np.int64)
	w_sums = np.zeros(num_bins, dtype=np.float64)
	for i in prange(indices.shape[0]):
		b = indices[i]
		hist[b] += 1  # Data race across OpenMP threads
		w_sums[b] += weights[i]  # Non-associative floating-point race
	return hist, w_sums


# PART 2: DETERMINISTIC THREAD-PRIVATE KERNEL
@njit(parallel=True)
def safe_hist_omp(indices, weights, num_bins):
	max_threads = get_num_threads()
	priv_hist = np.zeros((max_threads, num_bins), dtype=np.int64)
	priv_w_sums = np.zeros((max_threads, num_bins), dtype=np.float64)
	worker_hits = np.zeros(max_threads, dtype=np.int64)

	for i in prange(indices.shape[0]):
		tid = get_thread_id()
		b = indices[i]
		priv_hist[tid, b] += 1
		priv_w_sums[tid, b] += weights[i]
		worker_hits[tid] += 1

	# Deterministic row-wise reduction across 0 .. max_threads - 1
	hist = np.zeros(num_bins, dtype=np.int64)
	w_sums = np.zeros(num_bins, dtype=np.float64)
	for t in range(max_threads):
		for b in range(num_bins):
			hist[b] += priv_hist[t, b]
			w_sums[b] += priv_w_sums[t, b]

	return hist, w_sums, worker_hits


# PART 1: EMPIRICAL RACE DEMONSTRATION
print("\n--- TASK 1: RACE-CONDITION FORENSICS ---")
set_num_threads(1)
ref_hist, ref_w_sums = buggy_hist_omp(data_t1, weights_t1, BINS_T1)

target_8t = 8 if (os.cpu_count() or 1) >= 8 else os.cpu_count()
set_num_threads(target_8t)
_ = buggy_hist_omp(data_t1[:1000], weights_t1[:1000], BINS_T1)  # Warm-up

for run_idx in range(1, 11):
	b_hist, b_w_sums = buggy_hist_omp(data_t1, weights_t1, BINS_T1)
	lost_counts = N_T1 - int(np.sum(b_hist))
	max_bin_diff = int(np.max(np.abs(ref_hist - b_hist)))
	max_w_diff = float(np.max(np.abs(ref_w_sums - b_w_sums)))
	print(
		f"Run {run_idx:02d} ({target_8t}T) | Lost Counts: {lost_counts:,} | "
		f"Max Bin Discrepancy: {max_bin_diff:,} | Max Weight Diff: {max_w_diff:.6f}"
	)


# VERIFY SAFE KERNEL ACROSS 1, 2, 4, AND 8 THREADS
print("\n--- TASK 1: SAFE THREAD-PRIVATE SCALING & VERIFICATION ---")
thread_counts = [t for t in (1, 2, 4, 8) if t <= (os.cpu_count() or 1)]
base_safe_hist = None
base_safe_wsums = None

for tc in thread_counts:
	set_num_threads(tc)
	_ = safe_hist_omp(data_t1[:1000], weights_t1[:1000], BINS_T1)  # Warm-up
	t0 = time.perf_counter()
	s_hist, s_wsums, w_hits = safe_hist_omp(data_t1, weights_t1, BINS_T1)
	elapsed = time.perf_counter() - t0

	assert int(np.sum(s_hist)) == N_T1, f"Count mismatch at {tc} threads!"
	assert int(np.sum(w_hits)) == N_T1, f"Worker hits mismatch at {tc} threads!"
	active_workers = int(np.count_nonzero(w_hits))
	assert active_workers == tc, f"Expected {tc} active workers, saw {active_workers}!"

	if base_safe_hist is None:
		base_safe_hist = s_hist
		base_safe_wsums = s_wsums
	else:
		assert np.array_equal(s_hist, base_safe_hist), f"Integer histogram mismatch at {tc} threads!"
		assert np.allclose(s_wsums, base_safe_wsums, rtol=1e-13, atol=1e-11), f"Float sum drift at {tc} threads!"

	print(f"Threads: {tc} | Time: {elapsed:.4f}s | Active Workers: {active_workers} | Worker Hits: {w_hits.tolist()}")

# Store final 8-thread (or max-thread) results for Final Verification Bundle
hist_t1 = s_hist
wsums_t1 = s_wsums


# PART 3: DIGITAL DIAGNOSIS STRING (4-6 SENTENCES)
DIAGNOSIS_T1 = (
	"Even if integer bin increments were protected by atomic hardware instructions, floating-point addition "
	"remains inherently non-associative under IEEE-754 arithmetic because every addition rounds the intermediate "
	"result to a fixed 53-bit mantissa. When multiple OpenMP threads accumulate weights concurrently into shared "
	"bins, non-deterministic OS thread scheduling alters the exact sequence in which large and small numbers are "
	"added together. Adding a tiny weight to a large running sum causes low-order mantissa bits to be truncated "
	"differently than if several small weights were summed together first before being added to the total. "
	"Consequently, two executions with atomic floating-point updates can follow different rounding paths and "
	"produce slightly different bit-level results across runs."
)

# ============================================================================== 
# TASKS 2–4 AND FINAL BUNDLE
# ============================================================================== 
@njit(parallel=True)
def unpadded_state_omp(iters, seed_val):
	n = get_num_threads(); state = np.zeros(n, np.int64)
	for t in prange(n):
		tid = get_thread_id(); x = np.int64(seed_val + tid * 1315423911)
		for _ in range(iters):
			x = (x * np.int64(6364136223846793005) + np.int64(1442695040888963407)) & np.int64(0x7FFFFFFFFFFFFFFF)
			state[tid] ^= x >> 17
	return state

@njit(parallel=True)
def padded_state_omp(iters, seed_val, stride):
	n = get_num_threads(); state = np.zeros((n, stride), np.int64)
	for t in prange(n):
		tid = get_thread_id(); x = np.int64(seed_val + tid * 1315423911)
		for _ in range(iters):
			x = (x * np.int64(6364136223846793005) + np.int64(1442695040888963407)) & np.int64(0x7FFFFFFFFFFFFFFF)
			state[tid, 0] ^= x >> 17
	return state

print("\n--- TASK 2: FALSE SHARING ---")
t2_times = {}; state_t2 = None
for tc in thread_counts:
	set_num_threads(tc); unpadded_state_omp(1, STUDENT_ID); padded_state_omp(1, STUDENT_ID, PAD_STRIDE)
	t0=time.perf_counter(); a=unpadded_state_omp(ITERS_T2, STUDENT_ID); ta=time.perf_counter()-t0
	t0=time.perf_counter(); b=padded_state_omp(ITERS_T2, STUDENT_ID, PAD_STRIDE)[:,0]; tb=time.perf_counter()-t0
	assert np.array_equal(a,b); t2_times[tc]=(ta,tb)
	if tc == target_8t: state_t2=b
	print(f"{tc} threads: unpadded {ta:.3f}s, padded {tb:.3f}s")
print(f"8-thread padding speedup: {t2_times[target_8t][0]/t2_times[target_8t][1]:.3f}x")
DIAGNOSIS_T2 = ("Each worker repeatedly writes a distinct int64 value, but adjacent values share a 64-byte cache line. "
"MESI requires exclusive ownership for a write and invalidates other cores' copies, so workers repeatedly transfer line ownership. "
"This false sharing creates coherence traffic despite the absence of a logical data race. "
"Padding separates active slots by at least one cache line and reduces those invalidations. "
"The arithmetic and per-worker update sequence remain unchanged, so padded and unpadded state values must match exactly.")

@njit(parallel=True)
def _row_score(r, sid, mod):
	n = 40 + ((r * 7919 + sid) % mod) ** 2; v=0.0
	for k in range(n):
		x=r*0.001+k*0.0001+1.0
		v += np.sin(x)*np.cos(x)+np.sqrt(abs(x)+1.0)
	return v,n

@njit(parallel=True)
def static_skew_omp(rows,sid,mod,stride):
	out=np.empty(rows); ops=np.zeros((get_num_threads(),stride),np.int64)
	for r in prange(rows):
		t=get_thread_id(); out[r],n=_row_score(r,sid,mod); ops[t,0]+=n
	return out,ops[:,0].copy()

@njit(parallel=True)
def balanced_skew_omp(rows,sid,mod,stride):
	step=rows//2+1
	while np.gcd(step,rows)!=1: step+=1
	out=np.empty(rows); ops=np.zeros((get_num_threads(),stride),np.int64)
	for j in prange(rows):
		t=get_thread_id(); r=(j*step)%rows; out[r],n=_row_score(r,sid,mod); ops[t,0]+=n
	return out,ops[:,0].copy()

print("\n--- TASK 3: WORK SKEW ---")
set_num_threads(target_8t); static_skew_omp(32,STUDENT_ID,SKEW_MOD,PAD_STRIDE)
t0=time.perf_counter(); out_static,ops_static=static_skew_omp(ROWS_T3,STUDENT_ID,SKEW_MOD,PAD_STRIDE); static_time=time.perf_counter()-t0
t0=time.perf_counter(); out_balanced,ops_balanced=balanced_skew_omp(ROWS_T3,STUDENT_ID,SKEW_MOD,PAD_STRIDE); balanced_time=time.perf_counter()-t0
ratio_static=float(ops_static.max()/ops_static[ops_static>0].min()); ratio_balanced=float(ops_balanced.max()/ops_balanced[ops_balanced>0].min())
assert np.max(np.abs(out_static-out_balanced)) < 1e-11
assert ratio_balanced < 1.15, f"Interleaved scheduling imbalance {ratio_balanced:.3f}"
print(f"Static {static_time:.3f}s / {ratio_static:.3f}x; interleaved {balanced_time:.3f}s / {ratio_balanced:.3f}x")
out_t3=out_balanced
DIAGNOSIS_T3=("Static contiguous row blocks can leave a worker with many expensive rows because trip counts vary quadratically. "
"The balanced version permutes rows using a coprime modular stride before the parallel loop. "
"This interleaves high and low cost rows throughout the statically assigned iteration ranges. "
"Per-thread padded counters measure actual inner-loop operations without introducing a counter race. "
"The reported operation ratio verifies whether the permutation reduced workload skew on this run.")

@njit(parallel=True)
def sor_red_black_step(u,omega,stride):
	h,w=u.shape; n=get_num_threads(); maxima=np.zeros((2,n,stride))
	for color in range(2):
		for r in prange(1,h-1):
			t=get_thread_id(); m=0.0
			for c in range(1,w-1):
				if (r+c)%2==color:
					old=u[r,c]; new=(1.0-omega)*old+0.25*omega*(u[r-1,c]+u[r+1,c]+u[r,c-1]+u[r,c+1]); u[r,c]=new
					d=abs(new-old)
					if d>m: m=d
			maxima[color,t,0]=m
	best=0.0
	for color in range(2):
		for t in range(n):
			if maxima[color,t,0]>best: best=maxima[color,t,0]
	return best

@njit(parallel=True)
def solve_pde_omp(u,omega,iterations,stride):
	for _ in range(iterations): sor_red_black_step(u,omega,stride)
	return u

def make_grid():
	u=np.zeros((GRID_H,GRID_W)); u[0,:]=100.; u[-1,:]=-50.
	u[:,0]=25.*np.sin(np.linspace(0.,np.pi,GRID_H)); u[:,-1]=75.*np.cos(np.linspace(0.,np.pi/2.,GRID_H))
	return u

print("\n--- TASK 4: RED-BLACK SOR ---")
set_num_threads(1); grid_reference=solve_pde_omp(make_grid(),OMEGA_SOR,600,PAD_STRIDE)
t4_times={}; grid_t4=None
for tc in thread_counts:
	set_num_threads(tc); solve_pde_omp(make_grid(),OMEGA_SOR,1,PAD_STRIDE)
	g=make_grid(); t0=time.perf_counter(); g=solve_pde_omp(g,OMEGA_SOR,600,PAD_STRIDE); elapsed=time.perf_counter()-t0
	diff=float(np.max(np.abs(g-grid_reference))); assert diff<1e-9, f"SOR mismatch {tc} threads: {diff}"
	t4_times[tc]=elapsed
	if tc==target_8t: grid_t4=g
	print(f"{tc} threads: {elapsed:.3f}s, max difference {diff:.3e}")
print("SOR speedups: "+", ".join(f"{tc}T={t4_times[1]/t4_times[tc]:.3f}x" for tc in thread_counts))

set_num_threads(target_8t)
for idx,diag in enumerate([DIAGNOSIS_T1,DIAGNOSIS_T2,DIAGNOSIS_T3],1): assert isinstance(diag,str) and len(diag.strip())>=80, f"Complete DIAGNOSIS_T{idx}!"
checksum_blob=(f"{STUDENT_ID}|{int(np.sum(hist_t1))}|{float(np.sum(wsums_t1)):.4f}|{int(np.bitwise_xor.reduce(state_t2))}|{float(np.sum(out_t3)):.6f}|{float(np.sum(grid_t4)):.6f}")
lab_digest=hashlib.sha256(checksum_blob.encode()).hexdigest()[:20].upper()
bundle={"instructor":"Instructor - Sufyan bin Uzayr","student_name":STUDENT_NAME,"student_id":STUDENT_ID,"omp_layer":nb.threading_layer(),"cpu_cores":os.cpu_count(),"verification_digest":lab_digest}
print("=== OPENMP PYTHON LAB VERIFICATION BUNDLE ===")
print(json.dumps(bundle,indent=2))
