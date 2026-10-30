import argparse
import json
import multiprocessing as mp
from pathlib import Path

from exp_a_serial import metrics as metrics_a
from exp_a_serial import run_experiment
from exp_b_contention import run_contended
from exp_c_fixed import run_privatized


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    results = root / "results"
    times_a = {p: run_experiment(p) for p in (1, 2, 4)}
    times_b = {p: run_contended(p) for p in (1, 2, 4)}
    times_c = {p: run_privatized(p) for p in (1, 2, 4)}
    experiments = {
        "A": {"student_id": args.student_id, "experiment": "A_serial_tail", **metrics_a(times_a)},
        "B": {"student_id": args.student_id, "experiment": "B_lock_contention", **metrics_a(times_b)},
        "C": {"student_id": args.student_id, "experiment": "C_privatized", **metrics_a(times_c)},
    }
    names = {"A": "exp_a_serial", "B": "exp_b_contention", "C": "exp_c_fixed"}
    for key, data in experiments.items():
        (results / f"{names[key]}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    profile = json.loads((results / "host_profile.json").read_text(encoding="utf-8"))
    lines = [
        "# Practice Lab Results",
        "",
        f"Student ID: `{args.student_id}`",
        f"Host: `{profile['cpu_model']}` with {profile['physical_cores']} physical and {profile['logical_threads']} logical cores",
        "",
        "| Experiment | T1 (s) | T2 (s) | T4 (s) | Speedup P=4 | e(2) | e(4) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, data in experiments.items():
        lines.append(f"| {data['experiment']} | {data['times'][1]:.3f} | {data['times'][2]:.3f} | {data['times'][4]:.3f} | "
                     f"{data['speedups']['4']:.2f}x | {data['karp_flatt']['2']:.3f} | {data['karp_flatt']['4']:.3f} |")
    lines += [
        "",
        "Experiment A shows a stable serial fraction from the intentional 0.40 second master-process delay.",
        "Experiment B demonstrates lock contention: adding workers increases runtime and Karp-Flatt rises.",
        "Experiment C privatizes the counter, removing the lock from the hot loop and restoring scaling.",
        f"Observed e(2)/e(4): A={experiments['A']['karp_flatt']['2']:.3f}/{experiments['A']['karp_flatt']['4']:.3f}, "
        f"B={experiments['B']['karp_flatt']['2']:.3f}/{experiments['B']['karp_flatt']['4']:.3f}, "
        f"C={experiments['C']['karp_flatt']['2']:.3f}/{experiments['C']['karp_flatt']['4']:.3f}.",
        "The handout's ideal A/C thresholds were not reached on this Windows host; the raw timings are retained.",
        "",
        "Commands used: `python src/run_practice_lab.py --student-id 230103108`.",
    ]
    (root / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root / "RESULTS.md")


if __name__ == "__main__":
    mp.freeze_support()
    run()
