param(
    [ValidateSet('all', 'simple', 'A', 'B')]
    [string]$Scenario = 'all',
    [int]$Seed = 42,
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
$imageName = 'pttk-uav-ga:local'
$resultsPath = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Force -Path $resultsPath | Out-Null
if (-not $SkipBuild) {
    docker build -t $imageName $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
docker run --rm --network none --cpus 2 --memory 2g `
    --mount "type=bind,source=$resultsPath,target=/app/results" `
    $imageName python run_scenarios.py --scenario $Scenario --seed $Seed
exit $LASTEXITCODE
