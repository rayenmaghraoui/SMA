# ============================================================
# run_tests.ps1 — Lance les tests et sauvegarde les resultats
# Usage : .\run_tests.ps1
# ============================================================

# Forcer l'encodage UTF-8 sans BOM pour le terminal et les fichiers
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding            = [System.Text.Encoding]::UTF8

$ReportFile = "backend\tests\test_results.txt"
$Timestamp  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Activer le venv si ce n'est pas deja fait
if (-not $env:VIRTUAL_ENV) {
    & ".\.venv\Scripts\Activate.ps1"
}

$PythonVer = (.\.venv\Scripts\python.exe --version 2>&1)
$PytestVer = (.\.venv\Scripts\python.exe -m pytest --version 2>&1)

# En-tete du rapport (ASCII pur pour eviter les problemes d'encodage)
$Header = @"
============================================================
 AI Business Consultant - Rapport de tests
 Date    : $Timestamp
 Python  : $PythonVer
 Pytest  : $PytestVer
============================================================

"@

# Ecrire l'en-tete sans BOM
[System.IO.File]::WriteAllText(
    (Resolve-Path "." | Join-Path -ChildPath $ReportFile),
    $Header,
    [System.Text.UTF8Encoding]::new($false)
)

# Lancer pytest avec un StreamWriter UTF-8 (sans BOM) pour eviter le probleme
# de detection "binary" dans VS Code cause par Tee-Object (qui ecrit en UTF-16LE)
$writer = [System.IO.StreamWriter]::new(
    (Resolve-Path "." | Join-Path -ChildPath $ReportFile),
    $true,   # append
    [System.Text.UTF8Encoding]::new($false)  # UTF-8 sans BOM
)
try {
    .\.venv\Scripts\python.exe -m pytest backend/tests/ -v --tb=short --color=no 2>&1 |
        ForEach-Object {
            Write-Host $_
            $writer.WriteLine($_)
        }
} finally {
    $writer.Close()
}

Write-Host ""
Write-Host "Rapport sauvegarde dans : $ReportFile" -ForegroundColor Green
