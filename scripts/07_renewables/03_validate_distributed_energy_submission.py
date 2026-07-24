#!/usr/bin/env python3
"""Validate a proposed distributed-energy contribution CSV."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
STATES_PATH = ROOT / "data" / "final" / "nigeria_adm1_simplified.geojson"

REQUIRED_COLUMNS = {
    "submission_id",
    "asset_name",
    "distributed_energy_class",
    "asset_type",
    "state",
    "lga",
    "community",
    "status",
    "technology",
    "capacity_kw",
    "customers_served",
    "latitude",
    "longitude",
    "geocode_precision",
    "developer",
    "owner_operator",
    "program_name",
    "source_name",
    "source_url",
    "source_publication_date",
    "source_date_accessed",
    "evidence_level",
    "verification_status",
    "submitter_name",
    "submitter_contact",
    "notes",
    "attestation",
}
REQUIRED_VALUES = {
    "submission_id",
    "asset_name",
    "distributed_energy_class",
    "state",
    "status",
    "technology",
    "latitude",
    "longitude",
    "geocode_precision",
    "source_name",
    "source_url",
    "source_date_accessed",
    "evidence_level",
    "verification_status",
    "attestation",
}
ALLOWED_CLASSES = {
    "community_mini_grid",
    "captive_institutional_off_grid",
    "standalone_system",
    "interconnected_mini_grid",
}
ALLOWED_STATUSES = {
    "operational",
    "commissioned",
    "under_construction",
    "under_rehabilitation",
    "proposed",
    "unknown",
}
ALLOWED_PRECISIONS = {
    "exact_site",
    "facility",
    "campus",
    "community",
    "lga",
    "state",
    "derived_centroid",
}
ALLOWED_EVIDENCE = {
    "official_operational",
    "official_commissioned",
    "official_current_status",
    "regulator_record",
    "operator_record",
    "institutional_record",
    "credible_secondary",
}
SUBMISSION_ID_PATTERN = re.compile(r"^contrib-[a-z0-9][a-z0-9-]*$")


def state_names() -> set[str]:
    payload = json.loads(STATES_PATH.read_text(encoding="utf-8"))
    return {
        feature["properties"].get("name")
        or feature["properties"].get("shapeName")
        for feature in payload["features"]
    }


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def numeric(
    row_number: int,
    row: dict[str, str],
    column: str,
    errors: list[str],
    *,
    minimum: float,
    maximum: float | None = None,
    integer: bool = False,
) -> None:
    value = row.get(column, "").strip()
    if not value:
        return
    try:
        parsed = int(value) if integer else float(value)
    except ValueError:
        errors.append(f"row {row_number}: {column} must be numeric")
        return
    if parsed < minimum or (maximum is not None and parsed > maximum):
        upper = f" and <= {maximum}" if maximum is not None else ""
        errors.append(
            f"row {row_number}: {column} must be >= {minimum}{upper}"
        )


def validate_submission(path: Path, *, allow_empty: bool = False) -> list[str]:
    errors: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - columns)
        unexpected_columns = sorted(columns - REQUIRED_COLUMNS)
        if missing_columns:
            errors.append(f"missing columns: {missing_columns}")
        if unexpected_columns:
            errors.append(f"unexpected columns: {unexpected_columns}")
        if errors:
            return errors
        rows = list(reader)

    if not rows:
        return [] if allow_empty else ["submission must contain at least one row"]

    known_states = state_names()
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        for column in sorted(REQUIRED_VALUES):
            if not row.get(column, "").strip():
                errors.append(f"row {row_number}: {column} is required")

        submission_id = row.get("submission_id", "").strip()
        if submission_id and not SUBMISSION_ID_PATTERN.fullmatch(submission_id):
            errors.append(
                f"row {row_number}: submission_id must match "
                "contrib-[a-z0-9-]+"
            )
        if submission_id in seen_ids:
            errors.append(f"row {row_number}: duplicate submission_id")
        seen_ids.add(submission_id)

        checks = [
            ("distributed_energy_class", ALLOWED_CLASSES),
            ("status", ALLOWED_STATUSES),
            ("geocode_precision", ALLOWED_PRECISIONS),
            ("evidence_level", ALLOWED_EVIDENCE),
        ]
        for column, allowed in checks:
            value = row.get(column, "").strip()
            if value and value not in allowed:
                errors.append(
                    f"row {row_number}: invalid {column} '{value}'"
                )

        if row.get("state", "").strip() not in known_states:
            errors.append(f"row {row_number}: state is not a canonical ADM1 name")
        if row.get("verification_status", "").strip() != "submitted":
            errors.append(
                f"row {row_number}: verification_status must be 'submitted'"
            )
        if row.get("attestation", "").strip().lower() != "true":
            errors.append(f"row {row_number}: attestation must be true")

        source_url = row.get("source_url", "").strip()
        if source_url and not valid_url(source_url):
            errors.append(f"row {row_number}: source_url must be HTTP(S)")
        for column in ["source_publication_date", "source_date_accessed"]:
            value = row.get(column, "").strip()
            if value and not valid_date(value):
                errors.append(
                    f"row {row_number}: {column} must use YYYY-MM-DD"
                )

        numeric(row_number, row, "latitude", errors, minimum=3.9, maximum=14.0)
        numeric(row_number, row, "longitude", errors, minimum=2.5, maximum=14.8)
        numeric(row_number, row, "capacity_kw", errors, minimum=0)
        numeric(
            row_number,
            row,
            "customers_served",
            errors,
            minimum=0,
            integer=True,
        )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Accept a header-only template.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_submission(args.submission.resolve(), allow_empty=args.allow_empty)
    if errors:
        print(f"Validation failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: {args.submission}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
