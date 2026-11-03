# Dosya Yolu: REPO_ROOT/scripts/burak_manga/setup-signing-windows.ps1
# Amac: Kullanici imza dosyasini GitHub Actions Secrets'a guvenli sekilde aktarir
# Modul - PowerShell
# Version: 0.2.1
# Aciklama: Parola okumaz, dosyayi yazdirmaz, katalog yayinini kapali tutar
# Bagimli Oldugu Katman: Tool
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [string] $KeyFile = 'E:\Docker\Suwayomi-Secrets\burak-manga-signing.jks',
    [string] $Repository = 'b1glord/Suwayomi-Server-Extensions'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$SettingsUrl = "https://github.com/$Repository/settings/secrets/actions"

if (-not (Test-Path -LiteralPath $KeyFile -PathType Leaf)) {
    throw 'SIGNING_KEY_FILE_NOT_FOUND'
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GITHUB_CLI_NOT_FOUND: install GitHub CLI and run gh auth login'
}
& gh auth status 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw 'GITHUB_LOGIN_REQUIRED: run gh auth login'
}

Write-Host 'Use the PUBLIC SHA256 fingerprint printed by keytool -list -v.'
Write-Host 'Do NOT enter your keystore password here.'
$Fingerprint = ((Read-Host 'Public certificate SHA256 (colons allowed)') -replace ':','').Trim().ToLowerInvariant()
if ($Fingerprint -cnotmatch '^[0-9a-f]{64}$') {
    throw 'INVALID_CERTIFICATE_SHA256'
}

if ($WhatIfPreference) {
    Write-Host "What if: upload the selected keystore as a secret to $Repository."
    Write-Host 'What if: save public fingerprint, alias, and keep publishing disabled.'
    return
}

if ($PSCmdlet.ShouldProcess($Repository, 'Upload signing keystore and public identity; set publish gate to false')) {
    $Encoded = $null
    try {
        $Encoded = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($KeyFile))
        $Encoded | & gh secret set BURAK_MANGA_SIGNING_KEY_BASE64 --repo $Repository
        if ($LASTEXITCODE -ne 0) { throw 'KEY_UPLOAD_FAILED' }
    }
    finally {
        Remove-Variable Encoded -ErrorAction SilentlyContinue
    }

    & gh secret set BURAK_MANGA_KEY_ALIAS --repo $Repository --body 'burak-manga'
    if ($LASTEXITCODE -ne 0) { throw 'ALIAS_UPLOAD_FAILED' }

    & gh variable set BURAK_MANGA_SIGNING_CERT_SHA256 --repo $Repository --body $Fingerprint
    if ($LASTEXITCODE -ne 0) { throw 'FINGERPRINT_UPLOAD_FAILED' }

    & gh variable set BURAK_MANGA_PUBLISH_ENABLED --repo $Repository --body 'false'
    if ($LASTEXITCODE -ne 0) { throw 'PUBLISH_DISABLE_FAILED' }

    Write-Host 'GitHub keystore and certificate fingerprint were configured.' -ForegroundColor Green
    Write-Host 'Automatic publishing is DISABLED until you explicitly turn it on.' -ForegroundColor Yellow
    Write-Host "Next: $SettingsUrl"
    Write-Host 'Add the two PASSWORD secrets there (never paste them here):'
    Write-Host '  BURAK_MANGA_KEYSTORE_PASSWORD'
    Write-Host '  BURAK_MANGA_KEY_PASSWORD'
    Write-Host 'For PKCS12 these are normally the same password.'
    Write-Host 'Keep an offline backup of the signing key.'
    Write-Host ''
    Write-Host 'Verify configured secret NAMES only:'
    & gh secret list --repo $Repository
    if ($LASTEXITCODE -ne 0) { throw 'SECRET_LIST_FAILED' }
}
