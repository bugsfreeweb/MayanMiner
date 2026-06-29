$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$paths = @(
    "..\build",
    "..\__pycache__",
    "..\*.spec"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Removed: $path"
    }
}

Write-Host "Clean complete. The output folder remains intact."
