$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$DatabasePath = Join-Path $RepoRoot "data\verify_mvp.db"
$DataDir = Split-Path -Parent $DatabasePath

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Missing virtualenv Python at $Python. Run setup from README.md first."
}

function Invoke-CheckedPython {
    param([string[]]$CommandArgs)

    & $Python @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: $($CommandArgs -join ' ')"
    }
}

New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
if (Test-Path -LiteralPath $DatabasePath) {
    Remove-Item -LiteralPath $DatabasePath -Force
}

Push-Location $RepoRoot
try {
    Write-Host "Running lint..."
    Invoke-CheckedPython @("-m", "ruff", "check", "src", "tests", "scripts")

    Write-Host "Running type checks..."
    Invoke-CheckedPython @("-m", "mypy")

    Write-Host "Running tests..."
    Invoke-CheckedPython @("-m", "pytest", "-q")

    Write-Host "Checking installed dependencies..."
    Invoke-CheckedPython @("-m", "pip", "check")

    Write-Host "Auditing installed dependencies..."
    Invoke-CheckedPython @("-m", "pip_audit")

    Write-Host "Building package artifacts..."
    Invoke-CheckedPython @("-m", "build")
    Invoke-CheckedPython @("scripts/verify_distribution.py", "--dist", "dist")

    Write-Host "Inspecting source folder..."
    Invoke-CheckedPython @(
        "-m", "cm_dashboard.cli", "inspect-source", "--source", $RepoRoot
    )

    Write-Host "Rebuilding full verification database..."
    Invoke-CheckedPython @(
        "-m", "cm_dashboard.cli", "rebuild", "--source", $RepoRoot, "--db", $DatabasePath
    )

    Write-Host "Validating verification database..."
    Invoke-CheckedPython @(
        "-m", "cm_dashboard.cli", "validate", "--db", $DatabasePath
    )
}
finally {
    Pop-Location
}

Write-Host "MVP verification passed."
