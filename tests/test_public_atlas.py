"""Release-gate checks for processed data and the public atlas bundle."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "docs" / "assets" / "atlas_data.json"
BUILDER_PATH = ROOT / "scripts" / "build_public_atlas_data.py"
API_DIR = ROOT / "docs" / "api" / "v1"
APP_PATH = ROOT / "docs" / "assets" / "app.js"
CSS_PATH = ROOT / "docs" / "assets" / "app.css"
INDEX_PATH = ROOT / "docs" / "index.html"
ATLAS_ISSUE_TEMPLATE_PATH = (
    ROOT / ".github" / "ISSUE_TEMPLATE" / "atlas-data-submission.yml"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("build_public_atlas_data", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PublicAtlasTests(unittest.TestCase):
    def test_committed_bundle_is_reproducible(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            rebuilt_path = Path(directory) / "atlas_data.json"
            deferred_dir = Path(directory) / "layers"
            full_bundle = builder.build_bundle()
            web_bundle = builder.prepare_web_bundle(full_bundle, deferred_dir)
            builder.write_bundle(web_bundle, rebuilt_path)
            self.assertEqual(
                BUNDLE_PATH.read_bytes(),
                rebuilt_path.read_bytes(),
                "Run: python scripts/build_public_atlas_data.py",
            )
            committed_deferred = ROOT / "docs" / "assets" / "layers"
            for key in sorted(builder.DEFERRED_WEB_LAYERS):
                self.assertEqual(
                    (committed_deferred / f"{key}.geojson").read_bytes(),
                    (deferred_dir / f"{key}.geojson").read_bytes(),
                    f"Deferred layer drift for {key}; rebuild the public atlas.",
                )

    def _layer_feature_count(self, definition):
        deferred = definition.get("deferred") or {}
        if "feature_count" in deferred:
            return deferred["feature_count"]
        return len(definition["data"]["features"])

    def test_public_layer_counts(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        layers = bundle["layers"]
        counts = {
            sublayer: self._layer_feature_count(definition)
            for layer in layers.values()
            for sublayer, definition in layer["sublayers"].items()
        }
        self.assertEqual(
            counts,
            {
                "fields_oil": 33,
                "fields_gas": 147,
                "field_polygons_gas": 62,
                "field_polygons_mixed": 62,
                "gas_pipelines": 24,
                "oil_pipelines": 15,
                "lng_terminals": 24,
                "power_plants": 193,
                "hydro_plants": 7,
                "refineries": 4,
                "gas_infrastructure": 98,
                "oil_spills": 16326,
                "protected_areas": 1005,
                "conflict_exposure": 227,
                "demand_centers": 28,
                "roads": 5124,
                "railways": 1381,
                "rail_stations": 141,
                "power_grid": 931,
                "substations": 390,
                "ports": 25,
                "community_minigrids": 81,
                "captive_offgrid_systems": 10,
                "standalone_systems": 0,
                "interconnected_minigrids": 2,
                "population_access": 1278,
                "settlements": 1480,
            },
        )
        for key in [
            "oil_spills",
            "roads",
            "railways",
            "protected_areas",
            "settlements",
            "population_access",
        ]:
            definition = next(
                definition
                for layer in layers.values()
                for sublayer, definition in layer["sublayers"].items()
                if sublayer == key
            )
            self.assertEqual(definition["data"]["features"], [])
            self.assertEqual(
                definition["deferred"]["url"],
                f"./assets/layers/{key}.geojson",
            )
        distributed_energy = [
            feature
            for key in [
                "community_minigrids",
                "captive_offgrid_systems",
                "standalone_systems",
                "interconnected_minigrids",
            ]
            for feature in layers["renewables"]["sublayers"][key]["data"][
                "features"
            ]
        ]
        asset_ids = [
            feature["properties"]["asset_id"] for feature in distributed_energy
        ]
        self.assertEqual(len(asset_ids), 93)
        self.assertEqual(len(set(asset_ids)), 93)

    def test_coordinates_and_required_processed_columns(self):
        checks = {
            "data/processed/01_resource/goget_fields_nigeria_2023-08.csv": {
                "project", "lat", "lng",
            },
            "data/processed/04_demand/demand_centers_nigeria.csv": {
                "demand_center", "lat", "lon",
            },
            "data/processed/03_environmental/nosdra_oil_spills_nigeria.csv": {
                "id", "status_label", "incidentdate", "incident_year",
                "incident_date_quality", "cause_label", "latitude", "longitude",
            },
            "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv": {
                "asset_name", "latitude", "longitude", "status",
                "distributed_energy_class", "classification_basis",
                "classification_confidence",
            },
            "data/processed/07_renewables/standalone_solar_programme_evidence.csv": {
                "scope", "evidence_status", "systems_reported",
                "people_reached", "source_url", "reuse_note",
            },
            "data/processed/06_security/ucdp_organized_violence_grid_nigeria_2016_2025.csv": {
                "cell_id", "period", "grid_lat", "grid_lon", "event_count",
                "fatalities_best", "fatalities_low", "fatalities_high",
            },
            "data/processed/06_security/ucdp_organized_violence_state_year_nigeria_1989_2025.csv": {
                "state", "year", "event_count", "fatalities_best",
                "state_based_events", "non_state_events", "one_sided_events",
            },
            "data/processed/08_context/population_access_grid_nigeria.csv": {
                "cell_id", "grid_lat", "grid_lon", "population_estimate",
                "nightlight_population_share_pct",
            },
            "data/processed/08_context/state_population_access_summary_nigeria.csv": {
                "state", "worldpop_population_2025", "settlement_count",
            },
        }
        for relative_path, required in checks.items():
            frame = pd.read_csv(ROOT / relative_path)
            self.assertTrue(required.issubset(frame.columns))

        minigrids = pd.read_csv(
            ROOT / "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv"
        )
        self.assertTrue(minigrids["longitude"].between(2.5, 14.8).all())
        self.assertTrue(minigrids["latitude"].between(3.9, 14.0).all())
        self.assertTrue(minigrids["asset_id"].is_unique)
        self.assertEqual(len(minigrids), 93)
        self.assertEqual(
            minigrids["record_origin"].value_counts().to_dict(),
            {
                "nigeria_se4all": 66,
                "official_supplement": 14,
                "nigeria_se4all_survey": 13,
            },
        )
        self.assertEqual(
            minigrids["distributed_energy_class"].value_counts().to_dict(),
            {
                "community_mini_grid": 81,
                "captive_institutional_off_grid": 10,
                "interconnected_mini_grid": 2,
            },
        )
        self.assertTrue(
            minigrids["classification_basis"]
            .eq("deterministic_asset_type_mapping")
            .all()
        )
        survey_records = minigrids[
            minigrids["record_origin"].eq("nigeria_se4all_survey")
        ]
        self.assertEqual(len(survey_records), 13)
        self.assertTrue(survey_records["geocode_precision"].eq("community").all())
        self.assertTrue(
            survey_records["classification_confidence"].eq("medium").all()
        )
        kano = minigrids[minigrids["state"] == "Kano"]
        self.assertEqual(len(kano), 2)
        self.assertTrue(
            kano["asset_name"].str.contains("Bayero University").all()
        )

        audit = pd.read_csv(
            ROOT / "data/processed/07_renewables/minigrid_state_coverage_audit.csv"
        )
        self.assertEqual(len(audit), 37)
        self.assertTrue(audit["state"].is_unique)
        self.assertTrue(
            audit["catalogued_record_count"].eq(
                audit["se4all_record_count"]
                + audit["se4all_survey_record_count"]
                + audit["official_supplement_count"]
            ).all()
        )
        self.assertEqual(
            set(audit.loc[audit["catalogued_record_count"].eq(0), "state"]),
            {"Abia", "Borno", "Ekiti", "Enugu", "Zamfara"},
        )
        self.assertTrue(
            audit.loc[
                audit["catalogued_record_count"].eq(0), "coverage_interpretation"
            ].str.contains("must not be interpreted as zero assets").all()
        )

        spills = pd.read_csv(
            ROOT / "data/processed/03_environmental/nosdra_oil_spills_nigeria.csv",
            low_memory=False,
        )
        self.assertEqual(len(spills), 21124)
        self.assertEqual(
            spills[["latitude", "longitude"]].notna().all(axis=1).sum(),
            16326,
        )
        self.assertEqual(
            spills["incident_date_quality"].value_counts().to_dict(),
            {
                "source_reported": 20451,
                "missing": 672,
                "implausible": 1,
            },
        )
        implausible = spills[spills["incident_date_quality"].eq("implausible")]
        self.assertEqual(implausible["incidentdate"].tolist(), ["1902-02-08"])
        self.assertTrue(implausible["incident_year"].isna().all())
        self.assertTrue(
            spills.loc[spills["incident_year"].notna(), "incident_year"]
            .between(1950, 2026)
            .all()
        )

        context = pd.read_csv(
            ROOT / "data/processed/08_context/state_population_access_summary_nigeria.csv"
        )
        self.assertEqual(len(context), 37)
        self.assertTrue(context["state"].is_unique)
        self.assertFalse(context["worldpop_population_2025"].isna().any())
        self.assertFalse(context["settlement_count"].isna().any())
        self.assertTrue(context["nightlight_population_share_pct"].between(0, 100).all())

        conflict_grid = pd.read_csv(
            ROOT / "data/processed/06_security/ucdp_organized_violence_grid_nigeria_2016_2025.csv"
        )
        self.assertEqual(len(conflict_grid), 227)
        self.assertTrue(conflict_grid["period"].eq("2016-2025").all())
        self.assertTrue(
            ((conflict_grid["grid_lat"] * 2) % 1).eq(0.5).all()
        )
        self.assertTrue(
            ((conflict_grid["grid_lon"] * 2) % 1).eq(0.5).all()
        )
        self.assertTrue(
            {
                "side_a", "side_b", "source_article", "where_coordinates",
                "where_description",
            }.isdisjoint(conflict_grid.columns)
        )

    def test_field_taxonomy_is_non_overlapping_and_gas_inclusive(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        resource = bundle["layers"]["resource"]["sublayers"]
        self.assertNotIn("fields_mixed", resource)
        oil = resource["fields_oil"]["data"]["features"]
        gas = resource["fields_gas"]["data"]["features"]
        self.assertEqual(len(oil), 33)
        self.assertEqual(len(gas), 147)
        self.assertEqual(len(oil) + len(gas), 180)
        self.assertEqual(
            {item["properties"]["fuel_type"] for item in oil},
            {"oil"},
        )
        self.assertEqual(
            {item["properties"]["fuel_type"] for item in gas},
            {"gas", "oil and gas"},
        )

    def test_map_symbology_covers_every_public_sublayer(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        sublayer_keys = {
            key
            for category in bundle["layers"].values()
            for key in category["sublayers"]
        }
        app_source = APP_PATH.read_text(encoding="utf-8")
        style_keys = set(
            re.findall(
                r"^\s{4}([a-z_]+):\s*\{\s*colorVar:\s*\"--layer-",
                app_source,
                flags=re.MULTILINE,
            )
        )
        self.assertEqual(style_keys, sublayer_keys)

        css_source = CSS_PATH.read_text(encoding="utf-8")
        color_declarations = re.findall(
            r"^\s*--(layer-[a-z-]+):\s*(#[0-9A-Fa-f]{6});",
            css_source,
            flags=re.MULTILINE,
        )
        layer_colors = dict(color_declarations)
        self.assertEqual(len(layer_colors), len(sublayer_keys))
        self.assertEqual(
            len(set(layer_colors.values())),
            len(layer_colors),
            "Every public sublayer should have a distinct color",
        )

        def relative_luminance(hex_color):
            channels = [
                int(hex_color[index:index + 2], 16) / 255
                for index in (1, 3, 5)
            ]
            linear = [
                value / 12.92
                if value <= 0.04045
                else ((value + 0.055) / 1.055) ** 2.4
                for value in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def contrast(first, second):
            lighter, darker = sorted(
                (relative_luminance(first), relative_luminance(second)),
                reverse=True,
            )
            return (lighter + 0.05) / (darker + 0.05)

        palette_size = len(sublayer_keys)
        light_palette = dict(color_declarations[:palette_size])
        dark_palette = dict(color_declarations[palette_size:palette_size * 2])
        self.assertTrue(
            all(contrast(color, "#F6F7F2") >= 3 for color in light_palette.values())
        )
        self.assertTrue(
            all(contrast(color, "#16281F") >= 3 for color in dark_palette.values())
        )

    def test_oil_spill_intelligence_controls_and_clustering_are_wired(self):
        app_source = APP_PATH.read_text(encoding="utf-8")
        html_source = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn("L.markerClusterGroup", app_source)
        self.assertIn("chunkedLoading: true", app_source)
        self.assertIn('id="spill-status-filter"', html_source)
        self.assertIn('id="spill-cause-filter"', html_source)
        self.assertIn('id="spill-company-filter"', html_source)
        self.assertIn("leaflet.markercluster@1.5.3", html_source)
        self.assertIn("issues/new/choose", html_source)
        self.assertIn('id="download-report"', html_source)
        self.assertIn("profileTimelineChart", app_source)
        self.assertIn("state-report-v", app_source)
        self.assertIn("Historical organized-violence context", app_source)
        self.assertIn("not a live threat feed", app_source)

    def test_public_frontend_hardening_contract(self):
        app_source = APP_PATH.read_text(encoding="utf-8")
        html_source = INDEX_PATH.read_text(encoding="utf-8")
        issue_template = ATLAS_ISSUE_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("light_nolabels", app_source)
        self.assertIn("dark_nolabels", app_source)
        self.assertNotIn("light_all/{z}", app_source)
        self.assertNotIn("dark_all/{z}", app_source)
        self.assertIn("fillOpacity: selected ? 0.22 : 0.06", app_source)

        self.assertIn("data-remote-download", app_source)
        self.assertIn("fetch(link.href)", app_source)
        self.assertIn("anchor.download = filename", app_source)
        self.assertNotIn(
            'target="_blank" rel="noopener">Download processed CSV',
            app_source,
        )

        self.assertIn("./assets/app.css?v=0.12.1.1", html_source)
        self.assertIn("./assets/app.js?v=0.12.1", html_source)
        self.assertIn("./assets/atlas_data.json?v=0.12.1", app_source)
        self.assertIn("ensureSublayerLoaded", app_source)
        self.assertIn("        - Security Context", issue_template)
        css_source = (ROOT / "docs" / "assets" / "app.css").read_text(encoding="utf-8")
        self.assertIn("overflow-wrap: anywhere", css_source)
        self.assertNotIn(
            ".profile-metric span {\n    display: block;\n    overflow: hidden;",
            css_source,
        )

    def test_infraxis_country_edition_brand_contract(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        app_source = APP_PATH.read_text(encoding="utf-8")
        html_source = INDEX_PATH.read_text(encoding="utf-8")

        self.assertEqual(
            bundle["product"],
            {
                "name": "Infraxis Atlas — Nigeria",
                "master_brand": "Infraxis Atlas",
                "premium_brand": "Infraxis",
                "country": "Nigeria",
                "former_name": "Nigeria Infrastructure Atlas",
                "tagline": "Mapping infrastructure. Measuring disruption.",
                "role": "open_datasource",
                "relationship": (
                    "This open atlas is the public datasource and screening layer; "
                    "Infraxis is the separate premium analytical layer built on top of it."
                ),
            },
        )
        self.assertIn("<title>Infraxis Atlas — Nigeria</title>", html_source)
        self.assertIn('<span class="mark">Infraxis Atlas</span>', html_source)
        self.assertIn("Open atlas · Infraxis premium is separate", html_source)
        self.assertIn("infraxis-atlas-nigeria-", app_source)
        self.assertIn("Infraxis Atlas — Nigeria state report", app_source)
        self.assertNotIn("nigeria-infrastructure-atlas-\" + slug", app_source)
        identity = (ROOT / "docs" / "product_identity.md").read_text(encoding="utf-8")
        self.assertIn("The atlas is the open datasource. Infraxis is the premium layer.", identity)
        self.assertIn('role: "open_datasource"', identity)

    def test_benchmark_matches_processed_assets(self):
        benchmark = json.loads(
            (ROOT / "outputs/maps/public_asset_benchmark_summary.json").read_text()
        )
        counts = benchmark["asset_counts"]
        self.assertEqual(counts["power_plants"], 193)
        self.assertEqual(counts["substations"], 390)
        self.assertEqual(counts["demand_centres"], 28)
        self.assertEqual(counts["mini_grids"], 93)
        self.assertEqual(
            benchmark["mini_grid_benchmark"][
                "distributed_energy_class_distribution"
            ],
            {
                "community_mini_grid": 81,
                "captive_institutional_off_grid": 10,
                "standalone_system": 0,
                "interconnected_mini_grid": 2,
            },
        )
        self.assertEqual(
            benchmark["oil_spill_benchmark"],
            {
                "source_report_count": 21124,
                "mapped_report_count": 16326,
                "confirmed_mapped_report_count": 14382,
                "sabotage_attributed_mapped_report_count": 12718,
                "plausible_incident_year_count": 20451,
                "implausible_incident_date_count": 1,
            },
        )

    def test_state_profiles_are_complete_and_consistent(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        profiles = bundle["state_profiles"]
        state_names = {
            feature["properties"]["name"]
            for feature in bundle["states"]["features"]
        }
        self.assertEqual(set(profiles), state_names | {"Nigeria"})
        self.assertEqual(len(profiles), 38)

        national = profiles["Nigeria"]
        self.assertEqual(national["mapped_records"], 29098)
        self.assertEqual(national["counts"]["oil_spills"], 16326)
        spill = national["oil_spill_intelligence"]
        self.assertEqual(spill["mapped_reports"], 16326)
        self.assertEqual(spill["confirmed_reports"], 14382)
        self.assertEqual(spill["invalid_reports"], 551)
        self.assertEqual(spill["sabotage_attributed_reports"], 12718)
        self.assertEqual(spill["estimated_quantity_reported"], 733861.56)
        self.assertEqual(sum(spill["report_status_counts"].values()), 16326)
        self.assertEqual(sum(spill["cause_counts"].values()), 15903)
        self.assertGreater(sum(spill["yearly_counts"].values()), 0)
        self.assertEqual(national["counts"]["power_plants"], 193)
        self.assertEqual(national["counts"]["substations"], 390)
        self.assertEqual(national["counts"]["community_minigrids"], 81)
        self.assertEqual(national["counts"]["captive_offgrid_systems"], 10)
        self.assertEqual(national["counts"]["standalone_systems"], 0)
        self.assertEqual(national["counts"]["interconnected_minigrids"], 2)
        self.assertEqual(
            national["minigrid_coverage"]["distributed_energy_class_counts"],
            {
                "community_mini_grid": 81,
                "captive_institutional_off_grid": 10,
                "standalone_system": 0,
                "interconnected_mini_grid": 2,
            },
        )
        self.assertAlmostEqual(national["capacity"]["minigrid_kw"], 33680.4)
        self.assertEqual(
            national["standalone_solar_programme"]["systems_reported"],
            830000.0,
        )
        self.assertEqual(
            national["standalone_solar_programme"]["people_reached"],
            3900000.0,
        )
        self.assertEqual(
            national["security_intelligence"]["event_count"],
            5565,
        )
        self.assertEqual(
            national["security_intelligence"]["fatalities_best"],
            34105,
        )
        self.assertEqual(national["people_access"]["settlement_count"], 154319)
        self.assertAlmostEqual(
            national["people_access"]["worldpop_population_2025"],
            237527782.002,
        )
        for profile in profiles.values():
            self.assertIn("people_access", profile)
            self.assertIn("minigrid_coverage", profile)
            self.assertIn("standalone_solar_programme", profile)
            self.assertIn("security_intelligence", profile)

        for layer in bundle["layers"].values():
            for definition in layer["sublayers"].values():
                for feature in definition["data"]["features"]:
                    memberships = feature["properties"]["_states"]
                    self.assertTrue(set(memberships).issubset(state_names))

        ports = json.loads(
            (ROOT / "docs/api/v1/layers/ports.geojson").read_text(encoding="utf-8")
        )
        port_states = {
            (
                feature["properties"].get("_label")
                or feature["properties"].get("PORT_NAME")
            ): feature["properties"].get("_states") or []
            for feature in ports["features"]
        }
        self.assertIn("Lagos", port_states["LAGOS"])
        self.assertIn("Lagos", port_states["TIN CAN ISLAND"])
        self.assertTrue(
            all(port_states.values()),
            "every port should resolve to at least one state",
        )
        self.assertGreaterEqual(profiles["Lagos"]["counts"]["ports"], 2)

    def test_catalogue_covers_every_public_sublayer(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        catalogue = {item["key"]: item for item in bundle["catalogue"]}
        sublayers = {
            key: definition
            for layer in bundle["layers"].values()
            for key, definition in layer["sublayers"].items()
        }
        content_bearing = {
            key
            for key, definition in sublayers.items()
            if self._layer_feature_count(definition) > 0
        }
        self.assertEqual(set(catalogue), content_bearing)
        self.assertNotIn("standalone_systems", catalogue)
        standalone_metadata = sublayers["standalone_systems"]["metadata"]
        self.assertTrue(
            standalone_metadata["programme_evidence_url"].endswith(
                "standalone_solar_programme_evidence.csv"
            )
        )
        for key in content_bearing:
            definition = sublayers[key]
            metadata = catalogue[key]
            self.assertEqual(metadata, definition["metadata"])
            self.assertEqual(
                metadata["record_count"],
                self._layer_feature_count(definition),
            )
            if definition.get("deferred"):
                self.assertEqual(definition["data"]["features"], [])
                deferred_path = ROOT / "docs" / "assets" / "layers" / f"{key}.geojson"
                self.assertTrue(deferred_path.exists())
                deferred = json.loads(deferred_path.read_text(encoding="utf-8"))
                self.assertEqual(len(deferred["features"]), metadata["record_count"])
            self.assertIn(metadata["quality"], {"A", "B", "C"})
            self.assertTrue(metadata["download_url"].startswith("https://"))
            self.assertTrue((ROOT / metadata["path"]).exists())

    def test_status_and_temporal_filter_metadata(self):
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
        filters = bundle["filters"]
        self.assertEqual(sum(filters["status_groups"].values()), 29098)
        self.assertEqual(
            filters["temporal"]["dated_records"]
            + filters["temporal"]["undated_records"],
            29098,
        )
        self.assertEqual(filters["temporal"]["minimum_year"], 1912)
        self.assertEqual(filters["temporal"]["maximum_year"], 2026)
        self.assertEqual(filters["temporal"]["dated_records"], 19203)
        self.assertEqual(filters["oil_spills"]["source_record_count"], 21124)
        self.assertEqual(filters["oil_spills"]["mapped_record_count"], 16326)
        self.assertEqual(
            filters["oil_spills"]["default_report_status"], "Confirmed"
        )

        valid_statuses = set(filters["status_groups"])
        for layer in bundle["layers"].values():
            for definition in layer["sublayers"].values():
                for feature in definition["data"]["features"]:
                    props = feature["properties"]
                    self.assertIn(props["_status_group"], valid_statuses)
                    if "_year" in props:
                        self.assertGreaterEqual(props["_year"], 1912)
                        self.assertLessEqual(props["_year"], 2026)
                        self.assertTrue(props["_year_label"])

    def test_static_api_is_reproducible_and_complete(self):
        builder = load_builder()
        bundle = builder.build_bundle()
        with tempfile.TemporaryDirectory() as directory:
            rebuilt_api = Path(directory) / "v1"
            builder.write_api_outputs(bundle, rebuilt_api)
            expected_files = {
                path.relative_to(rebuilt_api)
                for path in rebuilt_api.rglob("*")
                if path.is_file()
            }
            committed_files = {
                path.relative_to(API_DIR)
                for path in API_DIR.rglob("*")
                if path.is_file() and path.name != "README.md"
            }
            self.assertEqual(committed_files, expected_files)
            for relative_path in expected_files:
                self.assertEqual(
                    (API_DIR / relative_path).read_bytes(),
                    (rebuilt_api / relative_path).read_bytes(),
                    f"API artifact differs: {relative_path}",
                )

        manifest = json.loads((API_DIR / "manifest.json").read_text())
        self.assertEqual(manifest["api_version"], "v1")
        self.assertEqual(manifest["atlas_release"]["version"], "0.12.1")
        self.assertEqual(manifest["atlas_release"]["date"], "2026-08-05")
        self.assertEqual(
            manifest["atlas_release"]["title"],
            "Ports State Join, Deferred Bundle, UI Polish",
        )
        self.assertEqual(manifest["product"]["name"], "Infraxis Atlas — Nigeria")
        self.assertEqual(manifest["product"]["master_brand"], "Infraxis Atlas")
        self.assertEqual(manifest["product"]["premium_brand"], "Infraxis")
        self.assertEqual(manifest["product"]["role"], "open_datasource")
        self.assertEqual(manifest["product"]["country"], "Nigeria")
        self.assertEqual(len(manifest["layers"]), 27)
        self.assertEqual(manifest["endpoints"]["freshness"], "freshness.json")
        freshness = json.loads((API_DIR / "freshness.json").read_text())
        self.assertEqual(freshness["summary"]["dataset_count"], 27)
        self.assertEqual(
            freshness["summary"]["current"] + freshness["summary"]["due"],
            27,
        )
        oil_refresh = next(
            item for item in freshness["datasets"] if item["key"] == "oil_spills"
        )
        self.assertEqual(oil_refresh["cadence"], "monthly")
        compatibility = manifest["compatibility_endpoints"]["minigrids"]
        self.assertEqual(compatibility["record_count"], 93)
        self.assertEqual(
            set(compatibility["replacement_layers"]),
            {
                "community_minigrids",
                "captive_offgrid_systems",
                "standalone_systems",
                "interconnected_minigrids",
            },
        )
        for layer in manifest["layers"]:
            endpoint = API_DIR / layer["endpoint"]
            payload = json.loads(endpoint.read_text())
            self.assertEqual(payload["product"], manifest["product"])
            self.assertEqual(len(payload["features"]), layer["record_count"])


if __name__ == "__main__":
    unittest.main()
