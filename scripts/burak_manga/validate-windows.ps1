# Dosya Yolu: REPO_ROOT/scripts/burak_manga/validate-windows.ps1
# Amac: Windows'ta Python kurmadan kaynak testlerini Docker ile calistirir
# Modul - PowerShell
# Version: 0.1.1
# Aciklama: Salt-okunur repo mount, sirayla kaynak ve unittest kontratlari
# Bagimli Oldugu Katman: Tool
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Image = 'python:3.13-alpine'
$Mount = "type=bind,source=$RepoRoot,target=/workspace,readonly"

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'docs\burak-manga\sources.json') -PathType Leaf)) {
    throw 'SOURCE_REGISTRY_NOT_FOUND'
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'DOCKER_NOT_FOUND'
}

if ($WhatIfPreference) {
    Write-Host "What if: Validate repository $RepoRoot with $Image (read-only bind mount)."
    return
}

& docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) {
    throw 'DOCKER_DAEMON_UNAVAILABLE'
}

if ($PSCmdlet.ShouldProcess($RepoRoot, "Run offline source checks in $Image")) {
    Write-Host '=== SOURCE REGISTRY ===' -ForegroundColor Cyan
    & docker run --rm --pull=missing --mount $Mount --workdir /workspace $Image python scripts/burak_manga/validate_sources.py
    if ($LASTEXITCODE -ne 0) {
        throw 'SOURCE_VALIDATION_FAILED'
    }

    Write-Host '=== UNIT TESTS ===' -ForegroundColor Cyan
    & docker run --rm --pull=missing --mount $Mount --workdir /workspace $Image sh -ec "python -m pip install --disable-pip-version-check -q 'protobuf>=6,<7' && python -m unittest discover -s tests/burak_manga -v"
    if ($LASTEXITCODE -ne 0) {
        throw 'UNIT_TESTS_FAILED'
    }
    Write-Host 'SOURCE_AND_UNIT_TESTS_PASS' -ForegroundColor Green
}
