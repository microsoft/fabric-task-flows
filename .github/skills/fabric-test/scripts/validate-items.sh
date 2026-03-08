#!/usr/bin/env bash
# =============================================================================
# ⚠️ DEPRECATED — Use validate-items.py (REST API) instead.
# This script requires ms-fabric-cli which is no longer a project dependency.
# Retained for backward compatibility only.
# =============================================================================
# Fabric Task Flows — Validation Script
# Parses a deployment-handoff.md, runs `fab exists` for each deployed item,
# and outputs a pre-filled validation-report.md YAML block to stdout.
#
# Usage:
#   ./scripts/validate-items.sh <deployment-handoff.md> [--workspace <name>]
#   ./scripts/validate-items.sh --help
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Brand Banner
# ---------------------------------------------------------------------------
print_banner() {
  local project_name="${1:-Project}"
  local task_flow="${2:-unknown}"
  local mode="${3:-Validation}"

  echo "" >&2
  echo "╔══════════════════════════════════════════════════════════════════╗" >&2
  echo "║                                                                  ║" >&2
  echo "║        /@@@@@@@@@@@@/                                            ║" >&2
  echo "║       /@@@@@@@@@@@@/   ┌──────────────────────────────────────┐  ║" >&2
  echo "║      /@@@@/            │                                      │  ║" >&2
  echo "║     /@@@@@@@@@@@@/     │ F A B R I C   T A S K   F L O W S    │  ║" >&2
  echo "║    /@@@@/              │ ──────────────────────────────────── │  ║" >&2
  echo "║   /@@@@/               │ Deploy Microsoft Fabric              │  ║" >&2
  echo "║  /@@@@/                │ architectures to production          │  ║" >&2
  echo "║                        └──────────────────────────────────────┘  ║" >&2
  echo "║                                                                  ║" >&2
  printf "║  Project:   %-53s ║\n" "$project_name" >&2
  printf "║  Task Flow: %-53s ║\n" "$task_flow" >&2
  printf "║  Mode:      %-53s ║\n" "$mode" >&2
  echo "║                                                                  ║" >&2
  echo "╚══════════════════════════════════════════════════════════════════╝" >&2
  echo "" >&2
}

# ---------------------------------------------------------------------------
# Color helpers (stderr only — stdout is reserved for YAML output)
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_pass()   { echo -e "  ${GREEN}✅ PASS${NC}  $*" >&2; }
log_fail()   { echo -e "  ${RED}❌ FAIL${NC}  $*" >&2; }
log_skip()   { echo -e "  ${YELLOW}⏭️  SKIP${NC}  $*" >&2; }
log_info()   { echo -e "  $*" >&2; }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
show_help() {
  cat <<'EOF'
Fabric Task Flows — validate-items.sh

Parses a deployment-handoff.md, runs `fab exists` for each deployed item,
and outputs a pre-filled validation-report.md YAML block to stdout.

USAGE:
  ./scripts/validate-items.sh <deployment-handoff.md> [OPTIONS]

OPTIONS:
  --workspace <name>   Override workspace name (auto-detected from handoff if omitted)
  --help               Show this help message

EXAMPLES:
  ./scripts/validate-items.sh projects/my-project/prd/deployment-handoff.md
  ./scripts/validate-items.sh projects/my-project/prd/deployment-handoff.md --workspace my-ws-dev
  ./scripts/validate-items.sh projects/my-project/prd/deployment-handoff.md > validation-report.yaml

EXIT CODES:
  0  All items verified (or only manual checks remain)
  1  One or more items failed verification
  2  Parse error or missing file
EOF
  exit 0
}

# ---------------------------------------------------------------------------
# Fab type mapping
# ---------------------------------------------------------------------------
declare -A FAB_TYPES=(
  ["Lakehouse"]="Lakehouse"
  ["Warehouse"]="Warehouse"
  ["Eventhouse"]="Eventhouse"
  ["Environment"]="Environment"
  ["Notebook"]="Notebook"
  ["Pipeline"]="DataPipeline"
  ["DataPipeline"]="DataPipeline"
  ["SemanticModel"]="SemanticModel"
  ["Report"]="Report"
  ["Dashboard"]="Dashboard"
  ["CopyJob"]="CopyJob"
  ["Eventstream"]="Eventstream"
  ["KQLQueryset"]="KQLQueryset"
  ["KQLDatabase"]="KQLDatabase"
  ["SQLDatabase"]="SQLDatabase"
  ["SparkJobDefinition"]="SparkJobDefinition"
  ["MLExperiment"]="MLExperiment"
  ["MLModel"]="MLModel"
)

PORTAL_ONLY=("Activator" "RealTimeDashboard" "GraphQLApi" "UserDataFunctions" "Dataflow" "CosmosDB" "Mirroring" "Ontology" "DataAgent")

is_portal_only() {
  local t="$1"
  for po in "${PORTAL_ONLY[@]}"; do
    [[ "$t" == "$po" ]] && return 0
  done
  return 1
}

# ---------------------------------------------------------------------------
# Phase assignment
# ---------------------------------------------------------------------------
get_phase() {
  local item_type="$1"
  case "$item_type" in
    Lakehouse|Warehouse|Eventhouse|SQLDatabase|KQLDatabase|CosmosDB) echo "Foundation" ;;
    Environment) echo "Environment" ;;
    CopyJob|Eventstream|DataPipeline|Pipeline|Dataflow|Mirroring) echo "Ingestion" ;;
    Notebook|SparkJobDefinition|KQLQueryset) echo "Transformation" ;;
    SemanticModel|Report|Dashboard|RealTimeDashboard) echo "Visualization" ;;
    MLExperiment|MLModel) echo "ML" ;;
    *) echo "Other" ;;
  esac
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
HANDOFF_FILE=""
WORKSPACE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) show_help ;;
    --workspace)
      [[ $# -lt 2 ]] && { echo "Error: --workspace requires a value" >&2; exit 2; }
      WORKSPACE_OVERRIDE="$2"; shift 2 ;;
    *)
      if [[ -z "$HANDOFF_FILE" ]]; then
        HANDOFF_FILE="$1"; shift
      else
        echo "Error: Unexpected argument '$1'. Run with --help for usage." >&2; exit 2
      fi ;;
  esac
done

if [[ -z "$HANDOFF_FILE" ]]; then
  echo "Error: No deployment-handoff.md file provided." >&2
  echo "Usage: ./scripts/validate-items.sh <deployment-handoff.md> [--workspace <name>]" >&2
  exit 2
fi

if [[ ! -f "$HANDOFF_FILE" ]]; then
  echo "Error: File not found: $HANDOFF_FILE" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Extract YAML block from markdown (content between ```yaml and ```)
# ---------------------------------------------------------------------------
YAML_CONTENT=$(sed -n '/^```yaml/,/^```/{/^```/d;p}' "$HANDOFF_FILE")

if [[ -z "$YAML_CONTENT" ]]; then
  # Fallback: try reading the whole file as YAML (no fenced block)
  YAML_CONTENT=$(cat "$HANDOFF_FILE")
fi

if [[ -z "$YAML_CONTENT" ]]; then
  echo "Error: Could not extract YAML content from $HANDOFF_FILE" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Parse top-level fields
# ---------------------------------------------------------------------------
PROJECT=$(echo "$YAML_CONTENT" | grep -m1 '^project:' | sed 's/^project:[[:space:]]*//' | tr -d '"' | tr -d "'")
TASK_FLOW=$(echo "$YAML_CONTENT" | grep -m1 '^task_flow:' | sed 's/^task_flow:[[:space:]]*//' | tr -d '"' | tr -d "'")
TODAY=$(date +%Y-%m-%d)

if [[ -z "$PROJECT" ]]; then
  echo "Error: Could not parse 'project:' from handoff file." >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Auto-detect workspace from fab commands in the handoff
# ---------------------------------------------------------------------------
if [[ -n "$WORKSPACE_OVERRIDE" ]]; then
  WORKSPACE="$WORKSPACE_OVERRIDE"
else
  WORKSPACE=$(echo "$YAML_CONTENT" | grep -oP '(?<=fab (mkdir|exists|set|get|ls) ")[^"]*(?=\.Workspace)' | head -1 || true)
  if [[ -z "$WORKSPACE" ]]; then
    # Try unquoted commands
    WORKSPACE=$(echo "$YAML_CONTENT" | grep -oP 'fab (mkdir|exists|set|get|ls) \K[^.]+(?=\.Workspace)' | head -1 || true)
  fi
  if [[ -z "$WORKSPACE" ]]; then
    # Fallback: use project name as workspace
    WORKSPACE="$PROJECT"
    log_info "⚠️  Could not auto-detect workspace; using project name: $WORKSPACE"
  fi
fi

# ---------------------------------------------------------------------------
# Parse items block — extract name, type, wave, status for each item
# ---------------------------------------------------------------------------
# We parse the items array by detecting "- name:" as item boundaries
ITEM_NAMES=()
ITEM_TYPES=()
ITEM_WAVES=()
ITEM_STATUSES=()

current_name=""
current_type=""
current_wave=""
current_status=""
in_items=false

while IFS= read -r line; do
  # Detect start of items block
  if echo "$line" | grep -qP '^items:'; then
    in_items=true
    continue
  fi

  # Detect end of items block (next top-level key)
  if $in_items && echo "$line" | grep -qP '^[a-z_]+:' && ! echo "$line" | grep -qP '^\s'; then
    # Flush last item
    if [[ -n "$current_name" ]]; then
      ITEM_NAMES+=("$current_name")
      ITEM_TYPES+=("$current_type")
      ITEM_WAVES+=("$current_wave")
      ITEM_STATUSES+=("$current_status")
    fi
    in_items=false
    continue
  fi

  if ! $in_items; then
    continue
  fi

  # New item boundary
  if echo "$line" | grep -qP '^\s+-\s+name:'; then
    # Flush previous item
    if [[ -n "$current_name" ]]; then
      ITEM_NAMES+=("$current_name")
      ITEM_TYPES+=("$current_type")
      ITEM_WAVES+=("$current_wave")
      ITEM_STATUSES+=("$current_status")
    fi
    current_name=$(echo "$line" | sed 's/.*name:[[:space:]]*//' | tr -d '"' | tr -d "'")
    current_type=""
    current_wave=""
    current_status=""
    continue
  fi

  # Parse fields within an item
  if echo "$line" | grep -qP '^\s+type:'; then
    current_type=$(echo "$line" | sed 's/.*type:[[:space:]]*//' | tr -d '"' | tr -d "'")
  elif echo "$line" | grep -qP '^\s+wave:'; then
    current_wave=$(echo "$line" | sed 's/.*wave:[[:space:]]*//' | tr -d '"' | tr -d "'")
  elif echo "$line" | grep -qP '^\s+status:'; then
    current_status=$(echo "$line" | sed 's/.*status:[[:space:]]*//' | tr -d '"' | tr -d "'")
  fi
done <<< "$YAML_CONTENT"

# Flush final item if we're still in items block
if $in_items && [[ -n "$current_name" ]]; then
  ITEM_NAMES+=("$current_name")
  ITEM_TYPES+=("$current_type")
  ITEM_WAVES+=("$current_wave")
  ITEM_STATUSES+=("$current_status")
fi

TOTAL_ITEMS=${#ITEM_NAMES[@]}

if [[ $TOTAL_ITEMS -eq 0 ]]; then
  echo "Error: No items found in the deployment handoff." >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Show banner
# ---------------------------------------------------------------------------
print_banner "$PROJECT" "$TASK_FLOW" "Validation"
log_info "Handoff:   $HANDOFF_FILE"
log_info "Workspace: $WORKSPACE"
log_info "Items:     $TOTAL_ITEMS"
echo "" >&2

# ---------------------------------------------------------------------------
# Run fab exists for each deployed item
# ---------------------------------------------------------------------------
declare -A PHASE_STATUS    # phase -> pass|warn|fail
VERIFIED_ITEMS=()          # parallel arrays for results
VERIFIED_METHODS=()
VERIFIED_RESULTS=()        # true|false
VERIFIED_ISSUES=()
MANUAL_ITEMS=()

pass_count=0
fail_count=0
skip_count=0
manual_count=0

for i in $(seq 0 $((TOTAL_ITEMS - 1))); do
  name="${ITEM_NAMES[$i]}"
  type="${ITEM_TYPES[$i]}"
  wave="${ITEM_WAVES[$i]}"
  status="${ITEM_STATUSES[$i]}"
  phase=$(get_phase "$type")

  # Only validate deployed items
  if [[ "$status" != "deployed" ]]; then
    log_skip "$name ($type) — status: $status"
    VERIFIED_ITEMS+=("$name")
    VERIFIED_METHODS+=("skipped (status: $status)")
    VERIFIED_RESULTS+=("false")
    VERIFIED_ISSUES+=("Item was not deployed (status: $status)")
    ((skip_count++)) || true
    # Mark phase as warn if not already fail
    if [[ "${PHASE_STATUS[$phase]:-pass}" != "fail" ]]; then
      PHASE_STATUS[$phase]="warn"
    fi
    continue
  fi

  # Portal-only items — cannot verify via CLI
  if is_portal_only "$type"; then
    log_skip "$name ($type) — portal-only, manual check required"
    VERIFIED_ITEMS+=("$name")
    VERIFIED_METHODS+=("manual (portal-only)")
    VERIFIED_RESULTS+=("false")
    VERIFIED_ISSUES+=("Cannot verify via CLI — check Fabric Portal")
    MANUAL_ITEMS+=("$name")
    ((manual_count++)) || true
    continue
  fi

  # Resolve fab type
  fab_type="${FAB_TYPES[$type]:-$type}"
  fab_path="${WORKSPACE}.Workspace/${name}.${fab_type}"

  log_info "Checking: $fab_path"

  if fab exists "$fab_path" 2>/dev/null; then
    log_pass "$name ($type)"
    VERIFIED_ITEMS+=("$name")
    VERIFIED_METHODS+=("fab exists")
    VERIFIED_RESULTS+=("true")
    VERIFIED_ISSUES+=("")
    ((pass_count++)) || true
    # Initialize phase status if not set
    PHASE_STATUS[$phase]="${PHASE_STATUS[$phase]:-pass}"
  else
    log_fail "$name ($type) — fab exists returned non-zero"
    VERIFIED_ITEMS+=("$name")
    VERIFIED_METHODS+=("fab exists")
    VERIFIED_RESULTS+=("false")
    VERIFIED_ISSUES+=("fab exists failed — item not found in workspace")
    ((fail_count++)) || true
    PHASE_STATUS[$phase]="fail"
  fi
done

# ---------------------------------------------------------------------------
# Determine overall status
# ---------------------------------------------------------------------------
if [[ $fail_count -gt 0 ]]; then
  OVERALL_STATUS="failed"
elif [[ $skip_count -gt 0 ]]; then
  OVERALL_STATUS="partial"
else
  OVERALL_STATUS="passed"
fi

# ---------------------------------------------------------------------------
# Build phases list — collect all unique phases from items
# ---------------------------------------------------------------------------
KNOWN_PHASES=("Foundation" "Environment" "Ingestion" "Transformation" "Visualization" "ML" "Other")
ACTIVE_PHASES=()

for i in $(seq 0 $((TOTAL_ITEMS - 1))); do
  phase=$(get_phase "${ITEM_TYPES[$i]}")
  # Add to active phases if not already there
  found=false
  for ap in "${ACTIVE_PHASES[@]+"${ACTIVE_PHASES[@]}"}"; do
    [[ "$ap" == "$phase" ]] && { found=true; break; }
  done
  $found || ACTIVE_PHASES+=("$phase")
done

# ---------------------------------------------------------------------------
# Summary (stderr)
# ---------------------------------------------------------------------------
echo "" >&2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
verified=$((pass_count + 0))
total_checkable=$((TOTAL_ITEMS - skip_count))
echo -e "  ${GREEN}${pass_count}${NC}/${total_checkable} items verified, ${RED}${fail_count}${NC} failed, ${YELLOW}${manual_count}${NC} manual checks needed" >&2
echo "  Overall status: $OVERALL_STATUS" >&2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
echo "" >&2

# ---------------------------------------------------------------------------
# Output YAML validation report (stdout)
# ---------------------------------------------------------------------------
cat <<EOF
# Validation Report (Automated Scan)
# Generated: $TODAY
# Run by: validate-items.sh
# ⚠️ LLM supplement needed: Validation Context + Future Considerations prose

project: "$PROJECT"
task_flow: "$TASK_FLOW"
date: "$TODAY"
status: $OVERALL_STATUS  # passed | partial | failed

phases:
EOF

# Emit phases in a stable order, including CI/CD Readiness as always-present
for phase in "${KNOWN_PHASES[@]}"; do
  # Check if this phase has any items
  phase_active=false
  for i in $(seq 0 $((TOTAL_ITEMS - 1))); do
    p=$(get_phase "${ITEM_TYPES[$i]}")
    if [[ "$p" == "$phase" ]]; then
      phase_active=true
      break
    fi
  done

  if $phase_active; then
    ps="${PHASE_STATUS[$phase]:-pass}"
    echo "  - name: $phase"
    echo "    status: $ps"
    echo "    notes: \"\""
  fi
done

# Always include CI/CD Readiness
echo "  - name: CI/CD Readiness"
echo "    status: na"
echo "    notes: \"\""

echo ""
echo "items_validated:"

for i in $(seq 0 $((${#VERIFIED_ITEMS[@]} - 1))); do
  echo "  - name: \"${VERIFIED_ITEMS[$i]}\""
  echo "    verified: ${VERIFIED_RESULTS[$i]}"
  echo "    method: \"${VERIFIED_METHODS[$i]}\""
  echo "    issue: \"${VERIFIED_ISSUES[$i]}\""
done

echo ""
echo "manual_steps:"

if [[ ${#MANUAL_ITEMS[@]} -gt 0 ]]; then
  for mi in $(seq 0 $((${#MANUAL_ITEMS[@]} - 1))); do
    idx=$((mi + 1))
    echo "  - id: M-${idx}"
    echo "    confirmed: false"
    echo "    action_needed: \"Verify ${MANUAL_ITEMS[$mi]} manually in Fabric Portal\""
  done
else
  echo "  []"
fi

echo ""
echo "issues:"

if [[ $fail_count -gt 0 ]]; then
  for i in $(seq 0 $((${#VERIFIED_ITEMS[@]} - 1))); do
    if [[ "${VERIFIED_RESULTS[$i]}" == "false" && "${VERIFIED_METHODS[$i]}" == "fab exists" ]]; then
      echo "  - severity: high"
      echo "    item: \"${VERIFIED_ITEMS[$i]}\""
      echo "    issue: \"${VERIFIED_ISSUES[$i]}\""
      echo "    action: \"Re-deploy item or verify workspace name\""
    fi
  done
else
  echo "  []"
fi

echo ""
echo "next_steps:"
echo "  - \"LLM: Add Validation Context prose section\""
echo "  - \"LLM: Add Future Considerations prose section\""

if [[ ${#MANUAL_ITEMS[@]} -gt 0 ]]; then
  echo "  - \"Verify ${#MANUAL_ITEMS[@]} portal-only item(s) manually\""
fi

if [[ $fail_count -gt 0 ]]; then
  echo "  - \"Investigate and re-deploy $fail_count failed item(s)\""
  echo "  - \"Re-run validation after fixes\""
fi

# ---------------------------------------------------------------------------
# Exit code
# ---------------------------------------------------------------------------
if [[ $fail_count -gt 0 ]]; then
  exit 1
else
  exit 0
fi
