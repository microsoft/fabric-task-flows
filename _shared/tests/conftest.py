"""Shared pytest fixtures for task-flows test suite."""
from __future__ import annotations

import json
import pytest
from pathlib import Path


@pytest.fixture
def mock_repo(tmp_path):
    """Scaffold a minimal project directory structure for testing.

    Creates:
        tmp_path/
        ├── _shared/registry/item-type-registry.json (minimal)
        ├── _shared/lib/
        ├── _projects/test-project/
        │   ├── docs/
        │   ├── deploy/
        │   └── docs/decisions/
        └── .github/skills/
    """
    # Create directory structure
    (tmp_path / "_shared" / "registry").mkdir(parents=True)
    (tmp_path / "_shared" / "lib").mkdir(parents=True)
    (tmp_path / "_projects" / "test-project" / "docs").mkdir(parents=True)
    (tmp_path / "_projects" / "test-project" / "deploy").mkdir(parents=True)
    (tmp_path / "_projects" / "test-project" / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / ".github" / "skills").mkdir(parents=True)

    # Write minimal registry
    registry = {
        "types": {
            "Lakehouse": {
                "fab_type": "Lakehouse",
                "display_name": "Lakehouse",
                "api_path": "lakehouses",
                "phase": "Foundation",
                "phase_order": 1,
                "task_type": "store data",
                "aliases": ["lakehouse"],
                "rest_api": {"creatable": True, "definition": True},
                "availability": "general availability",
                "notes": ""
            },
            "Notebook": {
                "fab_type": "Notebook",
                "display_name": "Notebook",
                "api_path": "notebooks",
                "phase": "Processing",
                "phase_order": 3,
                "task_type": "prepare data",
                "aliases": ["notebook", "spark notebook"],
                "rest_api": {"creatable": True, "definition": True},
                "availability": "general availability",
                "notes": ""
            }
        }
    }
    (tmp_path / "_shared" / "registry" / "item-type-registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def sample_handoff(tmp_path):
    """Write a minimal architecture-handoff.md and return its path.

    Contains items_to_deploy and deployment_waves YAML blocks.
    """
    content = """---
project: test-project
task_flow: medallion
workspace: test-workspace
---

# Architecture Handoff

```yaml
items_to_deploy:
  - name: raw_lakehouse
    type: Lakehouse
    description: Raw landing zone
  - name: transform_notebook
    type: Notebook
    description: Bronze to silver transform
    depends_on: [raw_lakehouse]
```

```yaml
deployment_waves:
  - wave: 1
    items: [raw_lakehouse]
  - wave: 2
    items: [transform_notebook]
```
"""
    path = tmp_path / "architecture-handoff.md"
    path.write_text(content, encoding="utf-8")
    return path
