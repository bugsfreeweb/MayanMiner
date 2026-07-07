$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$outputDir = Join-Path $projectRoot "output"
$tempDist = "$env:TEMP\mayanminer_gui_dist"
$tempBuild = "$env:TEMP\mayanminer_gui_build"
$exePath = Join-Path $tempDist "MayanMiner.exe"
$innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Use whichever Python is on PATH instead of a hardcoded, machine-specific
# install location (the previous path only existed on one developer's PC).
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Error "Python was not found on PATH. Please install Python 3.10+ with tcl/tk support and ensure 'python' is on PATH."
    exit 1
}

Write-Host "Using Python at $python"
Write-Host "Building MayanMiner.exe with GUI support..."
Set-Location $projectRoot

& $python -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python dependencies."
    exit 1
}

# Clean and recreate temp build directories
if (Test-Path $tempDist) { Remove-Item -Recurse -Force $tempDist }
if (Test-Path $tempBuild) { Remove-Item -Recurse -Force $tempBuild }
New-Item -ItemType Directory -Path $tempDist -Force | Out-Null
New-Item -ItemType Directory -Path $tempBuild -Force | Out-Null

# Run PyInstaller - bundles assets/logo.png (for the in-app logo) and sets
# assets/logo.ico as the exe's own icon.
$assetsDir = Join-Path $projectRoot "assets"
$iconPath = Join-Path $assetsDir "logo.ico"
& $python -m PyInstaller --clean --noconfirm --onefile --windowed --name MayanMiner `
    --icon "$iconPath" `
    --add-data "$assetsDir\logo.png;assets" `
    --hidden-import pystray._win32 `
    --distpath $tempDist --workpath $tempBuild --specpath $tempBuild main.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed."
    exit 1
}

if (-not (Test-Path $exePath)) {
    Write-Error "Built executable not found at $exePath"
    exit 1
}

if (-not (Test-Path $innoCompiler)) {
    Write-Error "Inno Setup compiler not found at $innoCompiler. Install Inno Setup 6 and rerun this script."
    exit 1
}

# Ensure output directory exists
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }

# Copy the built executable to output directory
Copy-Item -Path $exePath -Destination "$outputDir\MayanMiner.exe" -Force

$installerScript = Join-Path $scriptRoot "MayanMinerInstaller.iss"
& $innoCompiler "/O$outputDir" "$installerScript"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Installer build failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "Installer build complete. Output is in $outputDir."
Write-Host "Installer file: $outputDir\MayanMinerSetup.exe"
