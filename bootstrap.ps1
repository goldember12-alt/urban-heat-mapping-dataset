# bootstrap.ps1
# Reusable project bootstrap for Python repos on Windows/PowerShell.
# Keeps venvs, temp files, and pip cache outside OneDrive-backed repos.

param(
    [string]$BasePython = "C:\Program Files\Python312\python.exe",
    [string]$VenvRoot = "$HOME\.venvs",
    [string]$TempRoot = "$HOME\.tmp",
    [string]$PipCacheRoot = "$HOME\.pip-cache",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Get-SafePipHelperPath {
    param([string]$TempRootPath)

    $HelperPath = Join-Path $TempRootPath "bootstrap_safe_pip.py"
    @'
import pathlib
import sys
import tempfile
import uuid


SAFE_TEMP_ROOT = pathlib.Path(sys.argv[1])
SAFE_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def safe_mkdtemp(suffix=None, prefix=None, dir=None):
    suffix = suffix or ""
    prefix = prefix or "tmp"
    parent = pathlib.Path(dir) if dir else SAFE_TEMP_ROOT
    parent.mkdir(parents=True, exist_ok=True)

    for _ in range(1000):
        candidate = parent / f"{prefix}{uuid.uuid4().hex}{suffix}"
        try:
            # In this sandbox, tempfile's default Windows 0o700 directory creation
            # can produce ACLs that block later writes. Use inherited ACLs instead.
            candidate.mkdir()
            return str(candidate)
        except FileExistsError:
            continue

    raise FileExistsError("Could not create a unique temporary directory")


tempfile.mkdtemp = safe_mkdtemp

mode = sys.argv[2]

if mode == "ensurepip":
    import ensurepip

    ensurepip.bootstrap(upgrade=True, default_pip=True, verbosity=1)
elif mode == "pip":
    from pip._internal.cli.main import main as pip_main

    raise SystemExit(pip_main(sys.argv[3:]))
else:
    raise SystemExit(f"Unsupported mode: {mode}")
'@ | Set-Content -LiteralPath $HelperPath -Encoding UTF8

    return $HelperPath
}

function Invoke-SafePipHelper {
    param(
        [string]$PythonExe,
        [string]$HelperPath,
        [string]$Mode,
        [string[]]$Arguments = @()
    )

    & $PythonExe $HelperPath $TempRoot $Mode @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Safe pip helper failed with exit code $LASTEXITCODE while running mode '$Mode'."
    }
}

$ProjectName = Split-Path -Leaf (Get-Location)
$VenvPath = Join-Path $VenvRoot $ProjectName
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$SafePipHelperPath = Join-Path $TempRoot "bootstrap_safe_pip.py"

Write-Step "Validating base Python"
if (-not (Test-Path -LiteralPath $BasePython)) {
    throw "Base Python not found at: $BasePython"
}

Write-Step "Ensuring shared directories exist"
Ensure-Directory -Path $VenvRoot
Ensure-Directory -Path $TempRoot
Ensure-Directory -Path $PipCacheRoot

$env:TEMP = $TempRoot
$env:TMP = $TempRoot
$env:PIP_CACHE_DIR = $PipCacheRoot
$SafePipHelperPath = Get-SafePipHelperPath -TempRootPath $TempRoot

Write-Step "Session environment configured"
Write-Host "TEMP=$env:TEMP"
Write-Host "TMP=$env:TMP"
Write-Host "PIP_CACHE_DIR=$env:PIP_CACHE_DIR"

Write-Step "Creating virtual environment if needed"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $BasePython -m venv $VenvPath
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Project virtual environment python not found at: $VenvPython"
}

Write-Step "Ensuring pip is available inside project venv"
Invoke-SafePipHelper -PythonExe $VenvPython -HelperPath $SafePipHelperPath -Mode "ensurepip"

Write-Step "Upgrading pip inside project venv"
Invoke-SafePipHelper -PythonExe $VenvPython -HelperPath $SafePipHelperPath -Mode "pip" -Arguments @(
    "install",
    "--upgrade",
    "pip"
)

if ((Test-Path -LiteralPath ".\requirements.txt") -and (-not $SkipInstall)) {
    Write-Step "Installing requirements.txt"
    Invoke-SafePipHelper -PythonExe $VenvPython -HelperPath $SafePipHelperPath -Mode "pip" -Arguments @(
        "install",
        "-r",
        ".\requirements.txt"
    )
}
elseif (-not (Test-Path -LiteralPath ".\requirements.txt")) {
    Write-Step "No requirements.txt found; skipping dependency install"
}
else {
    Write-Step "Skipping dependency install because -SkipInstall was provided"
}

Write-Step "Python verification"
& $VenvPython -c "import sys; print(sys.executable)"

Write-Step "Done"
Write-Host "Project venv: $VenvPath" -ForegroundColor Green
Write-Host "Project python: $VenvPython" -ForegroundColor Green
Write-Host ""
Write-Host "Use this interpreter for future commands in this repo:" -ForegroundColor Yellow
Write-Host "& '$VenvPython' ..." -ForegroundColor Yellow
