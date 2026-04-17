Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    if ($null -eq $payload) {
        exit 0
    }

    $prompt = [string]$payload.prompt
    $keywords = @('deploy', 'approve', 'revise', 'pipeline', 'sign-off', 'run-pipeline.py')
    $matches = @()
    foreach ($k in $keywords) {
        if ($prompt -match [Regex]::Escape($k)) {
            $matches += $k
        }
    }

    Write-JsonlLog -FileName 'prompt-events.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        event = 'userPromptSubmitted'
        cwd = [string]$payload.cwd
        promptLength = $prompt.Length
        keywordHits = $matches
    }

    exit 0
}
catch {
    exit 0
}
