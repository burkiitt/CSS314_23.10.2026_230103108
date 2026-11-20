
import os
import platform
import hashlib
import subprocess

import numpy as np
from mpi4py import MPI
from numba import cuda


def get_cpu_signature():
    """
    Get CPU information for deterministic identification.
    """

    cpu = platform.processor()

    if not cpu and os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo", "r") as file:
            for line in file:
                if line.lower().startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break

    return cpu or platform.machine()


def get_gpu_uuid():
    """
    Retrieve UUID of NVIDIA GPU 0 using nvidia-smi.
    """

    result = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=uuid",
            "--format=csv,noheader"
        ],
        text=True
    )

    gpu_uuids = result.strip().splitlines()

    if not gpu_uuids:
        raise RuntimeError("No NVIDIA GPU UUID found")

    return gpu_uuids[0].strip()


def generate_instance_seed(github_username, cpu_signature, gpu_uuid):
    """
    Generate deterministic 64-bit seed using SHA-256.
    """

    identity = (
        f"{github_username}|"
        f"{cpu_signature}|"
        f"{gpu_uuid}"
    )

    digest = hashlib.sha256(identity.encode("utf-8")).digest()

    seed = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False
    )

    return seed


def init_hybrid_context():

    # --------------------------------------------------
    # 1. Initialize MPI
    # --------------------------------------------------

    comm = MPI.COMM_WORLD

    rank = comm.Get_rank()
    size = comm.Get_size()

    assert size == 4, (
        f"Expected exactly 4 MPI processes, got {size}"
    )

    # --------------------------------------------------
    # 2. Create 2 x 2 Cartesian communicator
    # --------------------------------------------------

    cart_comm = comm.Create_cart(
        dims=(2, 2),
        periods=(False, False),
        reorder=False
    )

    coords = cart_comm.Get_coords(rank)

    # Dimension 0: rows
    up, down = cart_comm.Shift(0, 1)

    # Dimension 1: columns
    left, right = cart_comm.Shift(1, 1)

    neighbors = {
        "up": up,
        "down": down,
        "left": left,
        "right": right
    }

    # --------------------------------------------------
    # 3. Select GPU 0
    # --------------------------------------------------

    if not cuda.is_available():
        raise RuntimeError(
            f"CUDA is not available for MPI rank {rank}"
        )

    cuda.select_device(0)

    # --------------------------------------------------
    # 4. Create node-local shared-memory communicator
    # --------------------------------------------------

    node_comm = comm.Split_type(
        MPI.COMM_TYPE_SHARED,
        key=rank
    )

    node_rank = node_comm.Get_rank()
    node_size = node_comm.Get_size()

    assert node_size == 4, (
        "All four MPI processes must run on the same node"
    )

    # --------------------------------------------------
    # 5. Allocate MPI-3 shared memory
    # --------------------------------------------------

    # 64 uint64 values = 512 bytes.
    # Extra 63 bytes guarantee room for 64-byte alignment.

    shared_bytes = 64 * np.dtype(np.uint64).itemsize

    allocation_size = (
        shared_bytes + 63 if node_rank == 0 else 0
    )

    win = MPI.Win.Allocate_shared(
        allocation_size,
        disp_unit=1,
        comm=node_comm
    )

    # Every rank accesses the segment allocated by node rank 0.
    buf, itemsize = win.Shared_query(0)

    # Create a byte-level view of the shared memory.
    raw = np.ndarray(
        shape=(shared_bytes + 63,),
        dtype=np.uint8,
        buffer=buf
    )

    # Calculate offset to the next 64-byte boundary.
    offset = (-raw.ctypes.data) % 64

    # Create 64 aligned uint64 slots.
    shm_view = np.ndarray(
        shape=(64,),
        dtype=np.uint64,
        buffer=buf,
        offset=offset
    )

    # Verify alignment.
    assert shm_view.ctypes.data % 64 == 0

    # Initialize shared memory once.
    if node_rank == 0:
        shm_view[:] = 0

    win.Sync()
    node_comm.Barrier()
    win.Sync()

    # --------------------------------------------------
    # 6. Generate deterministic INSTANCE_SEED
    # --------------------------------------------------

    github_username = os.environ.get("GITHUB_USERNAME")

    if not github_username:
        raise RuntimeError(
            "Set the GITHUB_USERNAME environment variable"
        )

    cpu_signature = get_cpu_signature()
    gpu_uuid = get_gpu_uuid()

    INSTANCE_SEED = generate_instance_seed(
        github_username,
        cpu_signature,
        gpu_uuid
    )

    # --------------------------------------------------
    # 7. Print initialization information
    # --------------------------------------------------

    print(
        f"\nMPI Rank: {rank}\n"
        f"Cartesian coordinates: {coords}\n"
        f"Neighbors: {neighbors}\n"
        f"Node rank: {node_rank}\n"
        f"Node size: {node_size}\n"
        f"GPU: 0\n"
        f"Shared memory address: {hex(shm_view.ctypes.data)}\n"
        f"Shared memory alignment: "
        f"{shm_view.ctypes.data % 64}\n"
        f"INSTANCE_SEED: {INSTANCE_SEED}\n"
    )

    return {
        "comm": comm,
        "cart_comm": cart_comm,
        "node_comm": node_comm,
        "win": win,
        "shm_view": shm_view,
        "rank": rank,
        "size": size,
        "coords": coords,
        "neighbors": neighbors,
        "node_rank": node_rank,
        "node_size": node_size,
        "INSTANCE_SEED": INSTANCE_SEED
    }


def main():

    context = init_hybrid_context()

    comm = context["comm"]
    rank = context["rank"]

    print(f"Rank {rank}: Hybrid context initialized successfully")

    # Wait until all processes finish initialization.
    comm.Barrier()

    # Release MPI resources.
    context["win"].Free()
    context["node_comm"].Free()
    context["cart_comm"].Free()


if __name__ == "__main__":
    main()
