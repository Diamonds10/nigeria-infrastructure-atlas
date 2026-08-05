"""Download the annual UCDP Georeferenced Event Dataset release.

UCDP GED 26.1 covers 1989-2025 and is licensed CC BY 4.0. The raw global
archive is kept under data/raw (gitignored); the processor publishes only a
Nigeria subset aggregated in space and time.
"""

import argparse
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "06_security"
SOURCE_URL = "https://ucdp.uu.se/downloads/ged/ged261-csv.zip"
OUTPUT_NAME = "ucdp_ged_26_1_global.zip"


def download(output_path: Path, force: bool = False) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not force:
        print(f"Skipping existing file: {output_path}")
        return
    with requests.get(
        SOURCE_URL,
        timeout=180,
        stream=True,
        headers={"User-Agent": "Infraxis-Atlas-Nigeria/0.12"},
    ) as response:
        response.raise_for_status()
        with output_path.open("wb") as destination:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    destination.write(chunk)
    print(f"Saved UCDP GED 26.1 archive: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        download(args.output_dir / OUTPUT_NAME, args.force)
    except (OSError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
