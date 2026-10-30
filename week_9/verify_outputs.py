import csv
import hashlib
import json
from pathlib import Path

from src.salt import get_student_params


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def rows(name):
    with (RESULTS / name).open(encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def main():
    salted = json.loads((RESULTS / "salted_params.json").read_text(encoding="utf-8"))
    assert salted == get_student_params(salted["student_id"])
    assert json.loads((RESULTS / "host_profile.json").read_text(encoding="utf-8"))
    print("[PASS] Milestone 0: Host topology and salted parameters validated.")

    dense = json.loads((RESULTS / "loop_interchange.json").read_text(encoding="utf-8"))
    assert dense["max_abs_error"] <= 1e-12
    stride = rows("stride_results.tsv")
    assert [int(row["stride"]) for row in stride] == [1, 2, 4, 8, 16, 32, 64, 128]
    print("[PASS] Milestone 1: Locality data and matrix result validated.")

    sharing = rows("false_sharing_karp_flatt.tsv")
    for row in sharing:
        assert int(row["total_count"]) == int(row["processes"]) * int(row["iterations"])
    print("[PASS] Milestone 2: Counter totals and Karp-Flatt data validated.")

    scaling = rows("scaling_metrics.tsv")
    for row in scaling:
        assert abs(float(row["checksum"]) - float(row["expected_checksum"])) < 1e-6
    assert json.loads((RESULTS / "roofline_summary.json").read_text(encoding="utf-8"))
    print("[PASS] Milestone 3: Scaling checksums and roofline data validated.")

    digest = hashlib.sha256()
    digest.update(salted["student_id"].encode())
    for name in ("host_profile.json", "salted_params.json", "stride_results.tsv",
                 "loop_interchange.json", "false_sharing_karp_flatt.tsv",
                 "scaling_metrics.tsv", "roofline_summary.json"):
        digest.update(name.encode())
        digest.update((RESULTS / name).read_bytes())
    receipt = RESULTS / "verification_receipt.sig"
    receipt.write_text(digest.hexdigest() + "\n", encoding="utf-8")
    print("[PASS] Milestone 4: SHA-256 receipt written.")


if __name__ == "__main__":
    main()
