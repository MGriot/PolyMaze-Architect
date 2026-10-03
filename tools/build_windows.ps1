<#
.SYNOPSIS
    Builds the Windows release: PyInstaller bundle, Inno Setup installer and portable zip.
.DESCRIPTION
    Same steps as the CI "desktop" job. Run from anywhere; paths are resolved from the repo root.
    Outputs (in dist\installer\):
        PolyMazeArchitect-Setup-<version>.exe
        PolyMazeArchitect-<version>-windows-x64-portable.zip
    Inno Setup 6 is optional locally (winget install JRSoftware.InnoSetup); without it only the zip is made.
.PARAMETER RequireInstaller
    Fail instead of skipping the installer when Inno Setup is missing (used by CI).
.PARAMETER Python
    Interpreter with requirements-dev.txt installed. Defaults to .venv\Scripts\python.exe, then python on PATH.
#>
param([string]$Python, [switch]$RequireInstaller)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $Python) {
    $venv = Join-Path $Root '.venv\Scripts\python.exe'
    $Python = if (Test-Path $venv) { $venv } else { 'python' }
}

$Version = (Select-String -Path 'src\polymaze\__init__.py' -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
Write-Host "PolyMaze Architect $Version" -ForegroundColor Cyan

& $Python -m PyInstaller packaging\pyinstaller\polymaze.spec --noconfirm
if ($LASTEXITCODE) { throw "PyInstaller failed ($LASTEXITCODE)" }

$OutDir = Join-Path $Root 'dist\installer'
New-Item -ItemType Directory -Force $OutDir | Out-Null

$Iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $Iscc) {
    $Iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
              "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if ($Iscc) {
    & $Iscc "/DAppVersion=$Version" packaging\windows\polymaze.iss
    if ($LASTEXITCODE) { throw "Inno Setup failed ($LASTEXITCODE)" }
} elseif ($RequireInstaller) {
    throw 'Inno Setup 6 (ISCC.exe) not found.'
} else {
    Write-Warning 'Inno Setup 6 not found; skipping the installer (winget install JRSoftware.InnoSetup).'
}

# Zip the folder itself so the archive extracts into PolyMazeArchitect\
$Zip = Join-Path $OutDir "PolyMazeArchitect-$Version-windows-x64-portable.zip"
Remove-Item $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path dist\PolyMazeArchitect -DestinationPath $Zip -CompressionLevel Optimal

Get-ChildItem $OutDir | Format-Table Name, @{ n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } } -AutoSize
