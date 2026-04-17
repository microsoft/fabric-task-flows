Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    Write-JsonlLog -FileName 'session-events.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        event = 'sessionEnd'
        reason = if ($null -ne $payload) { [string]$payload.reason } else { 'unknown' }
        cwd = if ($null -ne $payload) { [string]$payload.cwd } else { (Get-RepoRoot) }
    }
    exit 0
}
catch {
    exit 0
}
