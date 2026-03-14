#!/usr/bin/env python3
"""
Documentation drift detection for the task-flows knowledge base.

Validates cross-references across the repo to catch inconsistencies
before they reach users. Modeled after power-bi-projects'
documentationDrift.test.ts but tailored for a docs-only Markdown repo.

Usage:
    python .github/skills/fabric-test/scripts/check-drift.py          # Run all checks
    python .github/skills/fabric-test/scripts/check-drift.py --check  # CI mode: exit 1 on failure
    python .github/skills/fabric-test/scripts/check-drift.py --verbose # Show passing checks too

Exit codes:
    0 — no drift detected
    1 — drift detected (details printed)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"))
from paths import REPO_ROOT
from yaml_utils import extract_frontmatter

# Canonical task flow IDs — single source of truth
TASK_FLOW_SOURCE = REPO_ROOT / "task-flows.md"
DIAGRAMS_DIR = REPO_ROOT / "diagrams"
VALIDATION_REGISTRY = REPO_ROOT / "_shared" / "registry" / "validation-checklists.json"
DECISIONS_DIR = REPO_ROOT / "decisions"
ADVISOR_PATH = REPO_ROOT / ".github" / "agents" / "fabric-advisor.agent.md"
REGISTRY_PATH = REPO_ROOT / "_shared" / "registry" / "item-type-registry.json"


# ── helpers ──────────────────────────────────────────────────────────

def extract_task_flow_ids_from_taskflows_md() -> set[str]:
    """Extract task flow IDs from task-flows.md H2 anchors."""
    content = TASK_FLOW_SOURCE.read_text(encoding="utf-8")
    ids = set()
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            heading = m.group(1).strip()
            # Skip non-task-flow H2s (e.g., "Quick Reference", "How to Use")
            skip = {"quick-reference", "how-to-use", "overview", "task-flow-index",
                    "choosing-a-task-flow", "about", "introduction"}
            slug = re.sub(r"[^a-z0-9\s-]", "", heading.lower())
            slug = re.sub(r"\s+", "-", slug).strip("-")
            if slug not in skip:
                ids.add(slug)
    return ids


def extract_ids_from_index(index_path: Path) -> set[str]:
    """Extract task flow IDs from a _index.md routing table."""
    content = index_path.read_text(encoding="utf-8")
    ids = set()
    for line in content.splitlines():
        # Match table rows: | id | ... | filename.md |
        m = re.match(r"^\|\s*`?([a-z][\w-]*)`?\s*\|", line)
        if m:
            candidate = m.group(1).strip()
            if candidate not in ("id", "---", "task"):
                ids.add(candidate)
    return ids


def extract_signal_task_flows(advisor_path: Path) -> set[str]:
    """Extract all task flow IDs referenced in the signal mapping table."""
    content = advisor_path.read_text(encoding="utf-8")
    ids = set()
    in_table = False
    # Known single-word task flow IDs that don't contain hyphens
    single_word_flows = {"medallion", "lambda", "translytical", "general"}
    for line in content.splitlines():
        if "Signal Words" in line and "Task Flow Candidates" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            # Last column contains task flow candidates
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 5:
                candidates_col = cols[-2]  # second to last (last is empty after trailing |)
                # Extract kebab-case IDs (with hyphens)
                for token in re.findall(r"[a-z][a-z0-9-]+", candidates_col):
                    if "-" in token and len(token) > 3:
                        ids.add(token)
                # Also check for single-word flow IDs
                for word in single_word_flows:
                    if word in candidates_col.lower():
                        ids.add(word)
        elif in_table and not line.startswith("|"):
            break
    return ids


def extract_yaml_frontmatter(md_path: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None
    return extract_frontmatter(content) or None


def extract_ingestion_comparison_columns(md_path: Path) -> set[str]:
    """Extract column headers from the ingestion 4V comparison table."""
    content = md_path.read_text(encoding="utf-8")
    cols = set()
    for line in content.splitlines():
        # Match the header row: | Criteria | Copy Job | Dataflow Gen2 | ...
        if line.startswith("| Criteria |"):
            headers = [h.strip().strip("*") for h in line.split("|")[1:-1]]
            for h in headers:
                if h and h != "Criteria":
                    cols.add(h)
            break
    return cols


def extract_mirroring_sources(md_path: Path, pattern: str) -> set[str]:
    """Extract mirroring source names near a pattern match."""
    content = md_path.read_text(encoding="utf-8")
    sources = set()
    for line in content.splitlines():
        if pattern in line:
            # Extract database names (capitalized words before commas/pipes)
            for token in re.findall(r"Azure SQL MI|Azure SQL|Cosmos DB|Snowflake|Databricks|SQL Server 2025|MySQL|PostgreSQL", line):
                sources.add(token)
    return sources


# ── checks ───────────────────────────────────────────────────────────

class DriftChecker:
    def __init__(self, verbose: bool = False):
        self.failures: list[str] = []
        self.passes: list[str] = []
        self.verbose = verbose

    def check(self, name: str, condition: bool, message: str):
        if condition:
            self.passes.append(f"  ✅ {name}")
        else:
            self.failures.append(f"  ❌ {name}: {message}")

    def report(self) -> int:
        total = len(self.passes) + len(self.failures)
        if self.verbose:
            for p in self.passes:
                print(p)
        for f in self.failures:
            print(f)
        print()
        if self.failures:
            print(f"DRIFT DETECTED: {len(self.failures)}/{total} checks failed")
            return 1
        else:
            print(f"ALL CLEAR: {total}/{total} checks passed")
            return 0


def check_task_flow_coverage(dc: DriftChecker):
    """Every task flow ID in task-flows.md must have a diagram, validation
    checklist, and appear in the advisor signal mapping."""
    print("\n── Task Flow Cross-References ──")

    canonical = extract_task_flow_ids_from_taskflows_md()
    dc.check("task-flows.md has task flow IDs", len(canonical) >= 10,
             f"Expected ≥10 task flows, found {len(canonical)}")

    # Diagrams
    diagram_index = extract_ids_from_index(DIAGRAMS_DIR / "_index.md")
    diagram_files = {p.stem for p in DIAGRAMS_DIR.glob("*.md") if p.name != "_index.md"}

    missing_diagrams = canonical - diagram_files
    dc.check("every task flow has a diagram file",
             len(missing_diagrams) == 0,
             f"Missing diagram files: {sorted(missing_diagrams)}")

    missing_diagram_index = diagram_files - diagram_index
    dc.check("every diagram file is in diagrams/_index.md",
             len(missing_diagram_index) == 0,
             f"Diagram files not indexed: {sorted(missing_diagram_index)}")

    # Validation checklists (from JSON registry)
    validation_registry = json.loads(VALIDATION_REGISTRY.read_text(encoding="utf-8"))
    validation_task_flows = set(validation_registry.get("task_flows", {}).keys())

    missing_validation = canonical - validation_task_flows
    dc.check("every task flow has a validation checklist in JSON registry",
             len(missing_validation) == 0,
             f"Missing validation entries: {sorted(missing_validation)}")

    # Advisor signal coverage
    signal_flows = extract_signal_task_flows(ADVISOR_PATH)
    uncovered = canonical - signal_flows
    # general and cross-cutting flows may not appear as candidates
    uncovered -= {"general"}
    dc.check("every task flow appears in advisor signal mapping",
             len(uncovered) == 0,
             f"Task flows with no signal route: {sorted(uncovered)}")


def check_decision_guides(dc: DriftChecker):
    """Decision guide index matches actual files, and YAML frontmatter
    is consistent."""
    print("\n── Decision Guide Consistency ──")

    index_path = DECISIONS_DIR / "_index.md"
    index_ids = extract_ids_from_index(index_path)

    guide_files = {p.stem.replace("-selection", "")
                   for p in DECISIONS_DIR.glob("*-selection.md")}

    # _index.md should list all guide files
    missing_from_index = guide_files - index_ids
    dc.check("every decision guide file is in decisions/_index.md",
             len(missing_from_index) == 0,
             f"Guide files not indexed: {sorted(missing_from_index)}")

    # Every indexed guide should have a file
    index_content = index_path.read_text(encoding="utf-8")
    referenced_files = set(re.findall(r"\(([^)]+\.md)\)", index_content))
    for ref in referenced_files:
        file_path = DECISIONS_DIR / ref
        dc.check(f"indexed file {ref} exists",
                 file_path.exists(),
                 f"decisions/_index.md references {ref} which does not exist")

    # Every guide should have YAML frontmatter with id, title, options
    for guide_path in sorted(DECISIONS_DIR.glob("*-selection.md")):
        fm = extract_yaml_frontmatter(guide_path)
        if fm is None:
            dc.check(f"{guide_path.name} has YAML frontmatter", False,
                     "Missing YAML frontmatter")
            continue
        dc.check(f"{guide_path.name} has 'id' in frontmatter",
                 "id" in fm, "Missing 'id' field in frontmatter")
        dc.check(f"{guide_path.name} has 'title' in frontmatter",
                 "title" in fm, "Missing 'title' field in frontmatter")
        dc.check(f"{guide_path.name} has 'options' in frontmatter",
                 "options" in fm, "Missing 'options' field in frontmatter")


def check_ingestion_consistency(dc: DriftChecker):
    """Mirroring sources, comparison table columns, and YAML options are
    internally consistent within ingestion-selection.md."""
    print("\n── Ingestion Guide Internal Consistency ──")

    ing_path = DECISIONS_DIR / "ingestion-selection.md"
    content = ing_path.read_text(encoding="utf-8")
    fm = extract_yaml_frontmatter(ing_path)

    if not fm or "options" not in fm:
        dc.check("ingestion guide has options", False, "No YAML options found")
        return

    # YAML option labels should correspond to comparison table columns
    # Labels may differ slightly (e.g., "Data Pipeline" vs "Pipeline",
    # "OneLake Shortcut" vs "Shortcut", "Fabric Link (Dataverse)" vs "Fabric Link")
    yaml_labels = {opt["label"] for opt in fm["options"]}
    table_cols = extract_ingestion_comparison_columns(ing_path)

    # Build a mapping: normalize both to lowercase for flexible matching
    def normalize(s: str) -> str:
        return re.sub(r"\s*\(.*?\)", "", s).strip().lower()

    yaml_normalized = {normalize(entry): entry for entry in yaml_labels}
    table_normalized = {normalize(c): c for c in table_cols}

    # Check each YAML option has a corresponding table column
    unmatched_yaml = []
    for yn, orig in yaml_normalized.items():
        matched = yn in table_normalized
        if not matched:
            # Try substring match (e.g., "data pipeline" matches "pipeline")
            matched = any(yn in tn or tn in yn for tn in table_normalized)
        if not matched:
            unmatched_yaml.append(orig)

    dc.check("every YAML option has a corresponding comparison table column",
             len(unmatched_yaml) == 0,
             f"YAML options with no table column: {sorted(unmatched_yaml)}")

    # Mirroring sources should be consistent across all 3 places
    # 1. Quick reference table
    quick_ref = extract_mirroring_sources(ing_path, "**Mirroring**")
    # 2. Choose MIRRORING when
    choose_when = extract_mirroring_sources(ing_path, "Source is ")
    # 3. Both should have the same set
    diff = quick_ref.symmetric_difference(choose_when)
    dc.check("mirroring sources consistent (quick ref vs Choose when)",
             len(diff) == 0,
             f"Inconsistent mirroring sources: {sorted(diff)}")

    # Check that "Choose when" sections exist for each YAML option
    for opt in fm["options"]:
        label = opt["label"]
        opt_id = opt["id"]
        # Match flexibly: "Choose MIRRORING when", "Choose SHORTCUT when",
        # "Choose Fabric Link when", etc. — check both label and ID
        has_section = bool(re.search(
            rf"###\s+Choose\s+{re.escape(label)}\s+when",
            content, re.IGNORECASE
        ))
        if not has_section:
            # Try matching on ID (e.g., "shortcut" → "SHORTCUT")
            has_section = bool(re.search(
                rf"###\s+Choose\s+{re.escape(opt_id)}\s+when",
                content, re.IGNORECASE
            ))
        if not has_section:
            # Try matching on first word of label (e.g., "Fabric Link (Dataverse)" → "Fabric")
            first_word = label.split()[0]
            has_section = bool(re.search(
                rf"###\s+Choose\s+{re.escape(first_word)}.*when",
                content, re.IGNORECASE
            ))
        dc.check(f"'Choose when' section exists for {label}",
                 has_section,
                 f"Missing '### Choose {label} when:' section")


def check_signal_mapping_validity(dc: DriftChecker):
    """Signal mapping table references only valid task flow IDs and has
    no empty cells."""
    print("\n── Signal Mapping Validity ──")

    canonical = extract_task_flow_ids_from_taskflows_md()
    content = ADVISOR_PATH.read_text(encoding="utf-8")

    in_table = False
    row_count = 0
    invalid_ids = set()
    empty_rows = []
    single_word_flows = {"medallion", "lambda", "translytical", "general"}

    for i, line in enumerate(content.splitlines(), 1):
        if "Signal Words" in line and "Task Flow Candidates" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 5:
                continue
            row_count += 1
            # Check for empty critical cells
            signal_col = cols[1]
            velocity_col = cols[2]
            usecase_col = cols[3]
            candidate_col = cols[4]
            if not signal_col or not velocity_col or not usecase_col:
                empty_rows.append(f"row {row_count} (line {i})")
            # Validate task flow IDs in candidates column
            for token in re.findall(r"[a-z][a-z0-9-]+", candidate_col):
                if "-" in token and len(token) > 3:
                    if token not in canonical:
                        # Allow parenthetical notes
                        if token not in ("multi-workspace", "via", "cross-cutting",
                                         "user-confirmed", "cross-workspace"):
                            invalid_ids.add(token)
                elif token in single_word_flows and token not in canonical:
                    invalid_ids.add(token)
        elif in_table and not line.startswith("|"):
            break

    dc.check("signal mapping table has rows",
             row_count >= 30,
             f"Expected ≥30 signal rows, found {row_count}")

    dc.check("no empty cells in signal mapping table",
             len(empty_rows) == 0,
             f"Empty cells in: {empty_rows}")

    dc.check("all signal task flow IDs are valid",
             len(invalid_ids) == 0,
             f"Invalid task flow IDs in signals: {sorted(invalid_ids)}")


def check_registry_references(dc: DriftChecker):
    """Items referenced in diagrams and ingestion guide exist in the registry."""
    print("\n── Registry Cross-References ──")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    items = registry.get("types", {})
    # Build a set of all known names: fab_type, registry keys, display_names, and aliases (case-insensitive)
    all_known_names = set()
    for k, v in items.items():
        all_known_names.add(k.lower())
        all_known_names.add(v.get("fab_type", k).lower())
        all_known_names.add(v.get("display_name", k).lower())
        for a in v.get("aliases", []):
            all_known_names.add(a.lower())

    # Check diagrams reference known item types (deployment order tables only)
    for diagram_path in sorted(DIAGRAMS_DIR.glob("*.md")):
        if diagram_path.name == "_index.md":
            continue
        content = diagram_path.read_text(encoding="utf-8")
        in_code_block = False
        for line in content.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
            # Only scan inside code blocks (deployment order tables use box-drawing chars)
            if not in_code_block:
                continue
            if ("│" in line or line.startswith("|")) and "Lakehouse" not in line and "Wave" not in line:
                # Extract item types from table cells
                for m in re.finditer(r"\b(Lakehouse|Warehouse|Eventhouse|Notebook|Pipeline|"
                                     r"SemanticModel|Report|Eventstream|KQLDatabase|"
                                     r"SQLDatabase|SQLEndpoint|Environment|SparkJobDefinition|"
                                     r"MLModel|MLExperiment|Activator|DataPipeline|"
                                     r"MirroredDatabase|CopyJob|DataflowGen2)\b", line):
                    item_type = m.group(1)
                    dc.check(
                        f"{diagram_path.stem}: {item_type} in registry",
                        item_type.lower() in all_known_names,
                        f"{item_type} referenced in {diagram_path.name} but not in registry"
                    )

    # Registry should have version metadata
    dc.check("registry has $version field",
             "$version" in registry, "Missing $version in registry")
    dc.check("registry has $cli_version field",
             "$cli_version" in registry, "Missing $cli_version in registry")


def check_integration_first(dc: DriftChecker):
    """Verify Integration First principle is present and no prescriptive
    migration language exists."""
    print("\n── Integration First / Better Together ──")

    advisor_content = ADVISOR_PATH.read_text(encoding="utf-8")

    # Integration First section must exist
    dc.check("Integration First Principle section exists",
             "Integration First" in advisor_content,
             "Missing 'Integration First Principle' section in advisor")

    # No prescriptive migration language in advisor
    # Exclude lines that are RULES telling the advisor NOT to suggest migration
    prescriptive = []
    for i, line in enumerate(advisor_content.splitlines(), 1):
        low = line.lower()
        # Skip rule/boundary lines that tell the advisor what NOT to do
        if any(kw in low for kw in ["never", "do not", "don't", "🚫", "signs of drift"]):
            continue
        for phrase in ["you should migrate", "must migrate", "recommend migrating",
                       "we recommend moving", "move away from", "replace with fabric"]:
            if phrase in low:
                prescriptive.append(f"line {i}: '{phrase}'")

    dc.check("no prescriptive migration language in advisor",
             len(prescriptive) == 0,
             f"Found prescriptive migration language: {prescriptive}")

    # Databricks and Snowflake should be "Better Together"
    for platform in ["Databricks", "Snowflake"]:
        has_better = bool(re.search(
            rf"{platform}.*Better Together", advisor_content, re.IGNORECASE
        ))
        dc.check(f"{platform} framed as Better Together",
                 has_better,
                 f"{platform} signal row missing 'Better Together' framing")

    # "Evolution Paths" not "Migration Paths" in skillset guide
    skillset_path = DECISIONS_DIR / "skillset-selection.md"
    if skillset_path.exists():
        skillset = skillset_path.read_text(encoding="utf-8")
        dc.check("skillset guide uses 'Evolution Paths' not 'Migration Paths'",
                 "Evolution Paths" in skillset and "Migration Paths" not in skillset,
                 "Found 'Migration Paths' — should be 'Evolution Paths'")


# ── main ─────────────────────────────────────────────────────────────

def main():
    import argparse
    if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Documentation drift detection")
    parser.add_argument("--check", action="store_true", help="CI mode: exit 1 on failure")
    parser.add_argument("--verbose", action="store_true", help="Show passing checks too")
    args = parser.parse_args()

    print("Documentation Drift Detection")
    print("=" * 40)

    dc = DriftChecker(verbose=args.verbose or not args.check)

    check_task_flow_coverage(dc)
    check_decision_guides(dc)
    check_ingestion_consistency(dc)
    check_signal_mapping_validity(dc)
    check_registry_references(dc)
    check_integration_first(dc)

    exit_code = dc.report()
    sys.exit(exit_code if args.check else 0)


if __name__ == "__main__":
    main()
