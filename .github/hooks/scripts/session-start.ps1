Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    $root = Get-RepoRoot
    $required = @(
        '_shared\scripts\run-pipeline.py',
        '_shared\workflow-guide.md'
    )

    $missing = @()
    foreach ($rel in $required) {
        $full = Join-Path $root $rel
        if (-not (Test-Path -LiteralPath $full)) {
            $missing += $rel
        }
    }

    Write-JsonlLog -FileName 'session-events.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        event = 'sessionStart'
        cwd = if ($null -ne $payload) { [string]$payload.cwd } else { $root }
        source = if ($null -ne $payload) { [string]$payload.source } else { 'unknown' }
        hasInitialPrompt = ($null -ne $payload -and -not [string]::IsNullOrWhiteSpace([string]$payload.initialPrompt))
        missingCriticalFiles = $missing
    }

    exit 0
}
catch {
    exit 0
}
