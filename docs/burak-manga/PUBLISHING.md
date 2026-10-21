<!--
Dosya Yolu: REPO_ROOT/docs/burak-manga/PUBLISHING.md
Amac: Tek seferlik imza kurulumu ve otomatik Suwayomi uzanti katalogu
Modul - Markdown
Version: 0.2.0
Aciklama: Anahtar guvenligi, GitHub secrets, otomatik guncelleme ve geri alma
Bagimli Oldugu Katman: Documentation
-->
# Burak Manga Extensions — automatic personal catalog

This is the **primary project feature**. Suwayomi reads a fixed
Keiyoushi-compatible index and discovers extension versions without manual
APK downloads. A code checkout by itself is NOT an extension repository.

## Fixed catalog URL

After the first successful signed publication:

    https://raw.githubusercontent.com/b1glord/Suwayomi-Server-Extensions/repo/index.pb

The GitHub repo branch is **generated publication output**. The
develop/burak-manga-extensions branch contains editable extension source.
Do not merge the repo branch into the source branch or force-push it.
The main branch remains upstream-aligned and untouched.

## One-time owner action: create a permanent signing key

Key creation is intentionally **not automated**. Changing signing identities
prevents safe extension upgrades. Keep the keystore and passwords private.
Never paste them into chats, commits, issues, PRs or screenshots.

On Windows with Docker Desktop, create a directory **outside both repos**,
for example E:\Docker\Suwayomi-Secrets (user-chosen path).

    $KeyFolder = 'E:\Docker\Suwayomi-Secrets'
    New-Item -ItemType Directory -Path $KeyFolder -Force | Out-Null
    docker run --rm -it --mount "type=bind,source=$KeyFolder,target=/keys" eclipse-temurin:25-jdk keytool -genkeypair -alias burak-manga -keyalg RSA -keysize 3072 -validity 3650 -storetype PKCS12 -keystore /keys/burak-manga-signing.jks -dname 'CN=Burak Manga Extensions'

Choose a strong password and keep an offline backup. PKCS12 normally uses
the same password for both keystore and key. To view the PUBLIC certificate
SHA-256 fingerprint, run:

    docker run --rm -it --mount "type=bind,source=$KeyFolder,target=/keys,readonly" eclipse-temurin:25-jdk keytool -list -v -keystore /keys/burak-manga-signing.jks -alias burak-manga

Copy the displayed certificate SHA256 digest and remove colons, resulting
in a 64-character hexadecimal public fingerprint.

In fork Settings > Secrets and variables > Actions, configure:

| Type | Key | Value |
|---|---|---|
| Repository secret | BURAK_MANGA_SIGNING_KEY_BASE64 | Base64 of complete PKCS12 keystore file |
| Repository secret | BURAK_MANGA_KEY_ALIAS | burak-manga |
| Repository secret | BURAK_MANGA_KEYSTORE_PASSWORD | Keystore password |
| Repository secret | BURAK_MANGA_KEY_PASSWORD | Private key password (same for PKCS12) |
| Repository variable | BURAK_MANGA_SIGNING_CERT_SHA256 | Public 64-character fingerprint |
| Repository variable | BURAK_MANGA_PUBLISH_ENABLED | true; set this LAST |

If GitHub CLI (gh) is installed and authenticated, securely upload the
keystore file without printing the base64 in the terminal:

    $KeyFile = Join-Path $KeyFolder 'burak-manga-signing.jks'
    [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($KeyFile)) | gh secret set BURAK_MANGA_SIGNING_KEY_BASE64 -R b1glord/Suwayomi-Server-Extensions

Use the GitHub web UI or interactive secret input for passwords. Do not
put secret values into shell history, CI variables or Git commits. Keep
an offline backup of the signing key: losing it breaks update continuity.

## First publish and later automatic updates

The publisher runs on pushes to develop/burak-manga-extensions **only
after** the owner sets BURAK_MANGA_PUBLISH_ENABLED=true. Neither PR
checks nor debug-signed temporary APK artifact jobs can publish.

After setting the secrets and variable, explicitly activate the first
publication by making an empty commit from a clean, up-to-date checkout:

    git -C 'E:\Docker\Suwayomi-Server-Extensions' status --short --branch
    git -C 'E:\Docker\Suwayomi-Server-Extensions' commit --allow-empty -m 'chore: activate signed extension catalog'
    git -C 'E:\Docker\Suwayomi-Server-Extensions' push origin develop/burak-manga-extensions

An empty commit does not modify source files but triggers the publisher.
It builds and lints both modules using your permanent private key, checks
both APK certificate digests, generates index.pb, index.json, repo.json,
signed versioned APK/JAR files and SHA-256 checksums on branch repo.
Publishing fails safely if keys mismatch or a version is reused/downgraded.

After this GitHub Action has **successfully completed**, add the fixed index
URL above in Suwayomi's extension repository settings and refresh.
Future source changes to the development branch are automatically built
and published to the SAME URL.

The CI may compile both selected modules, but the publisher compares each
module's source/theme digest against the previous catalog. It retains the
existing signed APK/JAR URL when that module has not changed, so **Rüya Manga
and Merlin Scans update independently**. When a module changes, increment
its versionCode before pushing. Source changes with unchanged versionCode,
certificate rotations and version downgrades are rejected. Shared libraries
or build logic changes can affect both APKs: bump both version codes in
that case; broader shared-dependency checks remain a review responsibility.

Pause distribution at any time by setting BURAK_MANGA_PUBLISH_ENABLED=false.
Use only sources and content for which you have necessary permission.

## Runtime checks, migrations, rollback

Passing Gradle lint does not prove real site parsing or permitted content
retrieval. Validate search, chapter lists and page access separately.

Official upstream extensions can have different signing certificates;
do not overwrite existing extensions without a backup and migration plan.
Do not rotate the permanent certificate or change source IDs casually.

The repo branch retains prior versioned binaries. For a bad update, disable
publishing and create a new forward correction commit; never force-push.
Clients may require recovery steps; publishing an older version is not an
automatic rollback.
