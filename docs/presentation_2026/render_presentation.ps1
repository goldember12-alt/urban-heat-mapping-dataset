Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$pptxOutput = Join-Path $scriptDir "urban_heat_transfer_presentation.pptx"

function Get-PythonExecutable {
    $candidates = @(
        (Join-Path $repoRoot ".venv\Scripts\python.exe"),
        "C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    return $null
}

$python = Get-PythonExecutable

$missing = @()
if (-not $python) {
    $missing += "Python"
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing required tool(s): {0}" -f ($missing -join ", "))
    exit 1
}

Push-Location $repoRoot
try {
    Write-Host ("Using Python: {0}" -f $python) -ForegroundColor Green

    Write-Host ""
    Write-Host "Building editable PowerPoint..." -ForegroundColor Cyan
    & $python -m src.run_editable_presentation --output-path $pptxOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Editable PowerPoint build failed."
    }

    Write-Host ""
    Write-Host "Render complete." -ForegroundColor Green
    Write-Host ("PowerPoint: {0}" -f $pptxOutput)
}
finally {
    Pop-Location
}
