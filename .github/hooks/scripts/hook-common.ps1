Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-HookPayload {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }
    return $raw | ConvertFrom-Json
}

function Get-RepoRoot {
    if ($env:GITHUB_WORKSPACE -and (Test-Path -LiteralPath $env:GITHUB_WORKSPACE)) {
        return $env:GITHUB_WORKSPACE
    }
    return (Get-Location).Path
}

function Get-HookLogDir {
    $root = Get-RepoRoot
    $dir = Join-Path $root '.github\hooks\logs'
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    return $dir
}

function Write-JsonlLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FileName,
        [Parameter(Mandatory = $true)]
        [hashtable]$Entry
    )

    $dir = Get-HookLogDir
    $path = Join-Path $dir $FileName
    $line = ($Entry | ConvertTo-Json -Compress -Depth 8)
    Add-Content -LiteralPath $path -Value $line -Encoding utf8
}

function Get-ToolArgsObject {
    param(
        [Parameter(Mandatory = $false)]
        $ToolArgs
    )

    if ($null -eq $ToolArgs) {
        return $null
    }

    if ($ToolArgs -is [string]) {
        if ([string]::IsNullOrWhiteSpace($ToolArgs)) {
            return $null
        }
        try {
            return $ToolArgs | ConvertFrom-Json
        }
        catch {
            return @{ raw = $ToolArgs }
        }
    }

    return $ToolArgs
}

function Get-CommandString {
    param(
        [Parameter(Mandatory = $false)]
        $ToolArgsObj
    )

    if ($null -eq $ToolArgsObj) {
        return ''
    }

    if ($ToolArgsObj.PSObject.Properties.Name -contains 'command') {
        return [string]$ToolArgsObj.command
    }

    if ($ToolArgsObj.PSObject.Properties.Name -contains 'bashCommand') {
        return [string]$ToolArgsObj.bashCommand
    }

    return ''
}
