import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "catalog" / "asset-catalog-v0.1.json"

class AssetCatalogGuardrails(unittest.TestCase):
    def test_catalog_is_valid_json_and_has_required_fields(self):
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "0.1")
        required = set(data["required_fields"])
        ids = []
        for asset in data["assets"]:
            ids.append(asset["id"])
            self.assertTrue(required.issubset(asset.keys()), asset["id"])
            if asset["status"] == "not-created":
                self.assertIsNone(asset["source_path"])
                self.assertFalse(asset["validation"]["file_exists"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_charter_preserves_project_boundaries(self):
        charter = (ROOT / "docs" / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        self.assertIn("master APK unchanged", charter)
        self.assertIn("cancelled Godot prototype", charter)

if __name__ == "__main__":
    unittest.main()
