"""Validate the machine-readable redistribution gate for a Zenodo release."""

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTER = ROOT / "docs" / "redistribution_rights_register.csv"
REQUIRED_COLUMNS = {
    "source_id",
    "source_family",
    "repository_scope",
    "rights_status",
    "license_or_terms",
    "evidence_url",
    "clearance_requirement",
}
ALLOWED_STATUSES = {"cleared", "unresolved"}


def load_register(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Rights register is missing columns: " + ", ".join(sorted(missing))
            )
        rows = list(reader)
    if not rows:
        raise ValueError("Rights register contains no source families")
    source_ids = [row["source_id"].strip() for row in rows]
    if any(not source_id for source_id in source_ids):
        raise ValueError("Every rights row requires a source_id")
    duplicates = sorted(
        source_id for source_id in set(source_ids) if source_ids.count(source_id) > 1
    )
    if duplicates:
        raise ValueError("Duplicate source_id values: " + ", ".join(duplicates))
    invalid = sorted(
        {
            row["rights_status"].strip()
            for row in rows
            if row["rights_status"].strip() not in ALLOWED_STATUSES
        }
    )
    if invalid:
        raise ValueError("Invalid rights_status values: " + ", ".join(invalid))
    for row in rows:
        for column in REQUIRED_COLUMNS:
            if not row[column].strip():
                raise ValueError(
                    f"{row['source_id'] or '<unknown>'} has an empty {column}"
                )
    return rows


def readiness_report(rows: list[dict[str, str]]) -> dict[str, object]:
    unresolved = [
        {
            "source_id": row["source_id"],
            "source_family": row["source_family"],
            "clearance_requirement": row["clearance_requirement"],
        }
        for row in rows
        if row["rights_status"] != "cleared"
    ]
    return {
        "ready": not unresolved,
        "source_family_count": len(rows),
        "cleared_count": len(rows) - len(unresolved),
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = readiness_report(load_register(args.register))
    except (OSError, ValueError) as exc:
        print(f"Zenodo readiness register error: {exc}")
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    elif report["ready"]:
        print(
            "Zenodo rights gate passed: "
            f"{report['cleared_count']} source families cleared."
        )
    else:
        print(
            "Zenodo rights gate BLOCKED: "
            f"{report['unresolved_count']} of "
            f"{report['source_family_count']} source families unresolved."
        )
        for item in report["unresolved"]:
            print(f"- {item['source_id']}: {item['clearance_requirement']}")
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
