"""
Shared deployment-order loading utilities for task-flows scripts.

Primary source: _shared/registry/deployment-order.json (deterministic JSON)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

# Path to the canonical deployment order registry
_REGISTRY_PATH = Path(__file__).parent.parent / "registry" / "deployment-order.json"

# Cache for loaded registry
_registry_cache: dict | None = None


class DeploymentItem(TypedDict, total=False):
    """Schema for a deployment order item."""
    order: str
    itemType: str
    skillset: str
    dependsOn: list[str]
    requiredFor: list[str]
    alternativeGroup: str
    notes: str


class TaskFlowData(TypedDict, total=False):
    """Schema for a task flow entry in the registry."""
    primaryStorage: str
    items: list[DeploymentItem]


def load_registry() -> dict[str, TaskFlowData]:
    """Load the deployment order registry JSON.
    
    Returns a dict keyed by task flow ID (e.g., 'medallion', 'lambda').
    """
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    
    if not _REGISTRY_PATH.exists():
        _registry_cache = {}
        return _registry_cache
    
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    _registry_cache = data.get("taskFlows", {})
    return _registry_cache


def get_deployment_items(task_flow: str) -> list[DeploymentItem]:
    """Get deployment items for a task flow from the JSON registry.
    
    Args:
        task_flow: Task flow ID (e.g., 'medallion', 'lambda').
                   Case-insensitive — normalized to lowercase internally.
        
    Returns:
        List of deployment items with order, itemType, dependsOn, etc.
    """
    registry = load_registry()
    flow_data = registry.get(task_flow.lower(), {})
    return flow_data.get("items", [])
