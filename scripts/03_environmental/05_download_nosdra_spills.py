"""
Downloads Nigeria's official oil spill incident register from NOSDRA (National
Oil Spill Detection and Response Agency), served via the Nigerian Oil Spill
Monitor's public API (built by the same GreenInfo Network team behind several
other sources already in this atlas).

Source: https://oilspillmonitor.ng (dataset "nosdra")
API: https://oilspillmonitor.ng/api/spill-data.php?dataset=nosdra&format=json
License: Not stated on the site; confirm terms before redistributing.
Coverage: 21,000+ incident records, 2006-present, updated live (most recent
incident at time of writing was 2026-07-16) -- unlike most other sources in
this atlas, this is an actively maintained feed, not a static snapshot.

Only the "nosdra" dataset parameter is accessible; other guessed parameter
names (codes/legend/meta/definitions/lookup/reference) all return "You are
not allowed to access the requested dataset", so the code legends used in
scripts/03_environmental/06_process_nosdra_spills.py were read directly off
the site's own filter-picker UI (which renders "code: label" pairs for each
filterable field), not guessed or reverse-engineered from the raw codes.
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "03_environmental"
API_URL = "https://oilspillmonitor.ng/api/spill-data.php?dataset=nosdra&format=json"


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    response = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected response shape (expected a JSON list): {type(payload)}")

    import json
    dest_path.write_text(json.dumps(payload))
    print(f"Saved {len(payload):,} incident records -> {dest_path}")
    return dest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the NOSDRA oil spill dataset.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "nosdra_oil_spills.json"

    try:
        download_file(API_URL, dest_path, force=args.force)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
