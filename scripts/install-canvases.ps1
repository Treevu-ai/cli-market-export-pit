# Instala los canvas del repo en la carpeta de proyectos de Cursor (Windows).
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceDir = Join-Path $RepoRoot "canvases"
$CanvasFiles = @(
    "lucuma-granola-us-opportunity.canvas.tsx",
    "golden-lucuma-crunch-bom.canvas.tsx"
)

function Resolve-TargetDir {
    if ($env:CURSOR_CANVASES_DIR) {
        return $env:CURSOR_CANVASES_DIR
    }

    $ProjectsRoot = Join-Path $env:USERPROFILE ".cursor\projects"
    if (-not (Test-Path $ProjectsRoot)) {
        throw "No existe $ProjectsRoot. Define la variable CURSOR_CANVASES_DIR."
    }

    $RepoName = Split-Path -Leaf $RepoRoot
    $Match = Get-ChildItem -Path $ProjectsRoot -Directory |
        Where-Object { $_.Name -like "*$RepoName*" } |
        Select-Object -First 1

    if (-not $Match) {
        $Match = Get-ChildItem -Path $ProjectsRoot -Directory |
            Where-Object { $_.Name -eq "workspace" } |
            Select-Object -First 1
    }

    if (-not $Match) {
        $Match = Get-ChildItem -Path $ProjectsRoot -Directory | Select-Object -First 1
    }

    if (-not $Match) {
        throw "No se encontro workspace en $ProjectsRoot"
    }

    return Join-Path $Match.FullName "canvases"
}

$TargetDir = Resolve-TargetDir
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

foreach ($File in $CanvasFiles) {
    $Src = Join-Path $SourceDir $File
    if (-not (Test-Path $Src)) {
        throw "Falta archivo fuente: $Src"
    }
    Copy-Item -Path $Src -Destination (Join-Path $TargetDir $File) -Force
    Write-Host "OK  $(Join-Path $TargetDir $File)"
}

Write-Host ""
Write-Host "Canvas instalados. En Cursor: Developer -> Reload Window"
