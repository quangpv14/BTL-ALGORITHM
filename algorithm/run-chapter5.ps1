param([int]$Seed = 42, [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$imageName = 'pttk-uav-ga:chapter5'
$resultsPath = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Force -Path $resultsPath | Out-Null
if (-not $SkipBuild) {
    docker build -t $imageName $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
# V1's three campaigns are retained from the earlier run, as requested.
foreach ($variant in @('V2', 'V3', 'V4')) {
    foreach ($scenario in @('simple', 'A', 'B')) {
        $reportPath = Join-Path $resultsPath "chapter5/$variant/$scenario.json"
        if (Test-Path -LiteralPath $reportPath) {
            $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
            $expectedRuns = if ($scenario -eq 'simple') { 1 } else { 20 }
            if ($report.status -eq 'completed' -and $report.runs.Count -eq $expectedRuns -and
                $report.seed -eq $Seed -and $report.profile -eq 'chapter5' -and $report.variant -eq $variant) {
                Write-Output "Skip $scenario/${variant}: completed results already exist."
                continue
            }
        }
        docker run --rm --network none --cpus 2 --memory 2g `
            --mount "type=bind,source=$resultsPath,target=/app/results" `
            $imageName python run_scenarios.py --scenario $scenario --variant $variant `
            --profile chapter5 --seed $Seed --output "results/chapter5/$variant"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}
docker run --rm --network none --mount "type=bind,source=$resultsPath,target=/app/results" `
    $imageName python summarize_chapter5.py
exit $LASTEXITCODE
