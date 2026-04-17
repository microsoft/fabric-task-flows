Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    if ($null -eq $payload) {
        exit 0
    }

    $toolName = [string]$payload.toolName
    $toolArgsObj = Get-ToolArgsObject -ToolArgs $payload.toolArgs
    $command = Get-CommandString -ToolArgsObj $toolArgsObj

    $pathCandidate = ''
    if ($null -ne $toolArgsObj -and $toolArgsObj.PSObject.Properties.Name -contains 'path') {
        $pathCandidate = [string]$toolArgsObj.path
    }

    if ($pathCandidate -match '(?i)_projects[\\/].+?[\\/]pipeline-state\.json$') {
        @{ permissionDecision = 'deny'; permissionDecisionReason = 'Use run-pipeline.py for pipeline state transitions.' } | ConvertTo-Json -Compress
        exit 0
    }

    if ($toolName -match '^(powershell|bash|shell|terminal)$') {
        if ($command -match '(?i)git\s+reset\s+--hard' -or $command -match '(?i)git\s+checkout\s+--\s' -or $command -match '(?i)rm\s+-rf\s+/' -or $command -match '(?i)Remove-Item\s+.+-Recurse\s+-Force') {
            @{ permissionDecision = 'deny'; permissionDecisionReason = 'Destructive command blocked by repository hook policy.' } | ConvertTo-Json -Compress
            exit 0
        }

        if ($command -match '(?i)pipeline-state\.json' -and $command -notmatch '(?i)_shared/scripts/run-pipeline\.py') {
            @{ permissionDecision = 'deny'; permissionDecisionReason = 'Do not manipulate pipeline-state.json directly; use run-pipeline.py.' } | ConvertTo-Json -Compress
            exit 0
        }
    }

    exit 0
}
catch {
    $msg = $_.Exception.Message
    Write-JsonlLog -FileName 'hook-internal-errors.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        hook = 'pretool-policy'
        error = $msg
    }
    exit 0
}
