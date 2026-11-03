# Dosya Yolu: REPO_ROOT/tests/burak_manga/test_catalog.py
# Amac: Suwayomi katalog olusturma, surum ve imza sozlesmesini test eder
# Modul - Python
# Version: 0.2.0
# Aciklama: Fixture APK/JAR ile index.pb, kaynak bilgisi ve downgrade kontrolleri
# Bagimli Oldugu Katman: Testing
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "burak_manga"))
from build_catalog import build_catalog, checked_hex, index_pb2

SHA = "a" * 40
CERT = "b" * 64


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build_root = self.root / "source"
        self.output = self.root / "repo"
        for name, theme in (("ruyamanga", "madara"), ("merlinscans", "initmanga")):
            d = self.build_root / "src" / "tr" / name / "build"
            d.mkdir(parents=True)
            (d.parent / "build.gradle.kts").write_text("keiyoushi { versionCode = 101 }", encoding="utf-8")
            theme_dir = self.build_root / "lib-multisrc" / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            (theme_dir / "build.gradle.kts").write_text("theme", encoding="utf-8")
            (d / "keiyoushi-source-info.json").write_text(json.dumps({
                "module": f"tr.{name}",
                "theme": theme,
                "packageName": f"eu.kanade.tachiyomi.extension.tr.{name}",
                "name": name, "versionCode": 101, "versionName": "1.6.101",
                "extensionLib": "1.6", "contentWarning": 1,
                "sources": [{"id": 123, "lang": "tr", "name": name,
                             "baseUrl": "https://example.com", "mirrorUrls": []}],
            }), encoding="utf-8")
            for ext in ("apk", "jar"):
                p = d / "outputs" / ext / "release"
                p.mkdir(parents=True)
                (p / f"{name}.{ext}").write_bytes(b"fixture-not-a-real-package")

    def test_gzip_index_can_roundtrip(self):
        index = build_catalog(self.build_root, self.output, CERT, SHA)
        encoded = gzip.decompress((self.output / "index.pb").read_bytes())
        decoded = index_pb2.Index.FromString(encoded)
        self.assertEqual(len(decoded.extensionList.extensions), 2)
        self.assertEqual(decoded.signingKey, CERT)
        self.assertEqual(decoded.name, "Burak Manga Extensions")
        self.assertEqual(index, decoded)
        self.assertTrue(decoded.extensionList.extensions[0].resources.apkUrl.startswith(
            "https://raw.githubusercontent.com/b1glord/Suwayomi-Server-Extensions/repo/apk/"
        ))
        self.assertTrue((self.output / "repo.json").is_file())

    def test_repeated_publication_same_version_reuses_links(self):
        first = build_catalog(self.build_root, self.output, CERT, SHA)
        second = build_catalog(self.build_root, self.output, CERT, SHA)
        self.assertEqual(first, second)

    def test_changed_source_requires_version_bump(self):
        build_catalog(self.build_root, self.output, CERT, SHA)
        path = self.build_root / "src" / "tr" / "ruyamanga" / "build.gradle.kts"
        path.write_text("keiyoushi { versionCode = 102 }", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source changed"):
            build_catalog(self.build_root, self.output, CERT, SHA)

    def test_independent_version_update(self):
        before = build_catalog(self.build_root, self.output, CERT, SHA)
        d = self.build_root / "src" / "tr" / "ruyamanga" / "build"
        path = d / "keiyoushi-source-info.json"
        info = json.loads(path.read_text(encoding="utf-8"))
        info["versionCode"] += 1
        path.write_text(json.dumps(info), encoding="utf-8")
        source = d.parent / "build.gradle.kts"
        source.write_text("keiyoushi { versionCode = 102 }", encoding="utf-8")
        after = build_catalog(self.build_root, self.output, CERT, SHA)
        self.assertEqual(after.extensionList.extensions[1].resources.apkUrl,
                         before.extensionList.extensions[1].resources.apkUrl)
        self.assertNotEqual(after.extensionList.extensions[0].resources.apkUrl,
                            before.extensionList.extensions[0].resources.apkUrl)

    def test_signing_key_rotation_rejected(self):
        build_catalog(self.build_root, self.output, CERT, SHA)
        with self.assertRaisesRegex(ValueError, "signing key"):
            build_catalog(self.build_root, self.output, "c" * 64, SHA)

    def test_non_sha_fingerprint_rejected(self):
        with self.assertRaises(ValueError):
            checked_hex("temporary-debug-key")

    def test_missing_output_rejected(self):
        target = (self.build_root / "src" / "tr" / "merlinscans" / "build" /
                  "outputs" / "jar" / "release" / "merlinscans.jar")
        target.unlink()
        with self.assertRaisesRegex(ValueError, "jar output"):
            build_catalog(self.build_root, self.output, CERT, SHA)

    def test_source_package_confusion_rejected(self):
        path = (self.build_root / "src" / "tr" / "ruyamanga" / "build" /
                "keiyoushi-source-info.json")
        j = json.loads(path.read_text(encoding="utf-8"))
        j["packageName"] = "org.attacker.extension"
        path.write_text(json.dumps(j), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected module"):
            build_catalog(self.build_root, self.output, CERT, SHA)


if __name__ == "__main__":
    unittest.main()
