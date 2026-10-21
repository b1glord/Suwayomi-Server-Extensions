# Dosya Yolu: REPO_ROOT/scripts/burak_manga/validate_sources.py
# Amac: Manga uzanti kaynaklarinin depo metadata sozlesmesini kontrol eder
# Modul - Python
# Version: 0.1.0
# Aciklama: Agsiz kaynak konfig ve Gradle kaynak tanimlarini karsilastirir
# Bagimli Oldugu Katman: Tool
"""Offline Gradle source registry check; not a website compatibility test."""

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "docs" / "burak-manga" / "sources.json"
MODULE_PATTERN = re.compile(r"src/tr/[a-z0-9]+\Z")
SOURCE_URL_PATTERN = re.compile(r'^\s*baseUrl\s*=\s*"([^"\n]+)"', re.MULTILINE)
STATUSES = frozenset({"code_present_unverified", "requested_domain_differs"})


def canonical_https_url(value):
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    u = urlsplit(value)
    if (u.scheme != "https" or not u.hostname or u.username or u.password
            or u.port is not None or u.query or u.fragment or u.path not in {"", "/"}):
        raise ValueError("Only HTTPS base URLs with no path or credentials are supported")
    return u.hostname.lower()


def validate_registry(payload, repo_root=REPO_ROOT):
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Unsupported registry schema")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Registry must contain source entries")
    root = Path(repo_root).resolve()
    ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Source is not an object")
        ident = source.get("id")
        module = source.get("module")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9]*", ident):
            raise ValueError("Invalid source identifier")
        if ident in ids:
            raise ValueError(f"Duplicate source identifier: {ident}")
        ids.add(ident)
        if not isinstance(module, str) or MODULE_PATTERN.fullmatch(module) is None:
            raise ValueError(f"{ident}: unexpected module path")
        if module != f"src/tr/{ident}":
            raise ValueError(f"{ident}: module does not match identifier")
        if not isinstance(source.get("name"), str) or not source["name"].strip():
            raise ValueError(f"{ident}: invalid name")
        host = canonical_https_url(source.get("base_url"))
        requested_host = canonical_https_url(source.get("requested_url"))
        status = source.get("status")
        if status not in STATUSES:
            raise ValueError(f"{ident}: unknown status")
        if (host == requested_host) != (status == "code_present_unverified"):
            raise ValueError(f"{ident}: inconsistent requested domain status")
        path = (root / module / "build.gradle.kts").resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"{ident}: Gradle definition absent or outside repository")
        text = path.read_text(encoding="utf-8")
        matches = SOURCE_URL_PATTERN.findall(text)
        if len(matches) != 1 or matches[0].rstrip("/") != source["base_url"].rstrip("/"):
            raise ValueError(f"{ident}: Gradle baseUrl differs from registry")
    return len(ids)


def main():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    count = validate_registry(payload)
    print(f"PASS: {count} source definitions match registry; offline only")


if __name__ == "__main__":
    main()
