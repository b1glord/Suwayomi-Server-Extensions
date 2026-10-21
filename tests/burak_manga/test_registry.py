# Dosya Yolu: REPO_ROOT/tests/burak_manga/test_registry.py
# Amac: Kaynak uyum denetleyicisini gecici Gradle fixture'leriyle test eder
# Modul - Python
# Version: 0.1.0
# Aciklama: Metadata, yol, URL ve kaynak kaymasi icin cevrimdisi testler
# Bagimli Oldugu Katman: Testing
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "burak_manga"))
from validate_sources import REGISTRY, validate_registry


class RegistryContractTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for s in self.data["sources"]:
            path = self.root / s["module"] / "build.gradle.kts"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'keiyoushi {{\n    source {{\n        baseUrl = "{s["base_url"]}"\n    }}\n}}', encoding="utf-8")

    def test_repository_registry(self):
        self.assertEqual(validate_registry(json.loads(REGISTRY.read_text(encoding="utf-8"))), 2)

    def test_fixture(self):
        self.assertEqual(validate_registry(self.data, self.root), 2)

    def test_invalid_schema(self):
        bad = copy.deepcopy(self.data)
        bad["schema_version"] = 2
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)

    def test_duplicate_source(self):
        bad = copy.deepcopy(self.data)
        bad["sources"].append(copy.deepcopy(bad["sources"][0]))
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)

    def test_path_traversal_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["sources"][0]["module"] = "src/tr/../ruyamanga"
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)

    def test_source_url_drift(self):
        bad = copy.deepcopy(self.data)
        bad["sources"][0]["base_url"] = "https://new-domain.example"
        bad["sources"][0]["requested_url"] = "https://new-domain.example"
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)

    def test_wrong_domain_status(self):
        bad = copy.deepcopy(self.data)
        bad["sources"][1]["status"] = "code_present_unverified"
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)

    def test_insecure_url_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["sources"][0]["requested_url"] = "http://www.ruyamanga2.com"
        with self.assertRaises(ValueError):
            validate_registry(bad, self.root)


if __name__ == "__main__":
    unittest.main()
