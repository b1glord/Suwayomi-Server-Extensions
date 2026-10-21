<!--
Dosya Yolu: REPO_ROOT/docs/burak-manga/AGENTS.md
Amac: Yerel manga uzanti gelistirmesi icin ek proje kurallari
Modul - Markdown
Version: 0.1.0
Aciklama: Burak standardi referansi, upstream kurallarini koruyan kapsam
Bagimli Oldugu Katman: Documentation
-->
# Burak manga extension integration

Root AGENTS.md and upstream CONTRIBUTING.md remain authoritative for code conventions.
Central engineering standard: BURAK DEV STANDARD v3.0.0 (pinned commit):
https://github.com/TurkuazSoft/DevStandards/tree/257d0470460cdfce14f11da039ee2aa3a500755b

- Upstream: keiyoushi/extensions-source, branch main.
- Fork: b1glord/Suwayomi-Server-Extensions, branch develop/burak-manga-extensions.
- Preserve upstream architecture; isolate each extension change to its module.
- Never commit downloaded manga, signing keys, credentials, or private content.
- Treat remote HTML and third-party sources as untrusted. Respect permissions and rate limits, do not bypass access controls or DRM.
- Run focused local tests before GitHub CI; separately verify changed extension Gradle lint and real runtime. Do not claim success on tests not run.
- Never merge to main or publish APK/release without user approval.
