#!/usr/bin/env python3
"""Build the deterministic GeoJSON bundle used by the GitHub Pages atlas.

The public web map is deliberately a screening product. To keep the bundle
responsive it includes motorway and trunk roads, while the analysis-ready CSV
retains all four processed major-road classes.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from shapely import from_wkt
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEFAULT_STATES = ROOT / "data" / "final" / "nigeria_adm1_simplified.geojson"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "atlas_data.json"
DEFAULT_API_DIR = ROOT / "docs" / "api" / "v1"
PUBLIC_SIMPLIFY_TOLERANCE = 0.005
PUBLIC_COORDINATE_PRECISION = 5
PUBLIC_PROPERTY_PRECISION = 6
ATLAS_PRODUCT_NAME = "Infraxis Atlas — Nigeria"
ATLAS_MASTER_BRAND = "Infraxis Atlas"
ATLAS_PREMIUM_BRAND = "Infraxis"
ATLAS_COUNTRY = "Nigeria"
ATLAS_FORMER_NAME = "Nigeria Infrastructure Atlas"
ATLAS_TAGLINE = "Mapping infrastructure. Measuring disruption."
ATLAS_PRODUCT_ROLE = "open_datasource"
ATLAS_PRODUCT_RELATIONSHIP = (
    "This open atlas is the public datasource and screening layer; "
    "Infraxis is the separate premium analytical layer built on top of it."
)
ATLAS_RELEASE_VERSION = "0.12.0"
ATLAS_RELEASE_DATE = "2026-08-05"
ATLAS_RELEASE_TITLE = "Infraxis Atlas Rebrand and Pan-African Foundation"
REPOSITORY_RAW = "https://raw.githubusercontent.com/Diamonds10/infraxis-atlas-nigeria/main"
DISTRIBUTED_ENERGY_SUBLAYERS = {
    "community_minigrids",
    "captive_offgrid_systems",
    "standalone_systems",
    "interconnected_minigrids",
}
MONTHLY_REFRESH_LAYERS = {"oil_spills"}
QUARTERLY_REFRESH_LAYERS = {
    "roads",
    "railways",
    "rail_stations",
    "power_grid",
    "substations",
    "community_minigrids",
    "captive_offgrid_systems",
    "standalone_systems",
    "interconnected_minigrids",
}


def refresh_policy(sublayer_key: str, source_date: str) -> dict[str, Any]:
    """Return deterministic, machine-readable review expectations."""
    checked = date.fromisoformat(source_date)
    if sublayer_key in MONTHLY_REFRESH_LAYERS:
        cadence = "monthly"
        next_review = checked + timedelta(days=31)
    elif sublayer_key in QUARTERLY_REFRESH_LAYERS:
        cadence = "quarterly"
        next_review = checked + timedelta(days=92)
    else:
        cadence = "annual_or_source_release"
        next_review = checked + timedelta(days=366)
    release_day = date.fromisoformat(ATLAS_RELEASE_DATE)
    return {
        "cadence": cadence,
        "last_checked": source_date,
        "next_review_due": next_review.isoformat(),
        "review_status": "due" if next_review <= release_day else "current",
    }

CATALOGUE = {
    "fields_oil": {
        "description": "Site-level Nigerian fields classified oil-only by the GOGET source, with status, operator, and ownership context.",
        "source": "Global Energy Monitor / GreenInfo Network GOGET mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "33 of 180 GOGET field points are source-classified oil-only. GOGET's fuel_type is not an authoritative reservoir classification: known gas-producing sites including Soku, Bonny, and Gbaran are labelled oil. Use this layer as source-classified screening evidence.",
        "path": "data/processed/01_resource/goget_fields_nigeria_2023-08.csv",
    },
    "fields_gas": {
        "description": "Site-level Nigerian gas-producing fields classified gas-only or oil-and-gas by GOGET, with status, operator, and ownership context.",
        "source": "Global Energy Monitor / GreenInfo Network GOGET mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "147 of 180 GOGET field points are source-classified gas-only (2) or oil-and-gas (145). This non-overlapping display group replaces the misleading gas-only count. GOGET's fuel_type still omits some known gas-producing sites that it labels oil; use the SE4ALL field boundaries and source caveat alongside this layer.",
        "path": "data/processed/01_resource/goget_fields_nigeria_2023-08.csv",
    },
    "field_polygons_gas": {
        "description": "Gas-only field boundary polygons, including field names not present in the GOGET point inventory above.",
        "source": "Nigeria SE4ALL Open Data Portal",
        "source_date": "2026-07-24",
        "license": "Public portal; explicit redistribution terms not stated",
        "quality": "B",
        "quality_note": "62 of 124 SE4ALL polygons are classified Gas_Field. Adds real field footprints and field names not covered by GOGET.",
        "path": "data/processed/01_resource/se4all_gas_fields_nigeria_2026-07.csv",
    },
    "field_polygons_mixed": {
        "description": "Oil-and-gas field boundary polygons, including field names not present in the GOGET point inventory above.",
        "source": "Nigeria SE4ALL Open Data Portal",
        "source_date": "2026-07-24",
        "license": "Public portal; explicit redistribution terms not stated",
        "quality": "B",
        "quality_note": "60 of 124 SE4ALL polygons are classified Crude Oil and Gas Field; 2 more have no field_type recorded and are folded in here rather than treated as pure gas or oil. 8 of 124 total polygons carry no field name in the source.",
        "path": "data/processed/01_resource/se4all_gas_fields_nigeria_2026-07.csv",
    },
    "gas_pipelines": {
        "description": "Gas transmission pipeline routes that include Nigeria.",
        "source": "Global Energy Monitor / GreenInfo Network GGIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Public route geometry; cross-border projects may extend beyond Nigeria.",
        "path": "data/processed/02_infrastructure/ggit_gas_pipelines_nigeria.csv",
    },
    "oil_pipelines": {
        "description": "Oil and NGL transmission pipeline routes that include Nigeria.",
        "source": "Global Energy Monitor / GreenInfo Network GOIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Public route geometry; storage terminals are not included.",
        "path": "data/processed/02_infrastructure/goit_oil_ngl_pipelines_nigeria.csv",
    },
    "lng_terminals": {
        "description": "Nigerian LNG terminal train records with capacity and status context.",
        "source": "Global Energy Monitor / GreenInfo Network GGIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Site points with train-level records; multiple records may share a facility.",
        "path": "data/processed/02_infrastructure/ggit_lng_terminals_nigeria.csv",
    },
    "power_plants": {
        "description": "Oil- and gas-fired generating units across Nigerian power stations.",
        "source": "Global Energy Monitor / GreenInfo Network GOGPT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Unit-level records; counts are not unique power-station counts.",
        "path": "data/processed/02_infrastructure/gogpt_oil_gas_plants_nigeria.csv",
    },
    "hydro_plants": {
        "description": "Nigerian hydroelectric power stations, operating and planned, with capacity and status.",
        "source": "Global Energy Monitor / GreenInfo Network Global Hydropower Tracker mirror",
        "source_date": "2026-07-26",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "7 Nigerian hydro plants, all at GEM-reported 'exact' coordinate accuracy: 4 operating (Kainji, Jebba, Shiroro, Zungeru; ~2,638 MW combined), 1 pre-construction (Gurara II), 2 shelved (Makurdi, and the long-delayed Mambilla mega-project). This closes a real gap -- the power_plants layer above (GOGPT) covers only oil- and gas-fired generation by design and never included hydro.",
        "path": "data/processed/02_infrastructure/ght_hydropower_nigeria.csv",
    },
    "refineries": {
        "description": "Major Nigerian refinery sites with nameplate capacity and public status context.",
        "source": "Atlas compilation from public reporting",
        "source_date": "2026-07-21",
        "license": "Derived compilation; review underlying sources",
        "quality": "C",
        "quality_note": "Major refineries only; some coordinates are approximate and modular refineries are incomplete.",
        "path": "data/processed/02_infrastructure/refineries_nigeria.csv",
    },
    "gas_infrastructure": {
        "description": "Upstream and midstream oil/gas point infrastructure: compressor stations, gas plants, flow stations, and FPSOs (floating production, storage & offloading vessels).",
        "source": "Nigeria SE4ALL Open Data Portal",
        "source_date": "2026-07-24",
        "license": "Public portal; explicit redistribution terms not stated",
        "quality": "C",
        "quality_note": "Status, operator, and capacity fields are inconsistently populated. Records matching a facility already tracked in refineries or LNG terminals above are excluded here to avoid double-counting.",
        "path": "data/processed/02_infrastructure/se4all_gas_infrastructure_nigeria_2026-07.csv",
    },
    "oil_spills": {
        "description": "Oil spill incidents reported to NOSDRA (National Oil Spill Detection and Response Agency), with cause, contaminant, facility type, and operator.",
        "source": "NOSDRA, via the Nigerian Oil Spill Monitor public API",
        "source_date": "2026-07-25",
        "license": "Not stated on the site; confirm terms before redistributing",
        "quality": "B",
        "quality_note": "21,124 reported incidents in the extracted feed; 16,326 (77.3%) have valid coordinates within Nigeria and are published on the map/API. Report status is preserved, including invalid and inconclusive records, and can be filtered explicitly. One implausible 1902 source date is retained for provenance but excluded from timelines. 66.8% of records with a coded cause are attributed to sabotage/theft. This is a reported-incident screening layer, not an independently verified spill registry. Explicit redistribution terms are not stated by the source.",
        "path": "data/processed/03_environmental/nosdra_oil_spills_nigeria.csv",
    },
    "protected_areas": {
        "description": "Protected and conserved areas including forest reserves, parks, and wetlands.",
        "source": "UNEP-WCMC / IUCN Protected Planet",
        "source_date": "2026-07-22",
        "license": "Source-specific terms; non-commercial restrictions apply",
        "quality": "A",
        "quality_note": "Authoritative source geometry, simplified only for web display.",
        "path": "data/processed/03_environmental/wdpa_protected_areas_nigeria.csv",
    },
    "conflict_exposure": {
        "description": "Half-degree historical exposure cells derived from UCDP organized-violence events; exact event locations, actors, narratives, and source text are not republished.",
        "source": "UCDP Georeferenced Event Dataset (GED) version 26.1",
        "source_date": "2026-03-30",
        "source_checked": "2026-07-25",
        "license": "CC BY 4.0",
        "quality": "B",
        "quality_note": "Aggregates 2016-2025 events into approximately 55 km cells. Fatalities are UCDP low/best/high estimates, not independently verified atlas findings. Annual release only; no candidate or live feed.",
        "path": "data/processed/06_security/ucdp_organized_violence_grid_nigeria_2016_2025.csv",
        "state_year_path": "data/processed/06_security/ucdp_organized_violence_state_year_nigeria_1989_2025.csv",
    },
    "demand_centers": {
        "description": "Cross-category industrial demand centres covering cement, steel, fertiliser, and refining.",
        "source": "Atlas compilation reconciled against GEM and OpenStreetMap",
        "source_date": "2026-07-21",
        "license": "Derived compilation; OSM-derived elements are ODbL",
        "quality": "C",
        "quality_note": "Most sites were independently checked; eight locations remain less precisely verified.",
        "path": "data/processed/04_demand/demand_centers_nigeria.csv",
    },
    "roads": {
        "description": "Motorway and trunk road segments used in the public web map.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Web subset only; the processed CSV also includes primary and secondary roads.",
        "path": "data/processed/05_connectivity/osm_roads_major_nigeria.csv",
    },
    "railways": {
        "description": "Mapped Nigerian railway line segments.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Geometry reflects OSM mapping, not confirmed operational service.",
        "path": "data/processed/05_connectivity/osm_railways_nigeria.csv",
    },
    "rail_stations": {
        "description": "Mapped Nigerian railway stations.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Locations reflect OSM coverage and may include inactive stations.",
        "path": "data/processed/05_connectivity/osm_railways_nigeria.csv",
    },
    "power_grid": {
        "description": "Mapped electricity transmission and minor-line segments.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Useful for geometry screening; voltage attributes are incomplete.",
        "path": "data/processed/05_connectivity/osm_power_grid_nigeria.csv",
    },
    "substations": {
        "description": "Mapped electricity substations represented as display points.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Footprints are converted to centroids in the web bundle; electrical specifications are incomplete.",
        "path": "data/processed/05_connectivity/osm_power_grid_nigeria.csv",
    },
    "ports": {
        "description": "Nigerian seaports and offshore oil and gas terminals.",
        "source": "NGA World Port Index via HDX",
        "source_date": "2026-07-23",
        "license": "US government public data",
        "quality": "B",
        "quality_note": "Locations are stable, but facility attributes come from a 2017 source file.",
        "path": "data/processed/05_connectivity/world_port_index_nigeria.csv",
    },
    "community_minigrids": {
        "description": "Community-serving mini-grids with a local generation system and distribution network.",
        "source": "Nigeria SE4ALL Open Data Portal; REA/NEP/DARES; ECREEE; NEMSA; institutional sources",
        "source_date": "2026-07-25",
        "license": "Mixed public-source terms; review each record and source",
        "quality": "B",
        "quality_note": "81 records from the SE4ALL asset inventory, official supplements, and the SE4ALL community survey. Survey points represent community evidence, not verified plant footprints.",
        "path": "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "coverage_audit_path": "data/processed/07_renewables/minigrid_state_coverage_audit.csv",
        "supplement_path": "data/curated/07_renewables/verified_public_offgrid_supplement.csv",
    },
    "captive_offgrid_systems": {
        "description": "Captive and institutional off-grid systems serving a defined campus, hospital, department, or facility.",
        "source": "REA/NEP/DARES; ECREEE; institutional sources",
        "source_date": "2026-07-25",
        "license": "Mixed public-source terms; review each record and source",
        "quality": "B",
        "quality_note": "10 records classified from captive_off_grid, public_institution_off_grid, and facility-specific off_grid_solar asset types. These are not community mini-grids.",
        "path": "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "coverage_audit_path": "data/processed/07_renewables/minigrid_state_coverage_audit.csv",
        "supplement_path": "data/curated/07_renewables/verified_public_offgrid_supplement.csv",
    },
    "standalone_systems": {
        "description": "Standalone household, shop, facility, or solar-home systems without a local distribution network.",
        "source": "Public-source distributed-energy evidence",
        "source_date": "2026-07-25",
        "license": "Mixed public-source terms; review each record and source",
        "quality": "C",
        "quality_note": "No household-level point is published. State profiles instead carry official programme aggregates and named strong-coverage evidence without exposing beneficiary locations or inventing point precision.",
        "path": "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "coverage_audit_path": "data/processed/07_renewables/minigrid_state_coverage_audit.csv",
        "supplement_path": "data/curated/07_renewables/verified_public_offgrid_supplement.csv",
        "programme_evidence_path": "data/processed/07_renewables/standalone_solar_programme_evidence.csv",
    },
    "interconnected_minigrids": {
        "description": "Mini-grids designed to operate with, or interconnect to, an existing distribution network.",
        "source": "REA/NEP; NEMSA; official programme sources",
        "source_date": "2026-07-25",
        "license": "Mixed public-source terms; review each record and source",
        "quality": "B",
        "quality_note": "2 official-source interconnected mini-grid records. This is a conservative named-site inventory, not a complete national registry.",
        "path": "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "coverage_audit_path": "data/processed/07_renewables/minigrid_state_coverage_audit.csv",
        "supplement_path": "data/curated/07_renewables/verified_public_offgrid_supplement.csv",
    },
    "population_access": {
        "description": "Quarter-degree settlement-population grid with night-light and grid-distance screening signals.",
        "source": "World Bank Nigeria Distributed Renewable Energy Atlas",
        "source_date": "2025-06-12",
        "source_checked": "2026-07-24",
        "license": "CC BY 4.0",
        "quality": "B",
        "quality_note": "Aggregated from 154,319 settlement clusters. Night-light detection is a screening proxy, not a measured household electricity-access rate.",
        "path": "data/processed/08_context/population_access_grid_nigeria.csv",
    },
    "settlements": {
        "description": "Major settlement clusters, retaining the 40 highest-population source records per state for a responsive web map.",
        "source": "World Bank Nigeria Distributed Renewable Energy Atlas",
        "source_date": "2025-06-12",
        "source_checked": "2026-07-24",
        "license": "CC BY 4.0",
        "quality": "B",
        "quality_note": "Web subset of a 154,319-cluster processed inventory. Population and access fields are modelled screening estimates.",
        "path": "data/processed/08_context/major_settlements_nigeria.csv",
    },
}


def clean_value(value: Any) -> Any:
    """Convert pandas/numpy scalar values into strict JSON-compatible values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, float):
        return round(value, PUBLIC_PROPERTY_PRECISION)
    return value


def properties(row: pd.Series, columns: Iterable[str], label_column: str) -> dict[str, Any]:
    result = {}
    for column in columns:
        value = clean_value(row.get(column))
        if value is not None and value != "":
            result[column] = value
    result["_label"] = clean_value(row.get(label_column))
    return result


def feature(geometry: Any, props: dict[str, Any]) -> dict[str, Any]:
    geometry = geometry.simplify(PUBLIC_SIMPLIFY_TOLERANCE, preserve_topology=True)
    geojson_geometry = mapping(geometry)
    geojson_geometry["coordinates"] = round_coordinates(geojson_geometry["coordinates"])
    return {
        "type": "Feature",
        "properties": props,
        "geometry": geojson_geometry,
    }


def round_coordinates(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [round_coordinates(item) for item in value]
    return round(float(value), PUBLIC_COORDINATE_PRECISION)


def point_features(
    path: Path,
    longitude: str,
    latitude: str,
    columns: list[str],
    label_column: str,
    *,
    where: tuple[str, set[str]] | None = None,
) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    if where:
        column, allowed = where
        frame = frame[frame[column].isin(allowed)]
    frame = frame.dropna(subset=[longitude, latitude])
    return [
        feature(
            Point(float(row[longitude]), float(row[latitude])),
            properties(row, columns, label_column),
        )
        for _, row in frame.iterrows()
    ]


def wkt_features(
    path: Path,
    geometry_column: str,
    columns: list[str],
    label_column: str,
    *,
    where: tuple[str, set[str]] | None = None,
    exclude_notna: str | None = None,
    centroid: bool = False,
) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    if where:
        column, allowed = where
        frame = frame[frame[column].isin(allowed)]
    if exclude_notna:
        frame = frame[frame[exclude_notna].isna()]
    frame = frame.dropna(subset=[geometry_column])
    output = []
    for _, row in frame.iterrows():
        geometry = from_wkt(row[geometry_column])
        if geometry.geom_type == "MultiPoint" and len(geometry.geoms) == 1:
            geometry = geometry.geoms[0]
        if centroid and geometry.geom_type != "Point":
            geometry = geometry.centroid
        output.append(feature(geometry, properties(row, columns, label_column)))
    return output


def route_features(
    path: Path,
    columns: list[str],
    label_column: str,
) -> list[dict[str, Any]]:
    """Parse GEM routes encoded as colon-separated ``lat,lng`` pairs."""
    frame = pd.read_csv(path).dropna(subset=["route"])
    output = []
    for _, row in frame.iterrows():
        lines = []
        for encoded_line in str(row["route"]).split(";"):
            coordinates = []
            for pair in encoded_line.split(":"):
                latitude, longitude = pair.split(",", maxsplit=1)
                coordinates.append((float(longitude), float(latitude)))
            if len(coordinates) >= 2:
                lines.append(coordinates)
        if lines:
            geometry = LineString(lines[0]) if len(lines) == 1 else MultiLineString(lines)
            output.append(
                feature(
                    geometry,
                    properties(row, columns, label_column),
                )
            )
    return output


def sublayer(label: str, geometry_type: str, features: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "label": label,
        "geomType": geometry_type,
        "data": {"type": "FeatureCollection", "features": features},
    }


def status_bucket(props: dict[str, Any]) -> str:
    raw = str(props.get("status") or props.get("STATUS") or "").lower()
    if not raw:
        return "unknown"
    if any(value in raw for value in ("operat", "active", "in use", "commissioned")):
        return "operating"
    if any(value in raw for value in ("construction", "development", "pre-production", "rehabilitation")):
        return "development"
    if any(value in raw for value in ("proposed", "planned", "announced", "discovered")):
        return "proposed"
    if any(value in raw for value in ("mothballed", "cancelled", "shelved", "shut in", "retired", "down")):
        return "inactive"
    return "other"


def feature_year(sublayer_key: str, props: dict[str, Any]) -> tuple[int | None, str | None]:
    if sublayer_key in {"population_access", "settlements"}:
        return 2025, "Source release year"
    candidates = {
        "fields_oil": ("discovery_year", "Discovery year"),
        "fields_gas": ("discovery_year", "Discovery year"),
        "gas_pipelines": ("start_year", "Start year"),
        "oil_pipelines": ("start_year", "Start year"),
        "lng_terminals": ("start_year", "Start year"),
        "power_plants": ("start_year", "Start year"),
        "hydro_plants": ("start_year", "Start year"),
        "refineries": ("commissioned_year", "Commissioned year"),
        "oil_spills": ("incident_year", "Reported incident year"),
        "protected_areas": ("STATUS_YR", "Designation/status year"),
    }
    candidate = candidates.get(sublayer_key)
    if not candidate:
        return None, None
    field, label = candidate
    value = props.get(field)
    try:
        year = int(float(value))
    except (TypeError, ValueError):
        return None, None
    if year < 1800 or year > 2026:
        return None, None
    return year, label


def empty_profile(name: str, sublayer_keys: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "mapped_records": 0,
        "counts": {key: 0 for key in sublayer_keys},
        "category_counts": {
            "resource": 0,
            "infrastructure": 0,
            "environmental": 0,
            "security": 0,
            "demand": 0,
            "connectivity": 0,
            "renewables": 0,
            "context": 0,
        },
        "capacity": {
            "power_mw": 0.0,
            "refinery_bpd": 0.0,
            "minigrid_kw": 0.0,
        },
        "oil_spill_intelligence": {
            "mapped_reports": 0,
            "confirmed_reports": 0,
            "invalid_reports": 0,
            "sabotage_attributed_reports": 0,
            "estimated_quantity_reported": 0.0,
            "report_status_counts": {},
            "cause_counts": {},
            "yearly_counts": {},
        },
        "security_intelligence": {
            "period": "2016-2025",
            "event_count": 0,
            "fatalities_best": 0,
            "fatalities_low": 0,
            "fatalities_high": 0,
            "state_based_events": 0,
            "non_state_events": 0,
            "one_sided_events": 0,
            "yearly_counts": {},
        },
        "status": {
            "operating": 0,
            "development": 0,
            "proposed": 0,
            "inactive": 0,
            "other": 0,
            "unknown": 0,
        },
    }


def update_profile(
    profile: dict[str, Any],
    category_key: str,
    sublayer_key: str,
    props: dict[str, Any],
) -> None:
    profile["mapped_records"] += 1
    profile["counts"][sublayer_key] += 1
    profile["category_counts"][category_key] += 1
    profile["status"][status_bucket(props)] += 1

    if sublayer_key == "oil_spills":
        spill = profile["oil_spill_intelligence"]
        spill["mapped_reports"] += 1
        report_status = str(props.get("status_label") or "").lower()
        if report_status == "confirmed":
            spill["confirmed_reports"] += 1
        if report_status.startswith("invalid"):
            spill["invalid_reports"] += 1
        if props.get("is_sabotage_attributed") in {True, "Yes"}:
            spill["sabotage_attributed_reports"] += 1
        spill["estimated_quantity_reported"] += float(
            props.get("estimatedquantity") or 0
        )
        for output_key, property_key in [
            ("report_status_counts", "status_label"),
            ("cause_counts", "cause_label"),
        ]:
            value = props.get(property_key)
            if value:
                spill[output_key][str(value)] = (
                    spill[output_key].get(str(value), 0) + 1
                )
        incident_year = props.get("incident_year")
        if incident_year:
            year = str(int(incident_year))
            spill["yearly_counts"][year] = (
                spill["yearly_counts"].get(year, 0) + 1
            )

    if sublayer_key in ("power_plants", "hydro_plants"):
        profile["capacity"]["power_mw"] += float(props.get("capacity") or 0)
    elif sublayer_key == "refineries":
        profile["capacity"]["refinery_bpd"] += float(props.get("capacity_bpd") or 0)
    elif sublayer_key in DISTRIBUTED_ENERGY_SUBLAYERS:
        profile["capacity"]["minigrid_kw"] += float(props.get("capacity_kw") or 0)


def add_catalogue_and_state_profiles(
    bundle: dict[str, Any],
) -> None:
    """Add machine-readable catalogue metadata and state-level screening summaries."""
    sublayer_keys = [
        sublayer_key
        for layer in bundle["layers"].values()
        for sublayer_key in layer["sublayers"]
    ]
    state_geometries = []
    for state_feature in bundle["states"]["features"]:
        state_name = state_feature["properties"]["name"]
        state_geometry = shape(state_feature["geometry"])
        state_geometries.append((state_name, state_geometry, prep(state_geometry)))

    profiles = {"Nigeria": empty_profile("Nigeria", sublayer_keys)}
    for state_name, _, _ in state_geometries:
        profiles[state_name] = empty_profile(state_name, sublayer_keys)

    catalogue = []
    temporal_years = []
    status_counts = {
        "operating": 0,
        "development": 0,
        "proposed": 0,
        "inactive": 0,
        "other": 0,
        "unknown": 0,
    }
    for category_key, layer in bundle["layers"].items():
        for sublayer_key, definition in layer["sublayers"].items():
            metadata = dict(CATALOGUE[sublayer_key])
            metadata.update(
                {
                    "key": sublayer_key,
                    "label": definition["label"],
                    "category": category_key,
                    "category_label": layer["label"],
                    "record_count": len(definition["data"]["features"]),
                    "download_url": f"{REPOSITORY_RAW}/{metadata['path']}",
                    "refresh": refresh_policy(
                        sublayer_key,
                        str(metadata.get("source_checked", metadata["source_date"])),
                    ),
                }
            )
            if metadata.get("coverage_audit_path"):
                metadata["coverage_audit_url"] = (
                    f"{REPOSITORY_RAW}/{metadata['coverage_audit_path']}"
                )
            if metadata.get("supplement_path"):
                metadata["supplement_url"] = (
                    f"{REPOSITORY_RAW}/{metadata['supplement_path']}"
                )
            if metadata.get("programme_evidence_path"):
                metadata["programme_evidence_url"] = (
                    f"{REPOSITORY_RAW}/{metadata['programme_evidence_path']}"
                )
            if metadata.get("state_year_path"):
                metadata["state_year_url"] = (
                    f"{REPOSITORY_RAW}/{metadata['state_year_path']}"
                )
            definition["metadata"] = metadata
            # A sublayer with zero currently-mapped records still gets a full
            # static API endpoint (empty FeatureCollection) for consistency,
            # but is excluded from the public catalogue -- a card with a
            # description, quality grade, and download link implies real
            # content, and showing "0 records" there reads as broken rather
            # than as an honest gap.
            if metadata["record_count"] > 0:
                catalogue.append(metadata)

            for item in definition["data"]["features"]:
                item["properties"]["_status_group"] = status_bucket(item["properties"])
                status_counts[item["properties"]["_status_group"]] += 1
                year, year_label = feature_year(sublayer_key, item["properties"])
                if year is not None:
                    item["properties"]["_year"] = year
                    item["properties"]["_year_label"] = year_label
                    temporal_years.append(year)
                geometry = shape(item["geometry"])
                if geometry.geom_type == "Point":
                    state_names = [
                        name
                        for name, _, prepared in state_geometries
                        if prepared.covers(geometry)
                    ]
                else:
                    state_names = [
                        name
                        for name, _, prepared in state_geometries
                        if prepared.intersects(geometry)
                    ]
                item["properties"]["_states"] = state_names
                update_profile(
                    profiles["Nigeria"],
                    category_key,
                    sublayer_key,
                    item["properties"],
                )
                for state_name in state_names:
                    update_profile(
                        profiles[state_name],
                        category_key,
                        sublayer_key,
                        item["properties"],
                    )

    for profile in profiles.values():
        for capacity_key, value in profile["capacity"].items():
            profile["capacity"][capacity_key] = round(value, 2)
        profile["oil_spill_intelligence"]["estimated_quantity_reported"] = round(
            profile["oil_spill_intelligence"]["estimated_quantity_reported"], 2
        )
        for key in ["report_status_counts", "cause_counts", "yearly_counts"]:
            profile["oil_spill_intelligence"][key] = dict(
                sorted(profile["oil_spill_intelligence"][key].items())
            )

    context_summary = pd.read_csv(
        PROCESSED / "08_context/state_population_access_summary_nigeria.csv"
    )
    context_columns = [
        "worldpop_population_2025",
        "dre_cluster_population",
        "settlement_count",
        "population_with_nightlight_signal",
        "population_without_nightlight_signal",
        "nightlight_population_share_pct",
        "population_weighted_distance_transmission_km",
        "population_weighted_distance_gridlight_km",
    ]
    for _, row in context_summary.iterrows():
        state_name = str(row["state"])
        if state_name in profiles:
            profiles[state_name]["people_access"] = {
                column: clean_value(row.get(column)) for column in context_columns
            }

    population_weights = context_summary["dre_cluster_population"].fillna(0)
    national_context = {
        "worldpop_population_2025": context_summary[
            "worldpop_population_2025"
        ].sum(min_count=1),
        "dre_cluster_population": context_summary[
            "dre_cluster_population"
        ].sum(min_count=1),
        "settlement_count": context_summary["settlement_count"].sum(min_count=1),
        "population_with_nightlight_signal": context_summary[
            "population_with_nightlight_signal"
        ].sum(min_count=1),
        "population_without_nightlight_signal": context_summary[
            "population_without_nightlight_signal"
        ].sum(min_count=1),
    }
    national_population = national_context["dre_cluster_population"]
    national_context["nightlight_population_share_pct"] = (
        100
        * national_context["population_with_nightlight_signal"]
        / national_population
    )
    for column in [
        "population_weighted_distance_transmission_km",
        "population_weighted_distance_gridlight_km",
    ]:
        valid = context_summary[column].notna() & population_weights.gt(0)
        national_context[column] = (
            float(
                (context_summary.loc[valid, column] * population_weights[valid]).sum()
                / population_weights[valid].sum()
            )
            if valid.any()
            else None
        )
    profiles["Nigeria"]["people_access"] = {
        key: clean_value(value) for key, value in national_context.items()
    }

    minigrid_audit = pd.read_csv(
        PROCESSED / "07_renewables/minigrid_state_coverage_audit.csv"
    )
    for _, row in minigrid_audit.iterrows():
        state_name = str(row["state"])
        if state_name in profiles:
            profiles[state_name]["minigrid_coverage"] = {
                column: clean_value(row.get(column))
                for column in minigrid_audit.columns
                if column != "state"
            }
    distributed_energy_registry = pd.read_csv(
        PROCESSED / "07_renewables/renewable_offgrid_minigrid_nigeria.csv"
    )
    profiles["Nigeria"]["minigrid_coverage"] = {
        "catalogued_record_count": int(len(distributed_energy_registry)),
        "distributed_energy_class_counts": {
            class_name: int(
                distributed_energy_registry["distributed_energy_class"]
                .value_counts()
                .get(class_name, 0)
            )
            for class_name in [
                "community_mini_grid",
                "captive_institutional_off_grid",
                "standalone_system",
                "interconnected_mini_grid",
            ]
        },
        "states_or_territories_with_records": int(
            minigrid_audit["catalogued_record_count"].gt(0).sum()
        ),
        "states_or_territories_audited": int(len(minigrid_audit)),
        "coverage_status": "national_public_source_screening_inventory",
        "coverage_interpretation": (
            "Named public records from implemented sources; not a complete "
            "national operating registry."
        ),
        "audit_date": "2026-07-25",
    }

    standalone_evidence = pd.read_csv(
        PROCESSED / "07_renewables/standalone_solar_programme_evidence.csv"
    )
    national_standalone = standalone_evidence[
        standalone_evidence["scope"].eq("Nigeria")
    ].iloc[0]
    national_context = {
        column: clean_value(national_standalone.get(column))
        for column in standalone_evidence.columns
        if column != "scope"
    }
    profiles["Nigeria"]["standalone_solar_programme"] = national_context
    state_specific = {
        str(row["scope"]): {
            column: clean_value(row.get(column))
            for column in standalone_evidence.columns
            if column != "scope"
        }
        for _, row in standalone_evidence.iterrows()
        if row["scope"] != "Nigeria"
    }
    for state_name, profile in profiles.items():
        if state_name == "Nigeria":
            continue
        profile["standalone_solar_programme"] = state_specific.get(
            state_name,
            {
                "evidence_status": "national_programme_only",
                "systems_reported": None,
                "people_reached": None,
                "as_of_date": national_context["as_of_date"],
                "programme": national_context["programme"],
                "coverage_note": (
                    "Official reporting confirms nationwide historical NEP "
                    "coverage and current DARES deployment across all six "
                    "geopolitical zones, but no state-specific unit total was "
                    "published for this state."
                ),
                "source_name": national_context["source_name"],
                "source_url": national_context["source_url"],
                "historical_context": national_context["historical_context"],
                "historical_source_url": national_context[
                    "historical_source_url"
                ],
                "reuse_note": national_context["reuse_note"],
            },
        )

    security_state_year = pd.read_csv(
        PROCESSED
        / "06_security/ucdp_organized_violence_state_year_nigeria_1989_2025.csv"
    )
    for profile_name, profile in profiles.items():
        rows = security_state_year[
            security_state_year["state"].eq(profile_name)
            & security_state_year["year"].between(2016, 2025)
        ]
        intelligence = profile["security_intelligence"]
        for column in [
            "event_count",
            "fatalities_best",
            "fatalities_low",
            "fatalities_high",
            "state_based_events",
            "non_state_events",
            "one_sided_events",
        ]:
            intelligence[column] = int(rows[column].sum())
        intelligence["yearly_counts"] = {
            str(int(row["year"])): int(row["event_count"])
            for _, row in rows.sort_values("year").iterrows()
        }

    oil_spill_features = bundle["layers"]["environmental"]["sublayers"][
        "oil_spills"
    ]["data"]["features"]
    spill_filter_fields = {
        "report_statuses": "status_label",
        "causes": "cause_label",
        "companies": "company",
    }
    spill_filters = {
        "source_record_count": 21124,
        "mapped_record_count": len(oil_spill_features),
        "default_report_status": "Confirmed",
        "fields": {},
    }
    for output_key, property_key in spill_filter_fields.items():
        counts: dict[str, int] = {}
        for item in oil_spill_features:
            value = item["properties"].get(property_key)
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
        spill_filters["fields"][output_key] = [
            {"value": value, "count": count}
            for value, count in sorted(
                counts.items(), key=lambda pair: (-pair[1], pair[0].lower())
            )
        ]

    bundle["product"] = {
        "name": ATLAS_PRODUCT_NAME,
        "master_brand": ATLAS_MASTER_BRAND,
        "premium_brand": ATLAS_PREMIUM_BRAND,
        "country": ATLAS_COUNTRY,
        "former_name": ATLAS_FORMER_NAME,
        "tagline": ATLAS_TAGLINE,
        "role": ATLAS_PRODUCT_ROLE,
        "relationship": ATLAS_PRODUCT_RELATIONSHIP,
    }
    bundle["release"] = {
        "version": ATLAS_RELEASE_VERSION,
        "date": ATLAS_RELEASE_DATE,
        "title": ATLAS_RELEASE_TITLE,
    }
    bundle["catalogue"] = catalogue
    bundle["state_profiles"] = profiles
    bundle["filters"] = {
        "status_groups": status_counts,
        "temporal": {
            "dated_records": len(temporal_years),
            "undated_records": profiles["Nigeria"]["mapped_records"] - len(temporal_years),
            "minimum_year": min(temporal_years),
            "maximum_year": max(temporal_years),
            "semantics": "When enabled, the cutoff includes only records with a known relevant year at or before the selected year.",
        },
        "oil_spills": spill_filters,
    }


def write_api_outputs(bundle: dict[str, Any], api_dir: Path = DEFAULT_API_DIR) -> None:
    """Write stable, versioned static API resources for GitHub Pages."""
    layers_dir = api_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    manifest_layers = []
    for category_key, category in bundle["layers"].items():
        for sublayer_key, definition in category["sublayers"].items():
            endpoint = f"layers/{sublayer_key}.geojson"
            layer_payload = {
                "type": "FeatureCollection",
                "name": sublayer_key,
                "product": bundle["product"],
                "atlas_release": bundle["release"],
                "metadata": definition["metadata"],
                "features": definition["data"]["features"],
            }
            (api_dir / endpoint).write_text(
                json.dumps(
                    layer_payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_layers.append(
                {
                    "key": sublayer_key,
                    "label": definition["label"],
                    "category": category_key,
                    "record_count": len(definition["data"]["features"]),
                    "endpoint": endpoint,
                }
            )

    distributed_energy_features = [
        item
        for sublayer_key in [
            "community_minigrids",
            "captive_offgrid_systems",
            "standalone_systems",
            "interconnected_minigrids",
        ]
        for item in bundle["layers"]["renewables"]["sublayers"][sublayer_key][
            "data"
        ]["features"]
    ]
    compatibility_endpoints = {
        "minigrids": {
            "endpoint": "layers/minigrids.geojson",
            "record_count": len(distributed_energy_features),
            "status": "backward_compatible_aggregate",
            "replacement_layers": [
                "community_minigrids",
                "captive_offgrid_systems",
                "standalone_systems",
                "interconnected_minigrids",
            ],
        }
    }
    compatibility_payload = {
        "type": "FeatureCollection",
        "name": "minigrids",
        "product": bundle["product"],
        "atlas_release": bundle["release"],
        "metadata": {
            "key": "minigrids",
            "label": "Distributed Energy · Compatibility Aggregate",
            "record_count": len(distributed_energy_features),
            "compatibility_alias": True,
            "quality_note": (
                "Backward-compatible aggregate of the four structured "
                "distributed-energy layers. New integrations should use the "
                "replacement layers listed in manifest.json."
            ),
        },
        "features": distributed_energy_features,
    }
    (layers_dir / "minigrids.geojson").write_text(
        json.dumps(
            compatibility_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    states_payload = {
        "type": "FeatureCollection",
        "name": "nigeria_adm1",
        "product": bundle["product"],
        "atlas_release": bundle["release"],
        "features": bundle["states"]["features"],
    }
    (api_dir / "states.geojson").write_text(
        json.dumps(states_payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (api_dir / "catalogue.json").write_text(
        json.dumps(
            {
                "product": bundle["product"],
                "atlas_release": bundle["release"],
                "datasets": bundle["catalogue"],
                "compatibility_endpoints": compatibility_endpoints,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (api_dir / "state-profiles.json").write_text(
        json.dumps(
            {
                "product": bundle["product"],
                "atlas_release": bundle["release"],
                "method": "Public-map records whose display geometry intersects each ADM1 boundary.",
                "profiles": bundle["state_profiles"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://diamonds10.github.io/infraxis-atlas-nigeria/api/v1/schema.json",
        "title": "Infraxis Atlas — Nigeria public GeoJSON feature",
        "type": "object",
        "required": ["type", "properties", "geometry"],
        "properties": {
            "type": {"const": "Feature"},
            "properties": {
                "type": "object",
                "required": ["_status_group", "_states"],
                "properties": {
                    "_states": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                    "_status_group": {
                        "enum": [
                            "operating",
                            "development",
                            "proposed",
                            "inactive",
                            "other",
                            "unknown",
                        ]
                    },
                    "_year": {"type": "integer", "minimum": 1800, "maximum": 2026},
                    "_year_label": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "geometry": {"type": "object"},
        },
        "additionalProperties": True,
    }
    (api_dir / "schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    freshness_inventory = [
        definition["metadata"]
        for category in bundle["layers"].values()
        for definition in category["sublayers"].values()
    ]
    freshness = {
        "product": bundle["product"],
        "atlas_release": bundle["release"],
        "interpretation": (
            "Review dates are maintenance targets, not guarantees that an "
            "upstream publisher has issued new data."
        ),
        "summary": {
            "dataset_count": len(freshness_inventory),
            "current": sum(
                item["refresh"]["review_status"] == "current"
                for item in freshness_inventory
            ),
            "due": sum(
                item["refresh"]["review_status"] == "due"
                for item in freshness_inventory
            ),
        },
        "datasets": [
            {
                "key": item["key"],
                "label": item["label"],
                "source": item["source"],
                **item["refresh"],
            }
            for item in freshness_inventory
        ],
    }
    (api_dir / "freshness.json").write_text(
        json.dumps(freshness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "product": bundle["product"],
        "api_version": "v1",
        "atlas_release": bundle["release"],
        "base_url": "https://diamonds10.github.io/infraxis-atlas-nigeria/api/v1/",
        "formats": ["GeoJSON", "JSON"],
        "filter_fields": {
            "_states": "ADM1 names intersected by the public display geometry",
            "_status_group": "Normalized status group",
            "_year": "Relevant discovery, start, commissioning, incident, designation, or source release year",
            "_year_label": "Meaning of _year for the record",
            "oil_spills": "Oil-spill records also expose report status, cause, company, incident year, and date-quality fields",
        },
        "endpoints": {
            "catalogue": "catalogue.json",
            "schema": "schema.json",
            "freshness": "freshness.json",
            "state_profiles": "state-profiles.json",
            "states": "states.geojson",
        },
        "layers": manifest_layers,
        "compatibility_endpoints": compatibility_endpoints,
    }
    (api_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_bundle(states_path: Path = DEFAULT_STATES) -> dict[str, Any]:
    states = json.loads(states_path.read_text(encoding="utf-8"))

    GOGET_FIELDS_COLUMNS = [
        "project", "status", "operator", "owner", "fuel_type",
        "discovery_year", "start_year", "url",
    ]
    fields_oil = point_features(
        PROCESSED / "01_resource/goget_fields_nigeria_2023-08.csv",
        "lng", "lat", GOGET_FIELDS_COLUMNS, "project",
        where=("fuel_type", {"oil"}),
    )
    fields_gas = point_features(
        PROCESSED / "01_resource/goget_fields_nigeria_2023-08.csv",
        "lng", "lat", GOGET_FIELDS_COLUMNS, "project",
        where=("fuel_type", {"gas", "oil and gas"}),
    )

    SE4ALL_FIELD_POLYGON_COLUMNS = ["name", "field_type", "in_goget_fields"]

    def load_field_polygons(allowed_types: set[str]) -> list[dict[str, Any]]:
        items = wkt_features(
            PROCESSED / "01_resource/se4all_gas_fields_nigeria_2026-07.csv",
            "geometry",
            SE4ALL_FIELD_POLYGON_COLUMNS,
            "name",
            where=("field_type", allowed_types),
        )
        for item in items:
            if "in_goget_fields" in item["properties"]:
                item["properties"]["in_goget_fields"] = "Yes" if item["properties"]["in_goget_fields"] else "No"
        return items

    field_polygons_gas = load_field_polygons({"Gas_Field"})
    field_polygons_mixed = load_field_polygons({"Crude Oil and Gas Field", "Unspecified"})
    gas_pipelines = route_features(
        PROCESSED / "02_infrastructure/ggit_gas_pipelines_nigeria.csv",
        [
            "project", "parent", "status", "start_year", "capacity",
            "capacity_units", "url",
        ],
        "project",
    )
    oil_pipelines = route_features(
        PROCESSED / "02_infrastructure/goit_oil_ngl_pipelines_nigeria.csv",
        ["project", "parent", "status", "start_year", "capacity", "url"],
        "project",
    )
    lng_terminals = point_features(
        PROCESSED / "02_infrastructure/ggit_lng_terminals_nigeria.csv",
        "lng", "lat",
        [
            "project", "unit", "parent", "status", "start_year", "capacity",
            "capacity_units", "url",
        ],
        "project",
    )
    power_plants = point_features(
        PROCESSED / "02_infrastructure/gogpt_oil_gas_plants_nigeria.csv",
        "lng", "lat",
        [
            "project", "unit", "province", "status", "fuel_type", "capacity",
            "technology", "start_year", "owner", "url",
        ],
        "project",
    )
    hydro_plants = point_features(
        PROCESSED / "02_infrastructure/ght_hydropower_nigeria.csv",
        "lng", "lat",
        ["project", "capacity", "units", "type", "status", "start_year", "owner", "operator", "url"],
        "project",
    )
    refineries = point_features(
        PROCESSED / "02_infrastructure/refineries_nigeria.csv",
        "lng", "lat",
        ["project", "operator", "state", "status", "capacity_bpd", "commissioned_year"],
        "project",
    )
    gas_infrastructure = wkt_features(
        PROCESSED / "02_infrastructure/se4all_gas_infrastructure_nigeria_2026-07.csv",
        "geometry",
        ["name", "type", "status", "company", "location", "design_cap", "date_of_co"],
        "name",
        exclude_notna="possible_duplicate_of",
    )
    oil_spills = point_features(
        PROCESSED / "03_environmental/nosdra_oil_spills_nigeria.csv",
        "longitude", "latitude",
        [
            "id", "incidentnumber", "company", "incidentdate", "incident_year",
            "incident_date_quality", "status", "status_label", "cause_label",
            "is_sabotage_attributed",
            "contaminant_label", "facility_label", "habitat_label", "estimatedquantity",
            "state_label", "lga", "sitelocationname",
        ],
        "sitelocationname",
    )
    for item in oil_spills:
        if "is_sabotage_attributed" in item["properties"]:
            item["properties"]["is_sabotage_attributed"] = (
                "Yes" if item["properties"]["is_sabotage_attributed"] else "No"
            )
    protected_areas = wkt_features(
        PROCESSED / "03_environmental/wdpa_protected_areas_nigeria.csv",
        "geometry",
        ["NAME", "DESIG_ENG", "IUCN_CAT", "GIS_AREA", "STATUS", "STATUS_YR", "GOV_TYPE"],
        "NAME",
    )
    conflict_exposure = point_features(
        PROCESSED
        / "06_security/ucdp_organized_violence_grid_nigeria_2016_2025.csv",
        "grid_lon",
        "grid_lat",
        [
            "cell_id",
            "period",
            "event_count",
            "fatalities_best",
            "fatalities_low",
            "fatalities_high",
            "first_year",
            "latest_year",
            "state_based_events",
            "non_state_events",
            "one_sided_events",
            "source_states",
            "best_source_precision",
            "least_source_precision",
        ],
        "cell_id",
    )
    demand_centers = point_features(
        PROCESSED / "04_demand/demand_centers_nigeria.csv",
        "lon", "lat",
        ["demand_center", "category", "state_or_region", "status", "notes"],
        "demand_center",
    )
    roads = wkt_features(
        PROCESSED / "05_connectivity/osm_roads_major_nigeria.csv",
        "geometry", ["highway", "name", "ref", "surface", "lanes"], "name",
        where=("highway", {"motorway", "trunk"}),
    )
    railways = wkt_features(
        PROCESSED / "05_connectivity/osm_railways_nigeria.csv",
        "geometry", ["railway", "name", "operator", "gauge"], "name",
        where=("railway", {"rail"}),
    )
    rail_stations = wkt_features(
        PROCESSED / "05_connectivity/osm_railways_nigeria.csv",
        "geometry", ["name"], "name",
        where=("railway", {"station"}),
    )
    power_grid = wkt_features(
        PROCESSED / "05_connectivity/osm_power_grid_nigeria.csv",
        "geometry", ["power", "name", "operator", "voltage"], "name",
        where=("power", {"line", "minor_line"}),
    )
    substations = wkt_features(
        PROCESSED / "05_connectivity/osm_power_grid_nigeria.csv",
        "geometry", ["power", "name", "operator", "voltage"], "name",
        where=("power", {"substation"}),
        centroid=True,
    )
    ports = wkt_features(
        PROCESSED / "05_connectivity/world_port_index_nigeria.csv",
        "geometry",
        [
            "PORT_NAME", "HARBORSIZE", "HARBORTYPE", "CARGOWHARF",
            "CRANEFIXED", "RAILWAY", "MAX_VESSEL",
        ],
        "PORT_NAME",
        centroid=True,
    )
    distributed_energy = point_features(
        PROCESSED / "07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "longitude", "latitude",
        [
            "asset_id", "asset_name", "asset_type", "distributed_energy_class",
            "classification_basis", "classification_confidence",
            "program_name", "state", "lga",
            "community", "technology", "status", "capacity_kw",
            "customers_served", "developer", "owner_operator",
            "financing_source", "geocode_precision", "coordinate_source",
            "source_name", "source_url", "source_date_accessed",
            "evidence_level", "record_origin", "notes",
        ],
        "asset_name",
    )
    distributed_energy_by_class = {
        class_name: [
            item
            for item in distributed_energy
            if item["properties"].get("distributed_energy_class") == class_name
        ]
        for class_name in {
            "community_mini_grid",
            "captive_institutional_off_grid",
            "standalone_system",
            "interconnected_mini_grid",
        }
    }
    population_access = point_features(
        PROCESSED / "08_context/population_access_grid_nigeria.csv",
        "grid_lon",
        "grid_lat",
        [
            "cell_id",
            "population_estimate",
            "settlement_count",
            "population_with_nightlight_signal",
            "population_without_nightlight_signal",
            "nightlight_population_share_pct",
            "total_buildings",
            "modeled_demand",
            "population_weighted_distance_transmission_km",
            "population_weighted_distance_gridlight_km",
        ],
        "cell_id",
    )
    settlements = point_features(
        PROCESSED / "08_context/major_settlements_nigeria.csv",
        "lon",
        "lat",
        [
            "geohash",
            "settlement_name",
            "state",
            "lga",
            "population",
            "state_population_rank",
            "num_buildings",
            "nightlight_signal",
            "distance_to_existing_transmission_lines",
            "distance_to_existing_hv_transmission_lines",
            "distance_to_gridlight_targets",
            "main_road_access",
            "dist_main_road_km",
            "has_education_facility",
            "has_health_facility",
        ],
        "settlement_name",
    )

    bundle = {
        "states": states,
        "layers": {
            "resource": {
                "label": "Resource",
                "sublayers": {
                    "fields_oil": sublayer("Oil-only Fields · Source Classified", "point", fields_oil),
                    "fields_gas": sublayer("Gas-producing Fields · Source Classified", "point", fields_gas),
                    "field_polygons_gas": sublayer("Gas Field Boundaries", "polygon", field_polygons_gas),
                    "field_polygons_mixed": sublayer("Oil & Gas Field Boundaries (mixed)", "polygon", field_polygons_mixed),
                },
            },
            "infrastructure": {
                "label": "Infrastructure",
                "sublayers": {
                    "gas_pipelines": sublayer("Gas Pipelines", "line", gas_pipelines),
                    "oil_pipelines": sublayer("Oil & NGL Pipelines", "line", oil_pipelines),
                    "lng_terminals": sublayer("LNG Terminals", "point", lng_terminals),
                    "power_plants": sublayer("Gas & Oil Power Plants", "point", power_plants),
                    "hydro_plants": sublayer("Hydroelectric Power Plants", "point", hydro_plants),
                    "refineries": sublayer("Refineries", "point", refineries),
                    "gas_infrastructure": sublayer("Gas & Oil Point Infrastructure", "point", gas_infrastructure),
                },
            },
            "environmental": {
                "label": "Environmental",
                "sublayers": {
                    "oil_spills": sublayer("Oil Spill Incidents (NOSDRA)", "point", oil_spills),
                    "protected_areas": sublayer(
                        "Protected Areas (WDPA)", "polygon", protected_areas
                    )
                },
            },
            "security": {
                "label": "Security Context",
                "sublayers": {
                    "conflict_exposure": sublayer(
                        "Historical Organized-Violence Exposure (UCDP, 2016–2025)",
                        "point",
                        conflict_exposure,
                    )
                },
            },
            "demand": {
                "label": "Demand",
                "sublayers": {
                    "demand_centers": sublayer("Demand Centers", "point", demand_centers)
                },
            },
            "connectivity": {
                "label": "Connectivity",
                "sublayers": {
                    "roads": sublayer("Major Roads", "line", roads),
                    "railways": sublayer("Railways", "line", railways),
                    "rail_stations": sublayer("Railway Stations", "point", rail_stations),
                    "power_grid": sublayer("Power Grid Lines", "line", power_grid),
                    "substations": sublayer("Substations", "point", substations),
                    "ports": sublayer("Ports & Terminals", "point", ports),
                },
            },
            "renewables": {
                "label": "Distributed Energy",
                "sublayers": {
                    "community_minigrids": sublayer(
                        "Community Mini-grids",
                        "point",
                        distributed_energy_by_class["community_mini_grid"],
                    ),
                    "captive_offgrid_systems": sublayer(
                        "Captive & Institutional Off-grid",
                        "point",
                        distributed_energy_by_class[
                            "captive_institutional_off_grid"
                        ],
                    ),
                    "standalone_systems": sublayer(
                        "Standalone Systems",
                        "point",
                        distributed_energy_by_class["standalone_system"],
                    ),
                    "interconnected_minigrids": sublayer(
                        "Interconnected Mini-grids",
                        "point",
                        distributed_energy_by_class[
                            "interconnected_mini_grid"
                        ],
                    ),
                },
            },
            "context": {
                "label": "People & Access",
                "sublayers": {
                    "population_access": sublayer(
                        "Population & Access Grid", "point", population_access
                    ),
                    "settlements": sublayer(
                        "Major Settlements", "point", settlements
                    ),
                },
            },
        },
    }
    add_catalogue_and_state_profiles(bundle)
    return bundle


def write_bundle(bundle: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(bundle, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", type=Path, default=DEFAULT_STATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--api-dir", type=Path, default=DEFAULT_API_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_bundle(args.states.resolve())
    write_bundle(bundle, args.output.resolve())
    write_api_outputs(bundle, args.api_dir.resolve())
    total = sum(
        len(sub["data"]["features"])
        for layer in bundle["layers"].values()
        for sub in layer["sublayers"].values()
    )
    print(
        f"Saved {args.output} with {total:,} public map features "
        f"and API resources under {args.api_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
