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

    python scripts/burak_manga/validate_sources.py
    python -m unittest discover -s tests/burak_manga -v

Offline tests only compare the local registry with checked-out Gradle
source declarations. They do not run Android builds, site requests, or
extension download/install tests.

Before changing a Kotlin extension, read upstream CONTRIBUTING.md fully.
Lint every touched Android module. For example:

    ./gradlew :src:tr:ruyamanga:lintRelease :src:tr:merlinscans:lintRelease

Gradle requires a compatible JDK, Android SDK and dependencies. Never
report builds as passing unless they were actually executed. No signed APK,
private extension index or production release is created by this change.

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
