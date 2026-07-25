"""Build privacy-conscious Nigeria organized-violence exposure summaries.

The public map receives half-degree cells for 2016-2025, not UCDP's underlying
village-level events, actor names, narratives, or source text. State/year
aggregates retain the full 1989-2025 annual series for analytical profiles.
"""

import argparse
import math
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "06_security" / "ucdp_ged_26_1_global.zip"
PROCESSED_DIR = ROOT / "data" / "processed" / "06_security"
STATES_PATH = ROOT / "data" / "final" / "nigeria_adm1_simplified.geojson"
GRID_OUTPUT = "ucdp_organized_violence_grid_nigeria_2016_2025.csv"
STATE_YEAR_OUTPUT = "ucdp_organized_violence_state_year_nigeria_1989_2025.csv"
WINDOW_START = 2016
WINDOW_END = 2025
TYPE_LABELS = {
    1: "state_based",
    2: "non_state",
    3: "one_sided",
}
USE_COLUMNS = [
    "id",
    "year",
    "type_of_violence",
    "where_prec",
    "latitude",
    "longitude",
    "country",
    "best",
    "high",
    "low",
]


def load_nigeria_events(path: Path) -> pd.DataFrame:
    chunks = []
    for chunk in pd.read_csv(
        path,
        compression="zip",
        usecols=USE_COLUMNS,
        chunksize=100_000,
        low_memory=False,
    ):
        nigeria = chunk[chunk["country"].eq("Nigeria")].copy()
        if not nigeria.empty:
            chunks.append(nigeria)
    if not chunks:
        raise ValueError("No Nigeria records found in the UCDP archive")
    frame = pd.concat(chunks, ignore_index=True)
    for column in ["year", "type_of_violence", "where_prec", "latitude", "longitude", "best", "high", "low"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame[
        frame["latitude"].between(3.5, 14.5)
        & frame["longitude"].between(2.5, 15.0)
        & frame["year"].between(1989, 2025)
    ].copy()
    frame["violence_type"] = (
        frame["type_of_violence"].map(TYPE_LABELS).fillna("other")
    )
    return frame


def assign_states(frame: pd.DataFrame) -> pd.DataFrame:
    states = gpd.read_file(STATES_PATH)[["name", "geometry"]].to_crs("EPSG:4326")
    points = gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["longitude"], frame["latitude"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(points, states, how="left", predicate="within")
    joined = joined.rename(columns={"name": "state"})
    joined["state"] = joined["state"].fillna("Unassigned / offshore")
    return pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))


def aggregate_state_year(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["state", "year"], as_index=False).agg(
        event_count=("id", "count"),
        fatalities_best=("best", "sum"),
        fatalities_low=("low", "sum"),
        fatalities_high=("high", "sum"),
        state_based_events=("violence_type", lambda values: (values == "state_based").sum()),
        non_state_events=("violence_type", lambda values: (values == "non_state").sum()),
        one_sided_events=("violence_type", lambda values: (values == "one_sided").sum()),
    )
    national = frame.groupby("year", as_index=False).agg(
        event_count=("id", "count"),
        fatalities_best=("best", "sum"),
        fatalities_low=("low", "sum"),
        fatalities_high=("high", "sum"),
        state_based_events=("violence_type", lambda values: (values == "state_based").sum()),
        non_state_events=("violence_type", lambda values: (values == "non_state").sum()),
        one_sided_events=("violence_type", lambda values: (values == "one_sided").sum()),
    )
    national.insert(0, "state", "Nigeria")
    output = pd.concat([grouped, national], ignore_index=True)
    numeric_columns = [
        column for column in output.columns if column not in {"state", "year"}
    ]
    output[numeric_columns] = output[numeric_columns].fillna(0).astype(int)
    return output.sort_values(["state", "year"]).reset_index(drop=True)


def aggregate_grid(frame: pd.DataFrame) -> pd.DataFrame:
    recent = frame[frame["year"].between(WINDOW_START, WINDOW_END)].copy()
    recent["grid_lon"] = (
        recent["longitude"].map(lambda value: math.floor(value * 2) / 2 + 0.25)
    )
    recent["grid_lat"] = (
        recent["latitude"].map(lambda value: math.floor(value * 2) / 2 + 0.25)
    )
    grouped = recent.groupby(["grid_lat", "grid_lon"], as_index=False).agg(
        event_count=("id", "count"),
        fatalities_best=("best", "sum"),
        fatalities_low=("low", "sum"),
        fatalities_high=("high", "sum"),
        first_year=("year", "min"),
        latest_year=("year", "max"),
        state_based_events=("violence_type", lambda values: (values == "state_based").sum()),
        non_state_events=("violence_type", lambda values: (values == "non_state").sum()),
        one_sided_events=("violence_type", lambda values: (values == "one_sided").sum()),
        source_states=("state", lambda values: "; ".join(sorted(set(values)))),
        best_source_precision=("where_prec", "min"),
        least_source_precision=("where_prec", "max"),
    )
    grouped.insert(
        0,
        "cell_id",
        grouped.apply(
            lambda row: f"ucdp-05deg-{row.grid_lat:.2f}-{row.grid_lon:.2f}",
            axis=1,
        ),
    )
    grouped.insert(1, "period", f"{WINDOW_START}-{WINDOW_END}")
    numeric_columns = [
        "event_count",
        "fatalities_best",
        "fatalities_low",
        "fatalities_high",
        "first_year",
        "latest_year",
        "state_based_events",
        "non_state_events",
        "one_sided_events",
        "best_source_precision",
        "least_source_precision",
    ]
    grouped[numeric_columns] = grouped[numeric_columns].fillna(0).astype(int)
    return grouped.sort_values(["grid_lat", "grid_lon"]).reset_index(drop=True)


def process(input_path: Path, output_dir: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Missing {input_path}; run scripts/06_security/01_download_ucdp_ged.py"
        )
    frame = assign_states(load_nigeria_events(input_path))
    grid = aggregate_grid(frame)
    state_year = aggregate_state_year(frame)
    output_dir.mkdir(parents=True, exist_ok=True)
    grid.to_csv(output_dir / GRID_OUTPUT, index=False)
    state_year.to_csv(output_dir / STATE_YEAR_OUTPUT, index=False)
    print(
        f"Saved {len(grid):,} half-degree exposure cells and "
        f"{len(state_year):,} state/year rows from {len(frame):,} Nigeria events"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()
    try:
        process(args.input, args.output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
