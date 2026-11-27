<#
Run the NU workflow for model-1. Stops on the first error.

Steps:
  0. Groq model-existence check via official list-models endpoint (prints only HTTP status and presence booleans).
  1. Check that repo-root .env is git-ignored.
  2. Run model-1 smoke on 20 NU items to a temporary folder outside results/raw and STOP if smoke criteria fail.
  3. Run full NU for model-1 into results/raw (resumable).
  4. Print summary of counts, invalid rates, and tokens.

Safety:
  - This script never prints .env contents or API keys.
  - Real runs contact providers and use API quota; use -DryRun or -Mock for no-network testing.
  - results/RUN_LOG.md is updated only by src.eval.run during real runs, never by this script.
  - Smoke real-run rows are written outside results/raw so failed smoke rows never enter final data.
#>

[CmdletBinding()]
param(
    [string]$ModelSlug = "model-1",
    [string]$Items = "data/processed/items_nu.jsonl",
    [string]$Models = "configs/models.yaml",
    [string]$Config = "configs/config.yaml",
    [switch]$DryRun,
    [switch]$Mock,
    [string]$OutputDir,
    [string]$SmokeOutputDir
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

    function Get-ConfiguredModelString([string]$ModelsPath, [string]$Slug) {
        $py = @"
import json, sys, yaml
from pathlib import Path
models_path = Path(sys.argv[1])
slug = sys.argv[2]
data = yaml.safe_load(models_path.read_text(encoding='utf-8')) or {}
for entry in data.get('evaluated_models') or []:
    if isinstance(entry, dict) and entry.get('slug') == slug:
        value = entry.get('model_string')
        print(json.dumps(value))
        raise SystemExit(0)
raise SystemExit(2)
"@
        $out = & python -c $py $ModelsPath $Slug 2>&1
        $text = ($out | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) {
            Write-Host $text
            throw "Could not read configured model_string for '$Slug' from $ModelsPath"
        }
        return ($text | ConvertFrom-Json)
    }

    function Get-SummaryFromResults([string]$ResultsDir, [string]$Slug, [string]$Condition = "NU") {
        $py = @"
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
latest = {}
for idx, row in enumerate(rows):
    key = (row.get('item_id'), row.get('condition'), row.get('repeat'))
    latest[key] = (idx, row)
latest_rows = [v[1] for v in sorted(latest.values(), key=lambda x: x[0])]
effective_valid = sum(1 for r in latest_rows if r.get('valid') is True)
unresolved_errors = sum(1 for r in latest_rows if r.get('error') is not None)
errors = sum(1 for r in rows if r.get('error') is not None)
valid = sum(1 for r in rows if r.get('valid') is True)
invalid_rate = (len(latest_rows) - effective_valid) / len(latest_rows) if latest_rows else 0.0
summary = {
    'model_slug': slug,
    'condition': condition,
    'rows': len(rows),
    'valid_rows': valid,
    'effective_rows': len(latest_rows),
    'effective_valid_rows': effective_valid,
    'error_rows': errors,
    'unresolved_error_rows': unresolved_errors,
    'invalid_rate': invalid_rate,
    'tokens': 'unavailable (no token fields in results schema)'
}
print(json.dumps(summary, ensure_ascii=False))
"@
        $json = & python -c $py $ResultsDir $Slug $Condition 2>&1
        $text = ($json | Out-String)
        if ($LASTEXITCODE -ne 0) {
            Write-Host $text
            throw "Failed to compute summary from results in $ResultsDir"
        }
        return ($text | ConvertFrom-Json)
    }

    function Get-SmokeEvaluation([string]$ResultsDir, [string]$Slug, [string]$ConfiguredModelString, [string]$RunDate, [int]$ExpectedRequests = 20) {
        $py = @"
import json, sys
from pathlib import Path
results_dir = Path(sys.argv[1])
slug = sys.argv[2]
configured = sys.argv[3]
run_date = sys.argv[4]
expected_requests = int(sys.argv[5]) if len(sys.argv) > 5 else 20
path = results_dir / slug / f'{run_date}_smoke_r1.jsonl'
rows = []
if path.exists():
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
latest = {}
for idx, row in enumerate(rows):
    key = (row.get('item_id'), row.get('condition'), row.get('repeat'))
    latest[key] = (idx, row)
effective = [v[1] for v in sorted(latest.values(), key=lambda x: x[0])]
error_rows = [r for r in effective if r.get('error') is not None]
answered = [r for r in effective if r.get('error') is None]
invalid_answer_rows = [r for r in answered if r.get('valid') is not True]
empty = [r for r in answered if not isinstance(r.get('raw_output'), str) or r.get('raw_output','').strip() == '']
mismatch = [r for r in answered if r.get('model_string') != configured]
invalid_answer_rate = (len(invalid_answer_rows) / len(answered)) if answered else 1.0

def sample(rows_in, n=3):
    out = []
    for r in rows_in[:n]:
        out.append({
            'item_id': r.get('item_id'),
            'raw_output': r.get('raw_output'),
            'parsed_answer': r.get('parsed_answer'),
            'valid': r.get('valid'),
            'error': r.get('error'),
            'model_string': r.get('model_string'),
        })
    return out

problem_rows = []
seen = set()
for group in (error_rows, invalid_answer_rows, empty, mismatch):
    for r in group:
        rid = (r.get('item_id'), r.get('repeat'), r.get('condition'))
        if rid not in seen:
            seen.add(rid)
            problem_rows.append(r)
if not problem_rows:
    problem_rows = effective
passed = (
    len(effective) == expected_requests
    and len(error_rows) == 0
    and len(answered) == expected_requests
    and invalid_answer_rate <= 0.05
    and len(empty) == 0
    and len(mismatch) == 0
)
result = {
    'path': str(path),
    'effective_rows': len(effective),
    'answered_requests': len(answered),
    'error_count': len(error_rows),
    'invalid_answer_count': len(invalid_answer_rows),
    'invalid_answer_rate': invalid_answer_rate,
    'empty_answers': len(empty),
    'model_string_mismatches': len(mismatch),
    'recorded_model_strings': sorted({str(r.get('model_string')) for r in answered}),
    'configured_model_string': configured,
    'pass': passed,
    'sample_raw_outputs': sample(problem_rows, 3),
}
print(json.dumps(result, ensure_ascii=False))
"@
        $json = & python -c $py $ResultsDir $Slug $ConfiguredModelString $RunDate $ExpectedRequests 2>&1
        $text = ($json | Out-String)
        if ($LASTEXITCODE -ne 0) {
            Write-Host $text
            throw "Failed to evaluate smoke results in $ResultsDir"
        }
        return ($text | ConvertFrom-Json)
    }


    Write-Host "== run_nu.ps1 =="
    Write-Host "Repo root: $RepoRoot"
    Write-Host "Model: $ModelSlug"
    if ($DryRun) { Write-Host "Mode: dry-run (no network calls)" }
    elseif ($Mock) { Write-Host "Mode: mock (no network calls, temporary output)" }
    else { Write-Host "Mode: real run (will contact provider and use API quota)" }

    $runDate = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
    $configuredModelString = Get-ConfiguredModelString -ModelsPath $Models -Slug $ModelSlug
    $expectedRecordedModelString = $configuredModelString
    if ($Mock) { $expectedRecordedModelString = "mock" }
    Write-Host "Configured model_string: $configuredModelString"
    if ($Mock) { Write-Host "Expected recorded model_string in mock mode: mock" }

    # 0) Groq model-existence check
    Write-Host "`n[0/4] Groq model-existence check (HTTP status and presence only)..."
    $groqCheckArgs = @("scripts/check_groq_models.py", "--models", $Models)
    if ($DryRun -or $Mock) {
        $groqCheckArgs += "--mock"
    }
    $groqOut = & python @groqCheckArgs 2>&1
    $groqText = ($groqOut | Out-String).Trim()
    Write-Host $groqText
    Assert-LastExit "Groq model-existence check"
    $groq = $groqText | ConvertFrom-Json
    if (-not $groq.model_1_present -or -not $groq.helper_present) {
        throw "Configured model-1 and/or helper string not present according to Groq list-models check."
    }

    # 1) Check .env is git-ignored
    Write-Host "`n[1/4] Checking .env ignore status..."
    & git check-ignore -q -- ".env"
    if ($LASTEXITCODE -ne 0) {
        throw ".env is not git-ignored. Add it to .gitignore before running."
    }
    Write-Host ".env is git-ignored: OK"

    $commonArgs = @("--model-slug", $ModelSlug, "--items", $Items, "--conditions", "NU", "--models", $Models, "--config", $Config)

    $mockOutputDir = $null
    $tempSmokeDir = $null
    if ($Mock) {
        if ([string]::IsNullOrWhiteSpace($OutputDir)) {
            $mockOutputDir = Join-Path ([System.IO.Path]::GetTempPath()) ("run_nu_mock_" + [Guid]::NewGuid().ToString("N"))
        } else {
            $mockOutputDir = $OutputDir
        }
        New-Item -ItemType Directory -Force -Path $mockOutputDir | Out-Null
        Write-Host "Mock output dir (smoke and full, temporary): $mockOutputDir"
    } else {
        if ([string]::IsNullOrWhiteSpace($SmokeOutputDir)) {
            $tempSmokeDir = Join-Path ([System.IO.Path]::GetTempPath()) ("run_nu_smoke_" + [Guid]::NewGuid().ToString("N"))
        } else {
            $tempSmokeDir = $SmokeOutputDir
        }
        New-Item -ItemType Directory -Force -Path $tempSmokeDir | Out-Null
        Write-Host "Smoke output dir (temporary, outside results/raw): $tempSmokeDir"
    }

    $fullOutputDir = $null
    if ($Mock) {
        $fullOutputDir = $mockOutputDir
    } elseif (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
        $fullOutputDir = $OutputDir
    } else {
        $fullOutputDir = "results/raw"
    }

    $smokeArgs = @() + $commonArgs + @("--max-items", "20", "--purpose", "smoke")
    $fullArgs = @() + $commonArgs + @("--purpose", "nu")
    if ($Mock) {
        $smokeArgs += @("--mock", "--output-dir", $mockOutputDir)
        $fullArgs += @("--mock", "--output-dir", $mockOutputDir)
    } else {
        $smokeArgs += @("--output-dir", $tempSmokeDir)
        $fullArgs += @("--output-dir", $fullOutputDir)
    }

    # 2) Smoke test on 20 NU items
    Write-Host "`n[2/4] Smoke test (20 NU items)..."
    if ($DryRun) {
        & python -m src.eval.run @smokeArgs --dry-run
        Assert-LastExit "smoke dry-run"
        Write-Host "Smoke dry-run completed (no requests sent, smoke criteria not available)."
    } else {
        $smokeRunOut = & python -m src.eval.run @smokeArgs 2>&1
        $smokeRunText = ($smokeRunOut | Out-String)
        Write-Host $smokeRunText
        Assert-LastExit "smoke run"
        $smokeResultsDir = if ($Mock) { $mockOutputDir } else { $tempSmokeDir }
        $eval = Get-SmokeEvaluation -ResultsDir $smokeResultsDir -Slug $ModelSlug -ConfiguredModelString $expectedRecordedModelString -RunDate $runDate -ExpectedRequests 20
        Write-Host ("Smoke answered_requests: {0}" -f $eval.answered_requests)
        Write-Host ("Smoke error_count: {0}" -f $eval.error_count)
        Write-Host ("Smoke invalid_answer_rate (among answered): {0:P2}" -f [double]$eval.invalid_answer_rate)
        Write-Host ("Smoke empty_answers: {0}" -f $eval.empty_answers)
        Write-Host ("Smoke model_string_mismatches: {0}" -f $eval.model_string_mismatches)
        Write-Host ("Smoke recorded_model_strings: {0}" -f (($eval.recorded_model_strings | ConvertTo-Json -Compress)))
        if (-not $eval.pass) {
            Write-Host "Smoke criteria FAILED. Sample raw outputs (up to 3):"
            ($eval.sample_raw_outputs | ConvertTo-Json -Depth 6)
            throw "Smoke criteria failed (require all 20 answered after retries, error_count == 0, invalid_answer_rate among answered <= 5%, no empty answers, recorded model_string == configured). Stopping before full NU run."
        }
        Write-Host "Smoke criteria OK (all 20 answered, error_count == 0, invalid_answer_rate among answered <= 5%, no empty answers, model_string matches)."
        if (-not $Mock) {
            Write-Host "Smoke rows written outside results/raw: $tempSmokeDir"
        }
    }

    # 3) Full NU run (resumable)
    Write-Host "`n[3/4] Full NU run (resumable)..."
    if ($DryRun) {
        & python -m src.eval.run @fullArgs --dry-run
        Assert-LastExit "full NU dry-run"
        Write-Host "Full NU dry-run completed."
    } else {
        $fullRunOut = & python -m src.eval.run @fullArgs 2>&1
        $fullRunText = ($fullRunOut | Out-String)
        Write-Host $fullRunText
        Assert-LastExit "full NU run"
    }

    # 4) Summary
    Write-Host "`n[4/4] Summary (counts, invalid rates, tokens)..."
    if ($DryRun) {
        Write-Host "Dry-run mode: no result rows written. Counts/invalid rates/tokens unavailable."
        Write-Host "Tokens: unavailable (no token fields in results schema)."
    } elseif ($Mock) {
        $summary = Get-SummaryFromResults -ResultsDir $mockOutputDir -Slug $ModelSlug -Condition "NU"
        $summary | ConvertTo-Json -Depth 6
        Write-Host "Mock output retained at: $mockOutputDir"
    } else {
        $summary = Get-SummaryFromResults -ResultsDir $fullOutputDir -Slug $ModelSlug -Condition "NU"
        $summary | ConvertTo-Json -Depth 6
    }

    Write-Host "`nDone."
    exit 0
}
finally {
    Pop-Location
}
