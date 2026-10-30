from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def command(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=3, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def number(value: Any) -> int | float | None:
    try:
        result = float(str(value).strip())
        return int(result) if result.is_integer() else result
    except (TypeError, ValueError):
        return None


def bytes_from(value: Any) -> int | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*([\d.]+)\s*([KMGT]?B?)?\s*", str(value), re.I)
    if not match:
        return None
    units = {"B": 1, "K": 1024, "KB": 1024, "M": 1024**2, "MB": 1024**2,
             "G": 1024**3, "GB": 1024**3, "T": 1024**4, "TB": 1024**4}
    return int(float(match.group(1)) * units.get((match.group(2) or "B").upper(), 1))


def default_cache() -> dict[str, int | None]:
    return {"l1_data_bytes": None, "l2_bytes": None,
            "l3_shared_bytes": None, "line_size_bytes": 64}


def linux_cpu() -> dict[str, Any]:
    records = []
    current = {}
    try:
        lines = Path("/proc/cpuinfo").read_text(errors="replace").splitlines() + [""]
    except OSError:
        lines = []
    for line in lines:
        if not line.strip():
            if current:
                records.append(current)
                current = {}
        elif ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()

    first = records[0] if records else {}
    logical = len(records) or os.cpu_count()
    pairs = {(x.get("physical id"), x.get("core id")) for x in records
             if x.get("physical id") is not None and x.get("core id") is not None}
    physical = len(pairs) or number(first.get("cpu cores")) or logical
    base_hz = None
    base_file = Path("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
    if base_file.exists():
        base_hz = number(base_file.read_text().strip())
        base_hz = int(base_hz * 1000) if base_hz is not None else None
    if base_hz is None and number(first.get("cpu MHz")) is not None:
        base_hz = int(float(number(first["cpu MHz"])) * 1_000_000)

    cache = default_cache()
    for item in sorted(Path("/sys/devices/system/cpu/cpu0/cache").glob("index*")):
        try:
            level = item.joinpath("level").read_text().strip()
            kind = item.joinpath("type").read_text().strip().lower()
            size = bytes_from(item.joinpath("size").read_text())
            line_size = number(item.joinpath("coherency_line_size").read_text())
        except OSError:
            continue
        cache["line_size_bytes"] = line_size or cache["line_size_bytes"]
        if level == "1" and kind == "data":
            cache["l1_data_bytes"] = size
        elif level == "2":
            cache["l2_bytes"] = size
        elif level == "3":
            cache["l3_shared_bytes"] = size
    return {"model_name": first.get("model name") or first.get("Hardware") or platform.processor() or "unknown",
            "base_frequency_hz": base_hz, "physical_cores": physical,
            "logical_threads": logical, "cache": cache}


def mac_cpu() -> dict[str, Any]:
    def sysctl(name: str) -> str | None:
        return command(["sysctl", "-n", name])

    frequency = number(sysctl("hw.cpufrequency"))
    if frequency is None and number(sysctl("hw.cpufrequency_max")) is not None:
        frequency = int(float(number(sysctl("hw.cpufrequency_max"))) * 1_000_000)
    cache = {"l1_data_bytes": bytes_from(sysctl("hw.l1dcachesize")),
             "l2_bytes": bytes_from(sysctl("hw.l2cachesize")),
             "l3_shared_bytes": bytes_from(sysctl("hw.l3cachesize")),
             "line_size_bytes": number(sysctl("hw.cachelinesize")) or 64}
    return {"model_name": sysctl("machdep.cpu.brand_string") or platform.processor() or "unknown",
            "base_frequency_hz": frequency, "physical_cores": number(sysctl("hw.physicalcpu")),
            "logical_threads": number(sysctl("hw.logicalcpu")) or os.cpu_count(), "cache": cache}


def windows_cache() -> dict[str, int | None]:
    cache = default_cache()
    try:
        from ctypes import wintypes
        function = ctypes.WinDLL("kernel32", use_last_error=True).GetLogicalProcessorInformationEx
        function.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
        function.restype = wintypes.BOOL
        size = wintypes.DWORD(0)
        function(2, None, ctypes.byref(size))
        buffer = (ctypes.c_ubyte * size.value)()
        if not size.value or not function(2, buffer, ctypes.byref(size)):
            return cache
        raw = bytes(buffer[:size.value])
    except (AttributeError, OSError, TypeError):
        return cache

    offset = 0
    while offset + 16 <= len(raw):
        _, record_size = struct.unpack_from("<II", raw, offset)
        if record_size < 16 or offset + record_size > len(raw):
            break
        level, _, line_size, size, kind = struct.unpack_from("<BBHIB", raw, offset + 8)
        cache["line_size_bytes"] = line_size or cache["line_size_bytes"]
        if level == 1 and kind == 2:
            cache["l1_data_bytes"] = max(cache["l1_data_bytes"] or 0, size)
        elif level == 2 and kind == 0:
            cache["l2_bytes"] = max(cache["l2_bytes"] or 0, size)
        elif level == 3 and kind == 0:
            cache["l3_shared_bytes"] = max(cache["l3_shared_bytes"] or 0, size)
        offset += record_size
    return cache


def other_cpu() -> dict[str, Any]:
    return {"model_name": platform.processor() or "unknown", "base_frequency_hz": None,
            "physical_cores": None, "logical_threads": os.cpu_count(), "cache": default_cache()}


def cpu_profile() -> dict[str, Any]:
    system = platform.system()
    if system == "Linux":
        cpu = linux_cpu()
    elif system == "Darwin":
        cpu = mac_cpu()
    elif system == "Windows":
        cpu = other_cpu()
        cpu["cache"] = windows_cache()
    else:
        cpu = other_cpu()

    if psutil is not None:
        cpu["physical_cores"] = cpu["physical_cores"] or psutil.cpu_count(logical=False)
        cpu["logical_threads"] = cpu["logical_threads"] or psutil.cpu_count(logical=True)
        if not cpu["base_frequency_hz"]:
            frequency = psutil.cpu_freq()
            if frequency and frequency.max:
                cpu["base_frequency_hz"] = int(frequency.max * 1_000_000)

    model = cpu["model_name"].lower()
    if "apple" in model:
        microarchitecture = "Apple Silicon"
    elif "intel" in model or "xeon" in model:
        microarchitecture = "Intel x86-64"
    elif "amd" in model or "ryzen" in model or "epyc" in model:
        microarchitecture = "AMD x86-64"
    else:
        microarchitecture = platform.machine() or "unknown"
    cpu["microarchitecture"] = microarchitecture
    cpu["base_frequency_mhz"] = (round(cpu["base_frequency_hz"] / 1_000_000, 2)
                                  if cpu["base_frequency_hz"] else None)
    cpu["smt_enabled"] = bool(cpu["logical_threads"] and cpu["physical_cores"] and
                               cpu["logical_threads"] > cpu["physical_cores"])
    return cpu


def profile() -> dict[str, Any]:
    system = platform.system()
    cpu = cpu_profile()
    operating_system = {"system": system, "release": platform.release(),
                        "version": platform.version(),
                        "kernel_version": platform.version() if system == "Windows" else platform.release(),
                        "machine": platform.machine()}
    python = {"implementation": platform.python_implementation(),
              "version": platform.python_version(), "version_full": sys.version,
              "executable": sys.executable, "architecture": platform.architecture()[0]}
    return {"profiled_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cpu": cpu, "cache": cpu["cache"], "os": operating_system, "python": python,
            "cpu_model": cpu["model_name"], "microarchitecture": cpu["microarchitecture"],
            "base_frequency_hz": cpu["base_frequency_hz"],
            "base_frequency_mhz": cpu["base_frequency_mhz"],
            "physical_cores": cpu["physical_cores"], "logical_threads": cpu["logical_threads"],
            "smt_enabled": cpu["smt_enabled"], "kernel_version": operating_system["kernel_version"],
            "cache_line_bytes": cpu["cache"]["line_size_bytes"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "host_profile.json").write_text(json.dumps(profile(), indent=2) + "\n", encoding="utf-8")
    try:
        from salt import get_student_params
    except ImportError:
        from .salt import get_student_params
    (RESULTS / "salted_params.json").write_text(
        json.dumps(get_student_params(args.student_id), indent=2) + "\n", encoding="utf-8")
    print("Wrote results/host_profile.json")
    print("Wrote results/salted_params.json")


if __name__ == "__main__":
    main()
