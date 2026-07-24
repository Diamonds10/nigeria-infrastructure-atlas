"""Release checks for the open distributed-energy contribution workflow."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "scripts"
    / "07_renewables"
    / "03_validate_distributed_energy_submission.py"
)
TEMPLATE_PATH = (
    ROOT
    / "data"
    / "contributions"
    / "07_renewables"
    / "distributed_energy_submission_template.csv"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_distributed_energy_submission", VALIDATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DistributedEnergyContributionTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_validator()
        with TEMPLATE_PATH.open(newline="", encoding="utf-8") as handle:
            self.columns = next(csv.reader(handle))

    def write_submission(self, row):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "submission.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.columns)
            writer.writeheader()
            writer.writerow(row)
        return directory, path

    def valid_row(self):
        return {
            "submission_id": "contrib-kano-example",
            "asset_name": "Example community solar mini-grid",
            "distributed_energy_class": "community_mini_grid",
            "asset_type": "mini_grid",
            "state": "Kano",
            "lga": "Ungogo",
            "community": "Example",
            "status": "operational",
            "technology": "solar_battery",
            "capacity_kw": "100",
            "customers_served": "250",
            "latitude": "12.01",
            "longitude": "8.51",
            "geocode_precision": "community",
            "developer": "Example developer",
            "owner_operator": "Example operator",
            "program_name": "",
            "source_name": "Example public evidence",
            "source_url": "https://example.org/evidence",
            "source_publication_date": "2026-07-20",
            "source_date_accessed": "2026-07-24",
            "evidence_level": "operator_record",
            "verification_status": "submitted",
            "submitter_name": "Example contributor",
            "submitter_contact": "",
            "notes": "Test fixture only.",
            "attestation": "true",
        }

    def test_template_schema_matches_validator(self):
        self.assertEqual(set(self.columns), self.validator.REQUIRED_COLUMNS)
        self.assertEqual(
            self.validator.validate_submission(TEMPLATE_PATH, allow_empty=True),
            [],
        )

    def test_valid_submission_passes(self):
        directory, path = self.write_submission(self.valid_row())
        self.addCleanup(directory.cleanup)
        self.assertEqual(self.validator.validate_submission(path), [])

    def test_invalid_submission_reports_evidence_and_location_errors(self):
        row = self.valid_row()
        row.update(
            {
                "state": "Not a state",
                "latitude": "40",
                "source_url": "private-note",
                "attestation": "false",
            }
        )
        directory, path = self.write_submission(row)
        self.addCleanup(directory.cleanup)
        errors = self.validator.validate_submission(path)
        self.assertTrue(any("canonical ADM1" in error for error in errors))
        self.assertTrue(any("latitude" in error for error in errors))
        self.assertTrue(any("HTTP(S)" in error for error in errors))
        self.assertTrue(any("attestation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
