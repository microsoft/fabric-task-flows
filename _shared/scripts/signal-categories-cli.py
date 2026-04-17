#!/usr/bin/env python3
"""
Manage signal-category keywords in _shared/registry/signal-categories.json.

Usage examples:
  python _shared/scripts/signal-categories-cli.py list-categories
  python _shared/scripts/signal-categories-cli.py list-keywords --category 7 --tier moderate
  python _shared/scripts/signal-categories-cli.py add --category 7 --tier moderate --keyword "unity catalog"
  python _shared/scripts/signal-categories-cli.py remove --category 7 --tier weak --keyword "unity catalog"
  python _shared/scripts/signal-categories-cli.py move --category 7 --from-tier weak --to-tier moderate --keyword "unity catalog"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import bootstrap  # noqa: F401
from paths import REPO_ROOT  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "_shared" / "registry" / "signal-categories.json"
VALID_TIERS = ("strong", "moderate", "weak")


def _load_registry() -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: dict) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _find_category(data: dict, category_id: int) -> dict:
    for cat in data.get("categories", []):
        if cat.get("id") == category_id:
            return cat
    raise ValueError(f"Category id {category_id} not found.")


def _normalize_keyword(keyword: str) -> str:
    k = " ".join(keyword.strip().split())
    if not k:
        raise ValueError("Keyword cannot be empty.")
    return k


def _validate_tier(tier: str) -> str:
    if tier not in VALID_TIERS:
        raise ValueError(f"Tier must be one of: {', '.join(VALID_TIERS)}")
    return tier


def cmd_list_categories(data: dict, _args: argparse.Namespace) -> int:
    for cat in data.get("categories", []):
        print(f"{cat['id']:>2}  {cat['name']}")
    return 0


def cmd_list_keywords(data: dict, args: argparse.Namespace) -> int:
    cat = _find_category(data, args.category)
    if args.tier:
        tier = _validate_tier(args.tier)
        for kw in cat["keywords"].get(tier, []):
            print(kw)
        return 0

    for tier in VALID_TIERS:
        print(f"[{tier}]")
        for kw in cat["keywords"].get(tier, []):
            print(f"  - {kw}")
    return 0


def cmd_add(data: dict, args: argparse.Namespace) -> int:
    cat = _find_category(data, args.category)
    tier = _validate_tier(args.tier)
    keyword = _normalize_keyword(args.keyword)
    kws = cat["keywords"].setdefault(tier, [])
    if keyword in kws:
        print(f"Already exists in category {args.category} {tier}: {keyword}")
        return 0
    kws.append(keyword)
    _save_registry(data)
    print(f"Added to category {args.category} {tier}: {keyword}")
    return 0


def cmd_remove(data: dict, args: argparse.Namespace) -> int:
    cat = _find_category(data, args.category)
    tier = _validate_tier(args.tier)
    keyword = _normalize_keyword(args.keyword)
    kws = cat["keywords"].setdefault(tier, [])
    if keyword not in kws:
        print(f"Not found in category {args.category} {tier}: {keyword}")
        return 1
    kws.remove(keyword)
    _save_registry(data)
    print(f"Removed from category {args.category} {tier}: {keyword}")
    return 0


def cmd_move(data: dict, args: argparse.Namespace) -> int:
    cat = _find_category(data, args.category)
    from_tier = _validate_tier(args.from_tier)
    to_tier = _validate_tier(args.to_tier)
    keyword = _normalize_keyword(args.keyword)
    if from_tier == to_tier:
        raise ValueError("from-tier and to-tier must differ.")

    src = cat["keywords"].setdefault(from_tier, [])
    dst = cat["keywords"].setdefault(to_tier, [])
    if keyword not in src:
        print(f"Not found in category {args.category} {from_tier}: {keyword}")
        return 1
    src.remove(keyword)
    if keyword not in dst:
        dst.append(keyword)
    _save_registry(data)
    print(f"Moved category {args.category}: {keyword} ({from_tier} -> {to_tier})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Signal categories keyword helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-categories", help="List category ids and names")

    p_list = sub.add_parser("list-keywords", help="List keywords for a category")
    p_list.add_argument("--category", type=int, required=True, help="Category id")
    p_list.add_argument("--tier", choices=VALID_TIERS, help="Optional tier filter")

    p_add = sub.add_parser("add", help="Add keyword to category+tier")
    p_add.add_argument("--category", type=int, required=True, help="Category id")
    p_add.add_argument("--tier", choices=VALID_TIERS, required=True, help="Tier")
    p_add.add_argument("--keyword", required=True, help="Keyword/phrase")

    p_remove = sub.add_parser("remove", help="Remove keyword from category+tier")
    p_remove.add_argument("--category", type=int, required=True, help="Category id")
    p_remove.add_argument("--tier", choices=VALID_TIERS, required=True, help="Tier")
    p_remove.add_argument("--keyword", required=True, help="Keyword/phrase")

    p_move = sub.add_parser("move", help="Move keyword between tiers")
    p_move.add_argument("--category", type=int, required=True, help="Category id")
    p_move.add_argument("--from-tier", choices=VALID_TIERS, required=True, help="Source tier")
    p_move.add_argument("--to-tier", choices=VALID_TIERS, required=True, help="Destination tier")
    p_move.add_argument("--keyword", required=True, help="Keyword/phrase")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    data = _load_registry()

    handlers = {
        "list-categories": cmd_list_categories,
        "list-keywords": cmd_list_keywords,
        "add": cmd_add,
        "remove": cmd_remove,
        "move": cmd_move,
    }
    try:
        return handlers[args.command](data, args)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
