<!--
Dosya Yolu: REPO_ROOT/docs/burak-manga/README.md
Amac: Windows extension gelistirme clone ve test adimlarini belgelemek
Modul - Markdown
Version: 0.1.0
Aciklama: Sparse checkout, upstream takibi ve kaynak test kapsami
Bagimli Oldugu Katman: Documentation
-->
# Suwayomi Manga Extensions - local development

This fork follows Keiyoushi extensions-source, not the Suwayomi server.
A Git clone contains Kotlin/Gradle source code only. It does not install
extensions into the running Suwayomi container.

Read [upstream rules](../../AGENTS.md), [CONTRIBUTING](../../CONTRIBUTING.md)
and this project's [additional rules](AGENTS.md).

## Local Windows clone (user-chosen E: drive)

Run in PowerShell after the branch has been created on GitHub. Existing
Suwayomi-Server installations are left untouched.

    $ErrorActionPreference = 'Stop'
    $Root = 'E:\Docker'
    $Repo = Join-Path $Root 'Suwayomi-Server-Extensions'
    $Url = 'https://github.com/b1glord/Suwayomi-Server-Extensions.git'
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'E_DRIVE_ROOT_NOT_FOUND' }
    if (Test-Path -LiteralPath $Repo) { throw 'EXTENSIONS_TARGET_EXISTS_CHECK_MANUALLY' }
    git clone --filter=blob:none --sparse --branch develop/burak-manga-extensions --single-branch $Url $Repo
    if ($LASTEXITCODE -ne 0) { throw 'CLONE_FAILED' }
    git -C $Repo sparse-checkout set --cone --sparse-index common compiler core gradle lib lib-multisrc src/tr/ruyamanga src/tr/merlinscans docs/burak-manga scripts/burak_manga tests/burak_manga
    if ($LASTEXITCODE -ne 0) { throw 'SPARSE_CHECKOUT_FAILED' }
    git -C $Repo remote add upstream 'https://github.com/keiyoushi/extensions-source.git'
    if ($LASTEXITCODE -ne 0) { throw 'UPSTREAM_REMOTE_FAILED' }
    git -C $Repo status --short --branch

The path above is a user-selected checkout destination, not a hardcoded
runtime path. Existing checkouts are never reset or deleted automatically.

## Offline tests

On Windows, no local Python installation is required if Docker Desktop is
already running. From any directory, run the helper below (replace the
checkout folder if you chose another location):

    & 'E:\Docker\Suwayomi-Server-Extensions\scripts\burak_manga\validate-windows.ps1'

The helper derives its repository root from its own location. It runs
both checks inside the official python:3.13-alpine Docker image with the
checkout mounted read-only. The first run downloads the Python image;
later runs reuse it. It will not modify or restart the Suwayomi server.
Use `-WhatIf` to inspect the planned operation without invoking Docker.

You can still run tests directly if a local Python interpreter is installed:

    python scripts/burak_manga/validate_sources.py
    python -m unittest discover -s tests/burak_manga -v

Offline tests only compare the local registry with checked-out Gradle
source declarations. They do not run Android builds, site requests, or
extension download/install tests.

Before changing a Kotlin extension, read upstream CONTRIBUTING.md fully.
Lint every touched Android module. For example:

    ./gradlew :src:tr:ruyamanga:lintRelease :src:tr:merlinscans:lintRelease

For real compilation, a separate GitHub Actions workflow builds and lints
only the two selected extensions on a hosted Android-compatible runner:
[Targeted Gradle](../../.github/workflows/burak_manga_build.yml).
It runs release APK assembly, lint, Android APK signature verification and
stages two temporary debug-signed APKs as a GitHub Actions artifact named
`burak-manga-test-apks` (3-day retention). This uses the Keiyoushi build
plugin's fallback debug signing key, not a managed production/release key.

To inspect the files: open the targeted Gradle workflow run in GitHub,
find `burak-manga-test-apks` under Artifacts, download the ZIP and extract
the two APKs plus `SHA256SUMS.txt` and `BUILD_INFO.txt`. On Windows,
verify downloaded file hashes with `Get-FileHash -Algorithm SHA256`.

Only with explicit manual approval, use Suwayomi WebUI's
Browse > Extensions > Add/Install from file feature to try one of the APKs.
The UI location depends on the installed WebUI version. Do not uninstall
or replace an existing official extension simply to try a debug-signed APK:
the signing key differs and automatic upgrade paths may not work.
Back up Suwayomi's persistent data before manual extension changes.

The artifact does **not** install the APK, publish an extension repository
index, provide a stable signing identity, or prove live manga/chapter parsing.
Never confuse a temporary artifact with a GitHub Release.

Gradle requires a compatible JDK, Android SDK and dependencies. Never
report builds as passing unless they were actually executed.
No production-signed APK, private extension index or production release is
created by this change.

## Initial sources

- Rüya Manga code currently points at https://www.ruyamanga2.com.
- Merlin Scans code currently points at https://merlintoon.com, whereas
  the requested site is https://merlinscans.org.
- Both entries are unverified for live chapter fetching, downloading
  rights and Suwayomi runtime compatibility.

See [source metadata](sources.json).

## Other repository

Server-side Docker integration:
https://github.com/b1glord/Suwayomi-Server/tree/develop/burak-manga

Future source changes belong in focused PRs in this extension fork,
not copied into the server repository.

## Automatic personal extension catalog

The project's core goal is a single URL that Suwayomi can refresh for
signed extension updates. Intended catalog URL, AFTER initial publication:

    https://raw.githubusercontent.com/b1glord/Suwayomi-Server-Extensions/repo/index.pb

The repo branch is reserved now, but the index is not yet published:
a permanent signing key must be configured and publishing enabled by
the owner first. Full setup, backup, activation and rollback:
[PUBLISHING.md](PUBLISHING.md). Temporary review APKs are not published.
