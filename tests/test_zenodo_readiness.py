import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_zenodo_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_zenodo_readiness", MODULE_PATH)
READINESS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(READINESS)


class ZenodoReadinessTests(unittest.TestCase):
    def test_rights_register_is_valid_and_truthfully_blocked(self):
        rows = READINESS.load_register(READINESS.DEFAULT_REGISTER)
        report = READINESS.readiness_report(rows)
        self.assertGreaterEqual(report["source_family_count"], 15)
        self.assertFalse(report["ready"])
        self.assertGreater(report["unresolved_count"], 0)
        unresolved_ids = {
            item["source_id"] for item in report["unresolved"]
        }
        self.assertIn("nigeria_se4all", unresolved_ids)
        self.assertIn("nosdra", unresolved_ids)
        self.assertIn("protected_planet", unresolved_ids)
        self.assertNotIn("ucdp", unresolved_ids)


if __name__ == "__main__":
    unittest.main()
