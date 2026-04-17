Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    if ($null -eq $payload) {
        exit 0
    }

    $errorName = ''
    $errorMsg = ''
    if ($null -ne $payload.error) {
        if ($payload.error.PSObject.Properties.Name -contains 'name') {
            $errorName = [string]$payload.error.name
        }
        if ($payload.error.PSObject.Properties.Name -contains 'message') {
            $errorMsg = [string]$payload.error.message
        }
    }

    Write-JsonlLog -FileName 'error-events.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        event = 'errorOccurred'
        errorName = $errorName
        errorMessage = $errorMsg
    }

    exit 0
}
catch {
    exit 0
}
