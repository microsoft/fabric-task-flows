# Script Banner — Fabric Task Flows Brand Asset

**This is the canonical banner for ALL generated scripts.** Every script output by any agent (deploy scripts, validation scripts, rollback scripts, CLI tooling) MUST display this banner as the first thing the user sees when running the script.

## Banner Template

### Bash

```bash
print_banner() {
  local project_name="${1:-Project}"
  local task_flow="${2:-unknown}"
  local mode="${3:-Deploy}"

  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║                                                                  ║"
  echo "║        /@@@@@@@@@@@@@@/                                          ║"
  echo "║       /@@@@@@@@@@@@@@/  ╔════════════════════════════════════╗   ║"
  echo "║      /@@@@/             ║                                    ║   ║"
  echo "║     /@@@@@@@@@@@@@/     ║  F A B R I C   T A S K   F L O W S ║   ║"
  echo "║    /@@@@/               ║  ──────────────────────────────── ║   ║"
  echo "║   /@@@@/                ║  Deploy Microsoft Fabric           ║   ║"
  echo "║  /@@@@/                 ║  architectures to production       ║   ║"
  echo "║                         ╚════════════════════════════════════╝   ║"
  echo "║                                                                  ║"
  printf "║   Project:   %-49s ║\n" "$project_name"
  printf "║   Task Flow: %-49s ║\n" "$task_flow"
  printf "║   Mode:      %-49s ║\n" "$mode"
  echo "║                                                                  ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
}
```

### PowerShell

```powershell
function Print-Banner {
  param(
    [string]$ProjectName = "Project",
    [string]$TaskFlow = "unknown",
    [string]$Mode = "Deploy"
  )

  Write-Host ""
  Write-Host "╔══════════════════════════════════════════════════════════════════╗"
  Write-Host "║                                                                  ║"
  Write-Host "║        /@@@@@@@@@@@@@@/                                          ║"
  Write-Host "║       /@@@@@@@@@@@@@@/  ╔════════════════════════════════════╗   ║"
  Write-Host "║      /@@@@/             ║                                    ║   ║"
  Write-Host "║     /@@@@@@@@@@@@@/     ║  F A B R I C   T A S K   F L O W S ║   ║"
  Write-Host "║    /@@@@/               ║  ──────────────────────────────── ║   ║"
  Write-Host "║   /@@@@/                ║  Deploy Microsoft Fabric           ║   ║"
  Write-Host "║  /@@@@/                 ║  architectures to production       ║   ║"
  Write-Host "║                         ╚════════════════════════════════════╝   ║"
  Write-Host "║                                                                  ║"
  Write-Host ("║   Project:   {0,-49} ║" -f $ProjectName)
  Write-Host ("║   Task Flow: {0,-49} ║" -f $TaskFlow)
  Write-Host ("║   Mode:      {0,-49} ║" -f $Mode)
  Write-Host "║                                                                  ║"
  Write-Host "╚══════════════════════════════════════════════════════════════════╝"
  Write-Host ""
}
```

## Static Preview

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        /@@@@@@@@@@@@@@/                                          ║
║       /@@@@@@@@@@@@@@/  ╔════════════════════════════════════╗   ║
║      /@@@@/             ║                                    ║   ║
║     /@@@@@@@@@@@@@/     ║  F A B R I C   T A S K   F L O W S ║   ║
║    /@@@@/               ║  ──────────────────────────────── ║   ║
║   /@@@@/                ║  Deploy Microsoft Fabric           ║   ║
║  /@@@@/                 ║  architectures to production       ║   ║
║                         ╚════════════════════════════════════╝   ║
║                                                                  ║
║   Project:   {PROJECT_NAME}                                      ║
║   Task Flow: {TASK_FLOW}                                         ║
║   Mode:      {MODE}                                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

## Placeholders

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{PROJECT_NAME}` | Architecture Handoff → project name | `Energy Field Intelligence` |
| `{TASK_FLOW}` | Architecture Handoff → task flow ID | `medallion` |
| `{MODE}` | Deployment mode from handoff | `Design-Only (Local Script Generation)` or `Deploy to Fabric` |

## Agent Instructions

- **All script-generating agents** (engineer, tester) MUST call `print_banner` / `Print-Banner` at the top of every generated script
- The banner function is included directly in each generated script (not sourced from a shared file) so scripts are self-contained
- Use the bash version for `.sh` scripts and the PowerShell version for `.ps1` scripts
- The `mode` parameter should reflect the script's purpose: `Deploy to Fabric`, `Design-Only (Local Script Generation)`, `Validation`, `Rollback`
