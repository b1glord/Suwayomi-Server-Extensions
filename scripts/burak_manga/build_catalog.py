# Dosya Yolu: REPO_ROOT/scripts/burak_manga/build_catalog.py
# Amac: Kalici imzali uzantilardan Suwayomi uyumlu index.pb katalogu olusturur
# Modul - Python
# Version: 0.2.0
# Aciklama: Iki secili modulu paket metadata'sindan kataloglar; yayinlamaz
# Bagimli Oldugu Katman: Tool
"""Generate a Keiyoushi/Suwayomi extension catalog. Publishing is a separate step."""
import argparse
import gzip
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))
import index_pb2
from google.protobuf import json_format

OWNER = "b1glord"
REPOSITORY = "Suwayomi-Server-Extensions"
CATALOG_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/repo"
SOURCE_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/develop/burak-manga-extensions"
MODULES = ("ruyamanga", "merlinscans")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def checked_hex(value):
    value = value.strip().lower().replace(":", "")
    if not HEX.fullmatch(value):
        raise ValueError("Expected the real signing certificate's 64-character SHA-256 fingerprint")
    return value


def load_info(build_root, name):
    info_file = build_root / "src" / "tr" / name / "build" / "keiyoushi-source-info.json"
    info = json.loads(info_file.read_text(encoding="utf-8"))
    if info["module"] != f"tr.{name}" or info["packageName"] != f"eu.kanade.tachiyomi.extension.tr.{name}":
        raise ValueError(f"{name}: unexpected module or package name")
    if not isinstance(info.get("versionCode"), int) or info["versionCode"] <= 0:
        raise ValueError(f"{name}: invalid versionCode")
    if not isinstance(info.get("versionName"), str) or not info["versionName"]:
        raise ValueError(f"{name}: invalid versionName")
    if info.get("extensionLib") != "1.6" or info.get("contentWarning") not in (1, 2, 3):
        raise ValueError(f"{name}: unsupported metadata")
    sources = info.get("sources")
    if not isinstance(sources, list) or len(sources) != 1 or sources[0]["lang"] != "tr":
        raise ValueError(f"{name}: only a single Turkish source is supported")
    if not isinstance(sources[0].get("id"), int) or sources[0]["id"] <= 0:
        raise ValueError(f"{name}: missing source identifier")
    for suffix in ("apk", "jar"):
        outputs = sorted((info_file.parent / "outputs" / suffix / "release").glob(f"*.{suffix}"))
        if len(outputs) != 1:
            raise ValueError(f"{name}: expected exactly one {suffix} output")
    return info, info_file.parent


def build_catalog(build_root, destination, fingerprint, commit):
    fingerprint = checked_hex(fingerprint)
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("A full source commit SHA is required")
    build_root, destination = Path(build_root), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    previous = {}
    old_path = destination / "index.json"
    if old_path.exists():
        previous_index = json_format.Parse(old_path.read_text(encoding="utf-8"), index_pb2.Index())
        if previous_index.signingKey != fingerprint:
            raise ValueError("Refusing to rotate the repository signing key")
        previous = {e.packageName: e for e in previous_index.extensionList.extensions}
        if set(previous) - {f"eu.kanade.tachiyomi.extension.tr.{s}" for s in MODULES}:
            raise ValueError("Unexpected existing extension entries; refusing to remove them")

    extensions = []
    for name in MODULES:
        info, build_dir = load_info(build_root, name)
        package = info["packageName"]
        version = info["versionCode"]
        if package in previous and version < previous[package].versionCode:
            raise ValueError(f"{name}: versionCode downgrade forbidden")
        # Reusing a version for changed binary output breaks client update detection.
        if package in previous and version == previous[package].versionCode:
            raise ValueError(f"{name}: increment versionCode before republishing")

        resource_urls = {}
        for kind in ("apk", "jar"):
            source = next((build_dir / "outputs" / kind / "release").glob(f"*.{kind}"))
            target_name = f"{name}-v{version}-{commit[:12]}.{kind}"
            rel = f"{kind}/{target_name}"
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            resource_urls[kind] = f"{CATALOG_BASE}/{rel}"
        theme = info.get("theme")
        if theme not in ("madara", "initmanga"):
            raise ValueError(f"{name}: unsupported theme {theme}")
        icon_path = (f"lib-multisrc/{theme}/res/mipmap-xhdpi/ic_launcher.png"
                     if theme == "madara" else "core/src/main/res/mipmap-xhdpi/ic_launcher.png")
        icon_url = f"{SOURCE_BASE}/{icon_path}"
        source_infos = []
        for s in info["sources"]:
            source_infos.append(index_pb2.Source(
                id=int(s["id"]), name=s["name"], language=s["lang"],
                homeUrl=s["baseUrl"], mirrorUrls=s.get("mirrorUrls", []),
            ))
        extensions.append(index_pb2.Extension(
            name=info["name"],
            packageName=package,
            resources=index_pb2.Resources(
                apkUrl=resource_urls["apk"], jarUrl=resource_urls["jar"], iconUrl=icon_url,
            ),
            extensionLib=info["extensionLib"],
            versionCode=version,
            versionName=info["versionName"],
            contentWarning=info["contentWarning"],
            sources=source_infos,
        ))

    index = index_pb2.Index(
        name="Burak Manga Extensions",
        badgeLabel="BRK",
        signingKey=fingerprint,
        contact=index_pb2.Contact(website=f"https://github.com/{OWNER}/{REPOSITORY}"),
        extensionList=index_pb2.ExtensionList(extensions=extensions),
    )
    (destination / "index.pb").write_bytes(gzip.compress(index.SerializeToString(deterministic=True), mtime=0))
    (destination / "index.json").write_text(
        json_format.MessageToJson(index, preserving_proto_field_name=True) + "\n", encoding="utf-8",
    )
    (destination / "repo.json").write_text(
        json.dumps({"index_v2": f"{CATALOG_BASE}/index.pb",
                    "meta": {"name": "Burak Manga Extensions",
                             "website": f"https://github.com/{OWNER}/{REPOSITORY}",
                             "signingKeyFingerprint": fingerprint}}, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "BUILD_INFO.txt").write_text(f"source_commit={commit}\nmodules={','.join(MODULES)}\n", encoding="utf-8")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    result = build_catalog(args.build_root, args.out, args.fingerprint, args.commit)
    print(f"Generated {len(result.extensionList.extensions)} extension entries; no publication performed")


if __name__ == "__main__":
    main()
