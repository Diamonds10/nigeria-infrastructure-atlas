"""
Process the raw NOSDRA oil spill JSON into a cleaned CSV: decoded status,
cause, contaminant, facility-type, zonal-office, and state codes; numeric
quantity fields coerced from comma-formatted strings; coordinates parsed and
validated against Nigeria's extent.

This script expects that the raw JSON has already been downloaded into
`data/raw/03_environmental/` using
scripts/03_environmental/05_download_nosdra_spills.py.

Code legends below were read directly from the Nigerian Oil Spill Monitor's
own filter-picker UI (https://oilspillmonitor.ng, "Filter" > each field), not
guessed from the abbreviations. The site does not expose a metadata/legend
API endpoint, only the picker UI.
"""

import argparse
from datetime import date
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "03_environmental"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "03_environmental"
RAW_FILENAME = "nosdra_oil_spills.json"
OUTPUT_FILENAME = "nosdra_oil_spills_nigeria.csv"

NIGERIA_LAT_RANGE = (3.9, 14.0)
NIGERIA_LON_RANGE = (2.5, 14.8)

STATUS_LABELS = {
    "confirmed": "Confirmed", "invalid": "Invalid (mistakenly reported)",
    "new": "New report", "reviewed": "Reviewed (awaiting confirmation)",
    "inconclusive": "Inconclusive",  # present in data, not in the site's current picker
}
CONTAMINANT_LABELS = {
    "ch": "Chemicals / drilling mud", "co": "Condensate", "con": "Condensate",
    "cr": "Crude oil", "ga": "Gas", "gs": "Gas",  # "gs" is a legacy code, inferred (not in current picker)
    "no": "No spill", "re": "Refined products", "other:": "Other",
}
CAUSE_LABELS = {
    "cor": "Corrosion", "eqf": "Equipment failure", "ome": "Operational/maintenance error",
    "sab": "Sabotage/theft", "ytd": "Yet to be determined", "other:": "Other",
}
HABITAT_LABELS = {
    "co": "Coastland", "iw": "Inland waters", "la": "Land", "ns": "Near shore",
    "of": "Offshore", "ss": "Seasonal swamp", "sw": "Swamp", "other": "Other",
}
FACILITY_LABELS = {
    "cp": "Compressor plant", "fd": "Fuel dispensation station / retail outlet",
    "fl": "Flow line", "fp": "FPSO", "fs": "Flow station", "gl": "Gas line",
    "mf": "Manifold", "pl": "Pipeline", "ps": "Pumping station", "rg": "Rig",
    "st": "Storage tank", "tf": "Tank farm", "tk": "Tanker", "wh": "Well head",
}
ZONAL_OFFICE_LABELS = {
    "ab": "Abuja", "ak": "Akure", "by": "Bayelsa", "kd": "Kaduna",
    "lg": "Lagos", "ph": "Port Harcourt", "uy": "Uyo", "wa": "Warri",
}
STATE_LABELS = {
    "AB": "Abia", "AD": "Adamawa", "AK": "Akwa Ibom", "AN": "Anambra", "BA": "Bauchi",
    "BE": "Benue", "BO": "Borno", "BY": "Bayelsa", "CR": "Cross River", "DE": "Delta",
    "EB": "Ebonyi", "ED": "Edo", "EK": "Ekiti", "EN": "Enugu", "FC": "Abuja Federal Capital Territory",
    "GO": "Gombe", "IM": "Imo", "JI": "Jigawa", "KD": "Kaduna", "KE": "Kebbi", "KN": "Kano",
    "KO": "Kogi", "KT": "Katsina", "KW": "Kwara", "LA": "Lagos", "NA": "Nassarawa", "NI": "Niger",
    "OG": "Ogun", "ON": "Ondo", "OS": "Osun", "OY": "Oyo", "PL": "Plateau", "RI": "Rivers",
    "SO": "Sokoto", "TA": "Taraba", "YO": "Yobe", "ZA": "Zamfara",
}
# A few raw records spell the state out in full instead of using the 2-letter
# code (e.g. "KADUNA", "NIGER") -- map those directly rather than treating them
# as unrecognized.
STATE_FULLNAME_OVERRIDES = {v.upper(): v for v in STATE_LABELS.values()}
STATE_FULLNAME_OVERRIDES["FCT"] = "Abuja Federal Capital Territory"

KEEP_COLUMNS = [
    "id", "status", "status_label", "company", "incidentnumber", "incidentdate",
    "incident_year", "incident_date_quality", "reportdate",
    "cause", "cause_label", "is_sabotage_attributed", "contaminant", "contaminant_label",
    "estimatedquantity", "quantityrecovered", "typeoffacility", "facility_label",
    "spillareahabitat", "habitat_label", "sitelocationname", "lga", "statesaffected",
    "state_label", "zonaloffice", "zonaloffice_label", "latitude", "longitude",
    "descriptionofimpact", "spillstopdate", "jivdate", "certificatedate", "certificatenumber",
]

MIN_PLAUSIBLE_INCIDENT_YEAR = 1950


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/03_environmental/05_download_nosdra_spills.py first."
        )
    return path


def decode(series: pd.Series, labels: dict) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    mapped = normalized.map(labels)
    # Free-text entries like "other:Explosion" or "other: BLAST" don't exactly
    # match the "other:" key -- fall back to the generic "Other" label for any
    # unmapped value that starts with "other", rather than leaving it blank.
    other_fallback = normalized.str.startswith("other") & mapped.isna()
    mapped = mapped.mask(other_fallback, "Other")
    return mapped


def parse_coordinate(value) -> float:
    if value is None:
        return float("nan")
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return float("nan")


def clean_quantity(value) -> float:
    if value is None or value == "":
        return float("nan")
    text = str(value).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return float("nan")


def add_incident_date_quality(frame: pd.DataFrame) -> None:
    """Expose a safe filter year without rewriting NOSDRA's source date.

    The live feed currently contains one obvious 1902 outlier. Retaining the
    original text preserves provenance, while a separate quality flag prevents
    implausible dates from silently entering timelines and year filters.
    """
    parsed = pd.to_datetime(frame["incidentdate"], format="%Y-%m-%d", errors="coerce")
    plausible = (
        parsed.notna()
        & parsed.dt.year.between(MIN_PLAUSIBLE_INCIDENT_YEAR, date.today().year)
        & parsed.dt.date.le(date.today())
    )
    frame["incident_year"] = parsed.dt.year.where(plausible).astype("Int64")
    frame["incident_date_quality"] = "missing"
    frame.loc[parsed.notna() & ~plausible, "incident_date_quality"] = "implausible"
    frame.loc[plausible, "incident_date_quality"] = "source_reported"


def normalize_one_state(text: str) -> str | None:
    text = text.strip().upper()
    if text in STATE_LABELS:
        return STATE_LABELS[text]
    if text in STATE_FULLNAME_OVERRIDES:
        return STATE_FULLNAME_OVERRIDES[text]
    return None


def normalize_state(value) -> str | None:
    if not value or str(value).strip().lower() == "undefined":
        return None
    parts = [normalize_one_state(part) for part in str(value).split(",")]
    resolved = [p for p in parts if p]
    if not resolved:
        return None
    # dedupe while preserving order (source has e.g. "RI,RI")
    seen = []
    for p in resolved:
        if p not in seen:
            seen.append(p)
    return ", ".join(seen)


def process(input_path: Path, output_path: Path) -> None:
    import json
    records = json.loads(input_path.read_text(encoding="utf-8"))
    df = pd.DataFrame.from_records(records)

    df["status_label"] = decode(df["status"], STATUS_LABELS)
    df["cause_label"] = decode(df["cause"].fillna(""), CAUSE_LABELS)
    df["is_sabotage_attributed"] = df["cause"].astype(str).str.strip().str.lower() == "sab"
    df["contaminant_label"] = decode(df["contaminant"].fillna(""), CONTAMINANT_LABELS)
    df["facility_label"] = decode(df["typeoffacility"].fillna(""), FACILITY_LABELS)
    df["habitat_label"] = df["spillareahabitat"].fillna("").astype(str).str.strip().str.lower().map(
        lambda raw: ", ".join(HABITAT_LABELS.get(part, part) for part in raw.split(",")) if raw else None
    )
    df["zonaloffice_label"] = decode(df["zonaloffice"].fillna(""), ZONAL_OFFICE_LABELS)
    df["state_label"] = df["statesaffected"].apply(normalize_state)
    add_incident_date_quality(df)

    df["latitude"] = df["latitude"].apply(parse_coordinate)
    df["longitude"] = df["longitude"].apply(parse_coordinate)
    valid_coord = (
        df["latitude"].between(*NIGERIA_LAT_RANGE) & df["longitude"].between(*NIGERIA_LON_RANGE)
    )
    n_had_coords = df["latitude"].notna().sum()
    n_valid_coords = valid_coord.sum()
    df.loc[~valid_coord, ["latitude", "longitude"]] = float("nan")

    df["estimatedquantity"] = df["estimatedquantity"].apply(clean_quantity)
    df["quantityrecovered"] = df["quantityrecovered"].apply(clean_quantity)

    available_columns = [col for col in KEEP_COLUMNS if col in df.columns]
    df = df[available_columns]
    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].map(
            lambda value: "\n".join(
                line.rstrip() for line in value.splitlines()
            )
            if isinstance(value, str)
            else value
        )
    df = df.sort_values("incidentdate").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    n_sabotage = df["is_sabotage_attributed"].sum()
    n_implausible_dates = df["incident_date_quality"].eq("implausible").sum()
    print(
        f"Saved processed CSV: {output_path} ({len(df):,} rows)\n"
        f"  Coordinates: {n_had_coords:,} records had a raw lat/lon; "
        f"{n_valid_coords:,} parsed as valid decimal coordinates within Nigeria's extent "
        f"({n_had_coords - n_valid_coords:,} dropped as unparseable or out-of-range)\n"
        f"  Cause = sabotage/theft: {n_sabotage:,} of {len(df):,} records "
        f"({100 * n_sabotage / len(df):.1f}%)\n"
        f"  Incident dates: {df['incident_year'].notna().sum():,} plausible years; "
        f"{n_implausible_dates:,} implausible source date(s) excluded from timelines"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded NOSDRA oil spill JSON to a cleaned, decoded CSV."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
        process(input_path, processed_dir / OUTPUT_FILENAME)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
