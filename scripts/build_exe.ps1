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

$assetsDir = Join-Path $projectRoot "..\assets"
$iconPath = Join-Path $assetsDir "logo.ico"
python -m PyInstaller --clean --noconfirm --onefile --windowed --name MayanMiner `
    --icon "$iconPath" `
    --add-data "$assetsDir\logo.png;assets" `
    --hidden-import pystray._win32 `
    --distpath $outputDir --workpath $buildDir --specpath $buildDir ..\main.py

$exePath = Join-Path $outputDir "MayanMiner.exe"
if (Test-Path $exePath) {
    $hash = Get-FileHash -Path $exePath -Algorithm SHA256
    $hash.Hash | Out-File -Encoding ascii (Join-Path $outputDir "MayanMiner.exe.sha256")
    Write-Host "SHA256: $($hash.Hash)"
}

Write-Host "Build complete. Output file is located at $outputDir\MayanMiner.exe"
