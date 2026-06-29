$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$outputDir = Join-Path $projectRoot "output"
$tempDist = "$env:TEMP\mayanminer_gui_dist"
$tempBuild = "$env:TEMP\mayanminer_gui_build"
$exePath = Join-Path $tempDist "MayanMiner.exe"
$innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$python = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

# Build the GUI executable first
if (-not (Test-Path $python)) {
    Write-Error "Python 3.12 not found. Please install Python 3.12 with tcl/tk support."
    exit 1
}

Write-Host "Building MayanMiner.exe with GUI support..."
Set-Location $projectRoot

# Clean and recreate temp build directories
if (Test-Path $tempDist) { Remove-Item -Recurse -Force $tempDist }
if (Test-Path $tempBuild) { Remove-Item -Recurse -Force $tempBuild }
New-Item -ItemType Directory -Path $tempDist -Force | Out-Null
New-Item -ItemType Directory -Path $tempBuild -Force | Out-Null

# Run PyInstaller
& $python -m PyInstaller --clean --noconfirm --onefile --windowed --name MayanMiner --distpath $tempDist --workpath $tempBuild --specpath $tempBuild main.py
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
