# =============================================================================
# Fabric Task Flows — Validation Script (PowerShell)
# Parses a deployment-handoff.md, runs `fab exists` for each deployed item,
# and outputs a pre-filled validation-report.md YAML block to stdout.
#
# Usage:
#   ./scripts/validate-items.ps1 <deployment-handoff.md> [-Workspace <name>]
#   ./scripts/validate-items.ps1 -Help
# =============================================================================
param(
  [Parameter(Position = 0)]
  [string]$HandoffFile,

  [Alias("Workspace")]
  [string]$WorkspaceOverride,

  [Alias("h")]
  [switch]$Help
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Brand Banner
# ---------------------------------------------------------------------------
function Print-Banner {
  param(
    [string]$ProjectName = "Project",
    [string]$TaskFlow = "unknown",
    [string]$Mode = "Validation"
  )

  Write-Host ""
  Write-Host "╔══════════════════════════════════════════════════════════════════╗"
  Write-Host "║                                                                  ║"
  Write-Host "║        /@@@@@@@@@@@@/                                            ║"
  Write-Host "║       /@@@@@@@@@@@@/   ┌──────────────────────────────────────┐  ║"
  Write-Host "║      /@@@@/            │                                      │  ║"
  Write-Host "║     /@@@@@@@@@@@@/     │ F A B R I C   T A S K   F L O W S    │  ║"
  Write-Host "║    /@@@@/              │ ──────────────────────────────────── │  ║"
  Write-Host "║   /@@@@/               │ Deploy Microsoft Fabric              │  ║"
  Write-Host "║  /@@@@/                │ architectures to production          │  ║"
  Write-Host "║                        └──────────────────────────────────────┘  ║"
  Write-Host "║                                                                  ║"
  Write-Host ("║  Project:   {0,-53} ║" -f $ProjectName)
  Write-Host ("║  Task Flow: {0,-53} ║" -f $TaskFlow)
  Write-Host ("║  Mode:      {0,-53} ║" -f $Mode)
  Write-Host "║                                                                  ║"
  Write-Host "╚══════════════════════════════════════════════════════════════════╝"
  Write-Host ""
}

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
function Log-Pass  { param([string]$Msg) Write-Host "  ✅ PASS  $Msg" -ForegroundColor Green }
function Log-Fail  { param([string]$Msg) Write-Host "  ❌ FAIL  $Msg" -ForegroundColor Red }
function Log-Skip  { param([string]$Msg) Write-Host "  ⏭️  SKIP  $Msg" -ForegroundColor Yellow }
function Log-Info  { param([string]$Msg) Write-Host "  $Msg" }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
if ($Help) {
  Write-Host @"
Fabric Task Flows — validate-items.ps1

Parses a deployment-handoff.md, runs ``fab exists`` for each deployed item,
and outputs a pre-filled validation-report.md YAML block to stdout.

USAGE:
  ./scripts/validate-items.ps1 <deployment-handoff.md> [OPTIONS]

OPTIONS:
  -Workspace <name>   Override workspace name (auto-detected from handoff if omitted)
  -Help               Show this help message

EXAMPLES:
  ./scripts/validate-items.ps1 projects/my-project/prd/deployment-handoff.md
  ./scripts/validate-items.ps1 projects/my-project/prd/deployment-handoff.md -Workspace my-ws-dev
  ./scripts/validate-items.ps1 projects/my-project/prd/deployment-handoff.md > validation-report.yaml

EXIT CODES:
  0  All items verified (or only manual checks remain)
  1  One or more items failed verification
  2  Parse error or missing file
"@
  exit 0
}

# ---------------------------------------------------------------------------
# Fab type mapping
# --- AUTO-GENERATED from _shared/item-type-registry.json ---
# Regenerate: python scripts/generate-ps1-types.py
# Do NOT edit manually. See _shared/agent-boundaries.md.
# ---------------------------------------------------------------------------
$FabTypes = @{
  "Dashboard"              = "Dashboard"
  "DataPipeline"           = "DataPipeline"
  "Datapipeline"           = "DataPipeline"
  "Pipeline"               = "DataPipeline"
  "Datamart"               = "Datamart"
  "Environment"            = "Environment"
  "Eventhouse"             = "Eventhouse"
  "Eventstream"            = "Eventstream"
  "GraphQLApi"             = "GraphQLApi"
  "Graphqlapi"             = "GraphQLApi"
  "GraphqlApi"             = "GraphQLApi"
  "KQLDashboard"           = "KQLDashboard"
  "Kqldashboard"           = "KQLDashboard"
  "RealTimeDashboard"      = "KQLDashboard"
  "Realtimedashboard"      = "KQLDashboard"
  "RealTimeDash"           = "KQLDashboard"
  "KQLDatabase"            = "KQLDatabase"
  "Kqldatabase"            = "KQLDatabase"
  "KqlDatabase"            = "KQLDatabase"
  "KQLQueryset"            = "KQLQueryset"
  "Kqlqueryset"            = "KQLQueryset"
  "KqlQueryset"            = "KQLQueryset"
  "Lakehouse"              = "Lakehouse"
  "MLExperiment"           = "MLExperiment"
  "Mlexperiment"           = "MLExperiment"
  "MlExperiment"           = "MLExperiment"
  "Experiment"             = "MLExperiment"
  "MLModel"                = "MLModel"
  "Mlmodel"                = "MLModel"
  "MlModel"                = "MLModel"
  "MirroredDatabase"       = "MirroredDatabase"
  "Mirroreddatabase"       = "MirroredDatabase"
  "MirroredWarehouse"      = "MirroredWarehouse"
  "Mirroredwarehouse"      = "MirroredWarehouse"
  "MountedDataFactory"     = "MountedDataFactory"
  "Mounteddatafactory"     = "MountedDataFactory"
  "Notebook"               = "Notebook"
  "PaginatedReport"        = "PaginatedReport"
  "Paginatedreport"        = "PaginatedReport"
  "Reflex"                 = "Reflex"
  "Activator"              = "Reflex"
  "Report"                 = "Report"
  "SQLDatabase"            = "SQLDatabase"
  "Sqldatabase"            = "SQLDatabase"
  "SqlDatabase"            = "SQLDatabase"
  "SQLEndpoint"            = "SQLEndpoint"
  "Sqlendpoint"            = "SQLEndpoint"
  "SqlEndpoint"            = "SQLEndpoint"
  "SqlAnalyticsEndpoint"   = "SQLEndpoint"
  "SemanticModel"          = "SemanticModel"
  "Semanticmodel"          = "SemanticModel"
  "SparkJobDefinition"     = "SparkJobDefinition"
  "Sparkjobdefinition"     = "SparkJobDefinition"
  "SparkJobDef"            = "SparkJobDefinition"
  "Warehouse"              = "Warehouse"
}

$PortalOnly = @(
  "CopyJob", "CosmosDB", "Dashboard", "DataAgent", "DataflowGen2", "GraphQLApi",
  "KQLDashboard", "MetricsScorecard", "Mirroring", "Ontology", "PaginatedReport",
  "RealTimeMap", "Reflex", "SQLEndpoint", "UserDataFunctions", "VariableLibrary"
)

function Get-Phase {
  param([string]$ItemType)
  switch ($ItemType) {
    { $_ -in @("CosmosDB", "Datamart", "Eventhouse", "KQLDatabase", "Lakehouse", "MirroredDatabase", "MirroredWarehouse", "SQLDatabase", "SQLEndpoint", "Warehouse") } { return "Foundation" }
    { $_ -in @("Environment", "VariableLibrary") } { return "Environment" }
    { $_ -in @("CopyJob", "DataPipeline", "DataflowGen2", "Eventstream", "Mirroring", "MountedDataFactory") } { return "Ingestion" }
    { $_ -in @("KQLQueryset", "Notebook", "SparkJobDefinition", "UserDataFunctions") } { return "Transformation" }
    { $_ -in @("Dashboard", "DataAgent", "GraphQLApi", "KQLDashboard", "MetricsScorecard", "Ontology", "PaginatedReport", "RealTimeMap", "Reflex", "Report", "SemanticModel") } { return "Visualization" }
    { $_ -in @("MLExperiment", "MLModel") } { return "ML" }
    default { return "Other" }
  }
}

# ---------------------------------------------------------------------------
# Validate input
# ---------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($HandoffFile)) {
  Write-Host "Error: No deployment-handoff.md file provided." -ForegroundColor Red
  Write-Host "Usage: ./scripts/validate-items.ps1 <deployment-handoff.md> [-Workspace <name>]"
  exit 2
}

if (-not (Test-Path $HandoffFile)) {
  Write-Host "Error: File not found: $HandoffFile" -ForegroundColor Red
  exit 2
}

# ---------------------------------------------------------------------------
# Extract YAML block from markdown
# ---------------------------------------------------------------------------
$fileContent = Get-Content $HandoffFile -Raw
$yamlContent = ""

if ($fileContent -match '(?s)```yaml\s*\r?\n(.+?)```') {
  $yamlContent = $Matches[1]
} else {
  $yamlContent = $fileContent
}

if ([string]::IsNullOrWhiteSpace($yamlContent)) {
  Write-Host "Error: Could not extract YAML content from $HandoffFile" -ForegroundColor Red
  exit 2
}

$yamlLines = $yamlContent -split "`r?`n"

# ---------------------------------------------------------------------------
# Parse top-level fields
# ---------------------------------------------------------------------------
$Project = ""
$TaskFlow = ""

foreach ($line in $yamlLines) {
  if ($line -match '^\s*project:\s*"?([^"]+)"?\s*$') {
    $Project = $Matches[1].Trim().Trim("'").Trim('"')
  }
  if ($line -match '^\s*task_flow:\s*"?([^"]+)"?\s*$') {
    $TaskFlow = $Matches[1].Trim().Trim("'").Trim('"')
  }
}

$Today = (Get-Date).ToString("yyyy-MM-dd")

if ([string]::IsNullOrWhiteSpace($Project)) {
  Write-Host "Error: Could not parse 'project:' from handoff file." -ForegroundColor Red
  exit 2
}

# ---------------------------------------------------------------------------
# Auto-detect workspace from fab commands in the handoff
# ---------------------------------------------------------------------------
$Workspace = ""

if (-not [string]::IsNullOrWhiteSpace($WorkspaceOverride)) {
  $Workspace = $WorkspaceOverride
} else {
  # Try to find workspace from fab commands (quoted or unquoted)
  foreach ($line in $yamlLines) {
    if ($line -match 'fab\s+(?:mkdir|exists|set|get|ls)\s+"?([^".\s]+)\.Workspace') {
      $Workspace = $Matches[1]
      break
    }
  }
  if ([string]::IsNullOrWhiteSpace($Workspace)) {
    $Workspace = $Project
    Log-Info "⚠️  Could not auto-detect workspace; using project name: $Workspace"
  }
}

# ---------------------------------------------------------------------------
# Parse items block
# ---------------------------------------------------------------------------
$Items = @()
$inItems = $false
$currentItem = $null

foreach ($line in $yamlLines) {
  # Detect start of items block
  if ($line -match '^\s*items:\s*$') {
    $inItems = $true
    continue
  }

  # Detect end of items block (next top-level key that isn't indented)
  if ($inItems -and $line -match '^\S' -and $line -match '^\w[\w_]*:') {
    if ($null -ne $currentItem) {
      $Items += $currentItem
    }
    $inItems = $false
    continue
  }

  if (-not $inItems) { continue }

  # New item boundary
  if ($line -match '^\s+-\s+name:\s*"?([^"]+)"?\s*$') {
    if ($null -ne $currentItem) {
      $Items += $currentItem
    }
    $currentItem = @{
      Name   = $Matches[1].Trim().Trim("'").Trim('"')
      Type   = ""
      Wave   = ""
      Status = ""
    }
    continue
  }

  # Parse fields within an item
  if ($null -ne $currentItem) {
    if ($line -match '^\s+type:\s*"?([^"]+)"?\s*$') {
      $currentItem.Type = $Matches[1].Trim().Trim("'").Trim('"')
    } elseif ($line -match '^\s+wave:\s*(\S+)') {
      $currentItem.Wave = $Matches[1].Trim()
    } elseif ($line -match '^\s+status:\s*(\S+)') {
      $currentItem.Status = $Matches[1].Trim()
    }
  }
}

# Flush final item
if ($inItems -and $null -ne $currentItem) {
  $Items += $currentItem
}

$totalItems = $Items.Count

if ($totalItems -eq 0) {
  Write-Host "Error: No items found in the deployment handoff." -ForegroundColor Red
  exit 2
}

# ---------------------------------------------------------------------------
# Show banner
# ---------------------------------------------------------------------------
Print-Banner -ProjectName $Project -TaskFlow $TaskFlow -Mode "Validation"
Log-Info "Handoff:   $HandoffFile"
Log-Info "Workspace: $Workspace"
Log-Info "Items:     $totalItems"
Write-Host ""

# ---------------------------------------------------------------------------
# Run fab exists for each deployed item
# ---------------------------------------------------------------------------
$phaseStatus = @{}
$results = @()
$manualItems = @()

$passCount = 0
$failCount = 0
$skipCount = 0
$manualCount = 0

foreach ($item in $Items) {
  $name = $item.Name
  $type = $item.Type
  $status = $item.Status
  $phase = Get-Phase -ItemType $type

  # Only validate deployed items
  if ($status -ne "deployed") {
    Log-Skip "$name ($type) — status: $status"
    $results += @{
      Name     = $name
      Method   = "skipped (status: $status)"
      Verified = "false"
      Issue    = "Item was not deployed (status: $status)"
    }
    $skipCount++
    if ($phaseStatus[$phase] -ne "fail") {
      $phaseStatus[$phase] = "warn"
    }
    continue
  }

  # Portal-only items
  if ($type -in $PortalOnly) {
    Log-Skip "$name ($type) — portal-only, manual check required"
    $results += @{
      Name     = $name
      Method   = "manual (portal-only)"
      Verified = "false"
      Issue    = "Cannot verify via CLI — check Fabric Portal"
    }
    $manualItems += $name
    $manualCount++
    continue
  }

  # Resolve fab type
  $fabType = if ($FabTypes.ContainsKey($type)) { $FabTypes[$type] } else { $type }
  $fabPath = "$Workspace.Workspace/$name.$fabType"

  Log-Info "Checking: $fabPath"

  $fabResult = $false
  try {
    $null = fab exists $fabPath 2>$null
    if ($LASTEXITCODE -eq 0) { $fabResult = $true }
  } catch {
    $fabResult = $false
  }

  if ($fabResult) {
    Log-Pass "$name ($type)"
    $results += @{
      Name     = $name
      Method   = "fab exists"
      Verified = "true"
      Issue    = ""
    }
    $passCount++
    if (-not $phaseStatus.ContainsKey($phase)) {
      $phaseStatus[$phase] = "pass"
    }
  } else {
    Log-Fail "$name ($type) — fab exists returned non-zero"
    $results += @{
      Name     = $name
      Method   = "fab exists"
      Verified = "false"
      Issue    = "fab exists failed — item not found in workspace"
    }
    $failCount++
    $phaseStatus[$phase] = "fail"
  }
}

# ---------------------------------------------------------------------------
# Determine overall status
# ---------------------------------------------------------------------------
if ($failCount -gt 0) {
  $overallStatus = "failed"
} elseif ($skipCount -gt 0) {
  $overallStatus = "partial"
} else {
  $overallStatus = "passed"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
$totalCheckable = $totalItems - $skipCount
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  $passCount/$totalCheckable items verified, " -NoNewline
Write-Host "$failCount" -ForegroundColor Red -NoNewline
Write-Host " failed, " -NoNewline
Write-Host "$manualCount" -ForegroundColor Yellow -NoNewline
Write-Host " manual checks needed"
Write-Host "  Overall status: $overallStatus"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# ---------------------------------------------------------------------------
# Output YAML validation report (stdout via Write-Output)
# ---------------------------------------------------------------------------
$knownPhases = @("Foundation", "Environment", "Ingestion", "Transformation", "Visualization", "ML", "Other")

# Collect active phases
$activePhases = @()
foreach ($item in $Items) {
  $p = Get-Phase -ItemType $item.Type
  if ($p -notin $activePhases) { $activePhases += $p }
}

$yaml = @()
$yaml += "# Validation Report (Automated Scan)"
$yaml += "# Generated: $Today"
$yaml += "# Run by: validate-items.ps1"
$yaml += "# ⚠️ LLM supplement needed: Validation Context + Future Considerations prose"
$yaml += ""
$yaml += "project: `"$Project`""
$yaml += "task_flow: `"$TaskFlow`""
$yaml += "date: `"$Today`""
$yaml += "status: $overallStatus  # passed | partial | failed"
$yaml += ""
$yaml += "phases:"

foreach ($phase in $knownPhases) {
  if ($phase -in $activePhases) {
    $ps = if ($phaseStatus.ContainsKey($phase)) { $phaseStatus[$phase] } else { "pass" }
    $yaml += "  - name: $phase"
    $yaml += "    status: $ps"
    $yaml += '    notes: ""'
  }
}

# Always include CI/CD Readiness
$yaml += "  - name: CI/CD Readiness"
$yaml += "    status: na"
$yaml += '    notes: ""'

$yaml += ""
$yaml += "items_validated:"

foreach ($r in $results) {
  $yaml += "  - name: `"$($r.Name)`""
  $yaml += "    verified: $($r.Verified)"
  $yaml += "    method: `"$($r.Method)`""
  $yaml += "    issue: `"$($r.Issue)`""
}

$yaml += ""
$yaml += "manual_steps:"

if ($manualItems.Count -gt 0) {
  for ($mi = 0; $mi -lt $manualItems.Count; $mi++) {
    $idx = $mi + 1
    $yaml += "  - id: M-$idx"
    $yaml += "    confirmed: false"
    $yaml += "    action_needed: `"Verify $($manualItems[$mi]) manually in Fabric Portal`""
  }
} else {
  $yaml += "  []"
}

$yaml += ""
$yaml += "issues:"

if ($failCount -gt 0) {
  foreach ($r in $results) {
    if ($r.Verified -eq "false" -and $r.Method -eq "fab exists") {
      $yaml += "  - severity: high"
      $yaml += "    item: `"$($r.Name)`""
      $yaml += "    issue: `"$($r.Issue)`""
      $yaml += "    action: `"Re-deploy item or verify workspace name`""
    }
  }
} else {
  $yaml += "  []"
}

$yaml += ""
$yaml += "next_steps:"
$yaml += '  - "LLM: Add Validation Context prose section"'
$yaml += '  - "LLM: Add Future Considerations prose section"'

if ($manualItems.Count -gt 0) {
  $yaml += "  - `"Verify $($manualItems.Count) portal-only item(s) manually`""
}

if ($failCount -gt 0) {
  $yaml += "  - `"Investigate and re-deploy $failCount failed item(s)`""
  $yaml += '  - "Re-run validation after fixes"'
}

# Write YAML to stdout
$yaml | Write-Output

# ---------------------------------------------------------------------------
# Exit code
# ---------------------------------------------------------------------------
if ($failCount -gt 0) {
  exit 1
} else {
  exit 0
}
