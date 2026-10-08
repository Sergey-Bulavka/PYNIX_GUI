param(
    [ValidateSet("Tests", "Smokes", "All")]
    [string]$Mode = "All"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Missing .venv. Create it with: py -m venv .venv"
}

function Invoke-Tests {
    & $Python -m pip install -e .
    & $Python -m pytest -q
}

function Invoke-Smokes {
    $Scripts = @(
        "examples\adv_01_commands_smoke.py",
        "examples\adv_02_tree_table_smoke.py",
        "examples\adv_03_drag_dock_smoke.py",
        "examples\adv_04_canvas_smoke.py",
        "examples\adv_05_editor_smoke.py",
        "examples\resources_smoke.py",
        "examples\showcase.py"
    )

    foreach ($Script in $Scripts) {
        Write-Host ""
        Write-Host "============================================================"
        Write-Host "Native smoke: $Script"
        Write-Host "Close the window after checking it to continue."
        Write-Host "============================================================"
        & $Python $Script
    }
}

switch ($Mode) {
    "Tests" { Invoke-Tests }
    "Smokes" { Invoke-Smokes }
    "All" {
        Invoke-Tests
        Invoke-Smokes
    }
}
