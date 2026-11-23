<#
Run the NU workflow for model-1. Stops on the first error.

Steps:
  1. Check that repo-root .env is git-ignored.
  2. Run model-1 smoke on 20 NU items and STOP if invalid rate is above 10%.
  3. Run full NU for model-1 (resumable).
  4. Print summary of counts, invalid rates, and tokens.

Safety:
  - This script never prints .env contents or API keys.
  - Real runs contact providers and use API quota; use -DryRun or -Mock for no-network testing.
  - results/RUN_LOG.md is updated only by src.eval.run during real runs, never by this script.
#>

[CmdletBinding()]
param(
    [string]$ModelSlug = "model-1",
    [string]$Items = "data/processed/items_nu.jsonl",
    [string]$Models = "configs/models.yaml",
    [string]$Config = "configs/config.yaml",
    [switch]$DryRun,
    [switch]$Mock,
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RepoRoot
try {
    function Assert-LastExit([string]$Step) {
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed: $Step (exit code $LASTEXITCODE)"
        }
    }

    function Get-SummaryFromResults([string]$ResultsDir, [string]$Slug) {
        $py = @'
import json, sys
from pathlib import Path
results_dir = Path(sys.argv[1])
slug = sys.argv[2]
condition = sys.argv[3]
rows = []
model_dir = results_dir / slug
if model_dir.exists():
    for path in sorted(model_dir.rglob('*.jsonl')):
        with path.open(encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get('model_slug') == slug and row.get('condition') == condition:
                    rows.append(row)
# latest per key
latest = {}
for idx, row in enumerate(rows):
    key = (row.get('item_id'), row.get('condition'), row.get('repeat'))
    latest[key] = (idx, row)
latest_rows = [v[1] for v in sorted(latest.values(), key=lambda x: x[0])]
effective = latest_rows
effective_valid = sum(1 for r in effective if r.get('valid') is True)
unresolved_errors = sum(1 for r in effective if r.get('error') is not None)
errors = sum(1 for r in rows if r.get('error') is not None)
valid = sum(1 for r in rows if r.get('valid') is True)
invalid_rate = (len(effective) - effective_valid) / len(effective) if effective else 0.0
summary = {
    'model_slug': slug,
    'condition': condition,
    'rows': len(rows),
    'valid_rows': valid,
    'effective_rows': len(effective),
    'effective_valid_rows': effective_valid,
    'error_rows': errors,
    'unresolved_error_rows': unresolved_errors,
    'invalid_rate': invalid_rate,
    'tokens': 'unavailable (no token fields in results schema)'
}
print(json.dumps(summary, ensure_ascii=False))
'@
        $json = & python -c $py $ResultsDir $Slug "NU" 2>&1
        $text = ($json | Out-String)
        if ($LASTEXITCODE -ne 0) {
            Write-Host $text
            throw "Failed to compute summary from results in $ResultsDir"
        }
        return ($text | ConvertFrom-Json)
    }

    Write-Host "== run_nu.ps1 =="
    Write-Host "Repo root: $RepoRoot"
    Write-Host "Model: $ModelSlug"
    if ($DryRun) { Write-Host "Mode: dry-run (no network calls)" }
    elseif ($Mock) { Write-Host "Mode: mock (no network calls, temporary output)" }
    else { Write-Host "Mode: real run (will contact provider and use API quota)" }

    # 1) Check .env is git-ignored
    Write-Host "`n[1/4] Checking .env ignore status..."
    $ignored = $false
    & git check-ignore -q -- ".env"
    if ($LASTEXITCODE -eq 0) { $ignored = $true }
    if (-not $ignored) {
        throw ".env is not git-ignored. Add it to .gitignore before running."
    }
    Write-Host ".env is git-ignored: OK"

    $commonArgs = @("--model-slug", $ModelSlug, "--items", $Items, "--conditions", "NU", "--models", $Models, "--config", $Config)
    $smokeArgs = @() + $commonArgs + @("--max-items", "20", "--purpose", "smoke")
    $fullArgs = @() + $commonArgs + @("--purpose", "nu")

    $effectiveOutputDir = $null
    if ($Mock) {
        if ([string]::IsNullOrWhiteSpace($OutputDir)) {
            $effectiveOutputDir = Join-Path ([System.IO.Path]::GetTempPath()) ("run_nu_mock_" + [Guid]::NewGuid().ToString("N"))
        } else {
            $effectiveOutputDir = $OutputDir
        }
        New-Item -ItemType Directory -Force -Path $effectiveOutputDir | Out-Null
        $smokeArgs += @("--mock", "--output-dir", $effectiveOutputDir)
        $fullArgs += @("--mock", "--output-dir", $effectiveOutputDir)
        Write-Host "Mock output dir: $effectiveOutputDir"
    }

    # 2) Smoke test on 20 NU items
    Write-Host "`n[2/4] Smoke test (20 NU items)..."
    if ($DryRun) {
        & python -m src.eval.run @smokeArgs --dry-run
        Assert-LastExit "smoke dry-run"
        Write-Host "Smoke dry-run completed (no requests sent, invalid rate not available)."
    } else {
        $smokeJson = & python -m src.eval.run @smokeArgs 2>&1
        $smokeText = ($smokeJson | Out-String)
        Write-Host $smokeText
        Assert-LastExit "smoke run"
        $smoke = $smokeText | ConvertFrom-Json
        $invalidRate = [double]$smoke.invalid_rate
        Write-Host ("Smoke invalid_rate: {0:P2}" -f $invalidRate)
        if ($invalidRate -gt 0.10) {
            throw ("Smoke invalid rate {0:P2} is above 10%. Stopping before full NU run." -f $invalidRate)
        }
        Write-Host "Smoke invalid rate threshold OK (<= 10%)."
    }

    # 3) Full NU run (resumable)
    Write-Host "`n[3/4] Full NU run (resumable)..."
    if ($DryRun) {
        & python -m src.eval.run @fullArgs --dry-run
        Assert-LastExit "full NU dry-run"
        Write-Host "Full NU dry-run completed."
    } else {
        $fullJson = & python -m src.eval.run @fullArgs 2>&1
        $fullText = ($fullJson | Out-String)
        Write-Host $fullText
        Assert-LastExit "full NU run"
    }

    # 4) Summary
    Write-Host "`n[4/4] Summary (counts, invalid rates, tokens)..."
    if ($DryRun) {
        Write-Host "Dry-run mode: no result rows written. Counts/invalid rates/tokens unavailable."
        Write-Host "Tokens: unavailable (no token fields in results schema)."
    } elseif ($Mock) {
        $summary = Get-SummaryFromResults -ResultsDir $effectiveOutputDir -Slug $ModelSlug
        $summary | ConvertTo-Json -Depth 6
        Write-Host "Mock output retained at: $effectiveOutputDir"
    } else {
        $resultsDir = "results/raw"
        $summary = Get-SummaryFromResults -ResultsDir $resultsDir -Slug $ModelSlug
        $summary | ConvertTo-Json -Depth 6
    }

    Write-Host "`nDone."
    exit 0
}
finally {
    Pop-Location
}
