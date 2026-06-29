$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$outputDir = Join-Path $projectRoot "..\output"
$buildDir = Join-Path $projectRoot "..\build"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
}

python -m pip install --disable-pip-version-check -r ..\requirements.txt
python -m PyInstaller --clean --noconfirm --onefile --windowed --name MayanMiner --distpath $outputDir --workpath $buildDir --specpath $buildDir ..\main.py

Write-Host "Build complete. Output file is located at $outputDir\MayanMiner.exe"
