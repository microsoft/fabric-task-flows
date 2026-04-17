Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\hook-common.ps1"

try {
    $payload = Get-HookPayload
    if ($null -eq $payload) {
        exit 0
    }

    $toolArgsObj = Get-ToolArgsObject -ToolArgs $payload.toolArgs
    $command = Get-CommandString -ToolArgsObj $toolArgsObj

    $resultType = ''
    $resultText = ''
    if ($null -ne $payload.toolResult) {
        if ($payload.toolResult.PSObject.Properties.Name -contains 'resultType') {
            $resultType = [string]$payload.toolResult.resultType
        }
        if ($payload.toolResult.PSObject.Properties.Name -contains 'textResultForLlm') {
            $resultText = [string]$payload.toolResult.textResultForLlm
        }
    }

    $isPipelineCmd = ($command -match '(?i)_shared/scripts/run-pipeline\.py\s+(start|advance|next|status|reconcile|reset)')

    Write-JsonlLog -FileName 'tool-events.jsonl' -Entry @{
        ts = (Get-Date).ToUniversalTime().ToString('o')
        event = 'postToolUse'
        toolName = [string]$payload.toolName
        resultType = $resultType
        isPipelineCommand = $isPipelineCmd
        commandPreview = if ($command.Length -gt 180) { $command.Substring(0, 180) } else { $command }
    }

    if ($resultType -eq 'failure') {
        Write-JsonlLog -FileName 'tool-failures.jsonl' -Entry @{
            ts = (Get-Date).ToUniversalTime().ToString('o')
            toolName = [string]$payload.toolName
            commandPreview = if ($command.Length -gt 180) { $command.Substring(0, 180) } else { $command }
            errorPreview = if ($resultText.Length -gt 400) { $resultText.Substring(0, 400) } else { $resultText }
        }
    }

    exit 0
}
catch {
    exit 0
}
