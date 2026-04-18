Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$sourceFile = Join-Path $scriptDir "slides_powerpoint.qmd"
$pptxOutput = Join-Path $scriptDir "urban_heat_transfer_presentation.pptx"
$buildOutput = Join-Path $scriptDir "build"

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

function Get-PandocExecutable {
    $cmd = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Quarto\bin\tools\pandoc.exe"),
        (Join-Path $env:ProgramFiles "Quarto\bin\tools\pandoc.exe")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Invoke-PandocRender {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PandocPath
    )

    & $PandocPath $sourceFile --from markdown --to pptx --output $pptxOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Pandoc render failed for PowerPoint output."
    }
}

$python = Get-PythonExecutable
$pandoc = Get-PandocExecutable

$missing = @()
if (-not $python) {
    $missing += "Python"
}
if (-not $pandoc) {
    $missing += "Pandoc"
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing required tool(s): {0}" -f ($missing -join ", "))
    exit 1
}

if (-not (Test-Path $sourceFile)) {
    Write-Error ("Source file not found: {0}" -f $sourceFile)
    exit 1
}

Push-Location $repoRoot
try {
    Write-Host ("Using Python: {0}" -f $python) -ForegroundColor Green
    Write-Host ("Using Pandoc: {0}" -f $pandoc) -ForegroundColor Green

    Write-Host ""
    Write-Host "Building slide visuals..." -ForegroundColor Cyan
    & $python -m src.run_presentation_deck --presentation-dir $scriptDir --output-dir $buildOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Slide visual build failed."
    }

    Write-Host ""
    Write-Host "Rendering PowerPoint..." -ForegroundColor Cyan
    Push-Location $scriptDir
    try {
        Invoke-PandocRender -PandocPath $pandoc
    }
    finally {
        Pop-Location
    }

    $pandocScratch = Join-Path $scriptDir "slides_powerpoint_files"
    if (Test-Path $pandocScratch) {
        Remove-Item -LiteralPath $pandocScratch -Recurse -Force
    }

    Write-Host ""
    Write-Host "Render complete." -ForegroundColor Green
    Write-Host ("PowerPoint: {0}" -f $pptxOutput)
    Write-Host ("Slide assets: {0}" -f $buildOutput)
}
finally {
    Pop-Location
}
