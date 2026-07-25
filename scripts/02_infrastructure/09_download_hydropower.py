"""
Downloads the field-level Global Hydropower Tracker (GHT) dataset served by
GreenInfo Network's public map viewer (built for Global Energy Monitor),
following the same mirror pattern already used for GGIT/GOIT/GOGPT in this
layer.

Source: https://greeninfo-network.github.io/global-hydropower-tracker/
License: CC-BY 4.0 (inferred; same GEM data policy as the other GreenInfo
mirrors already used in this atlas).
Coverage: hydroelectric plants worldwide; this atlas keeps only Nigeria.

This closes a real gap: the existing power_plants layer (GOGPT) only covers
oil- and gas-fired generation by design -- it never included Nigeria's major
hydro stations (Kainji, Jebba, Shiroro, Zungeru, etc.).
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "02_infrastructure"
DATA_URL = "https://greeninfo-network.github.io/global-hydropower-tracker/static/data/data.csv"


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    print(f"Saved -> {dest_path}")
    return dest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the Global Hydropower Tracker dataset.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "ght_hydropower_all_countries.csv"

    try:
        download_file(DATA_URL, dest_path, force=args.force)
    except requests.RequestException as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
