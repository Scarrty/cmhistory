$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$DatabasePath = Join-Path $RepoRoot "data\verify_mvp.db"
$DataDir = Split-Path -Parent $DatabasePath

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Missing virtualenv Python at $Python. Run setup from README.md first."
}

New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
if (Test-Path -LiteralPath $DatabasePath) {
    Remove-Item -LiteralPath $DatabasePath -Force
}

Push-Location $RepoRoot
try {
    Write-Host "Running tests..."
    & $Python -m pytest

    Write-Host "Running lint..."
    & $Python -m ruff check src tests

    Write-Host "Inspecting source folder..."
    & $Python -m cm_dashboard.cli inspect-source --source $RepoRoot

    Write-Host "Importing full source folder into verification database..."
    & $Python -m cm_dashboard.cli import --source $RepoRoot --db $DatabasePath

    Write-Host "Validating verification database..."
    & $Python -m cm_dashboard.cli validate --db $DatabasePath
}
finally {
    Pop-Location
}

Write-Host "MVP verification passed."
