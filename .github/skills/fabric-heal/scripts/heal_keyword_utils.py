#!/usr/bin/env python3
"""Keyword gap-analysis helpers for heal-orchestrator."""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

_STOPWORDS = frozenset({
    "we", "our", "the", "a", "an", "to", "and", "or", "in", "of",
    "for", "is", "it", "that", "with", "on", "at", "from", "by",
    "but", "not", "are", "was", "be", "have", "has", "had", "do",
    "does", "did", "will", "can", "could", "should", "would", "may",
    "might", "shall", "need", "want", "like", "just", "also",
    "they", "them", "their", "this", "these", "those", "some",
    "any", "all", "each", "every", "both", "either", "neither",
    "i", "me", "my", "you", "your", "he", "she", "his", "her",
    "its", "us", "we're", "don't", "can't", "won't", "doesn't",
    "didn't", "isn't", "aren't", "haven't", "hasn't", "wasn't",
    "weren't", "how", "what", "when", "where", "which", "who",
    "re", "ve", "ll", "no", "yes", "so", "very", "too", "more",
    "most", "much", "many", "few", "than", "then", "now",
    "about", "into", "over", "after", "before", "between",
    "through", "during", "without", "within", "across",
    "per", "get", "gets", "getting", "been", "being",
    "same", "new", "one", "two", "three", "first", "last",
    "using", "use", "used", "currently", "current", "data",
    "still", "already", "right", "back", "way", "keep",
})

_GENERIC_UNCOVERED_TERMS = frozenset({
    "need", "needs", "team", "teams", "data", "data from", "from data",
    "only", "size", "global", "real", "time", "real time", "batch",
    "daily", "weekly", "monthly", "code", "some code",
    "retailer", "retailer our", "skill", "level",
})


def _is_generic_uncovered_term(term: str) -> bool:
    t = term.strip().lower()
    if not t:
        return True
    if t in _GENERIC_UNCOVERED_TERMS:
        return True
    tokens = t.split()
    if all(tok in _STOPWORDS for tok in tokens):
        return True
    if len(tokens) == 1 and len(t) <= 4:
        return True
    return False


def _load_existing_keywords(signal_mapper_path: Path) -> set[str]:
    """Load canonical keyword inventory from signal-mapper runtime categories."""
    try:
        spec = importlib.util.spec_from_file_location(
            "signal_mapper_runtime",
            signal_mapper_path,
        )
        if spec is None or spec.loader is None:
            return set()
        module = importlib.util.module_from_spec(spec)
        # Ensure decorators/types relying on module lookup can resolve __module__.
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        categories = getattr(module, "CATEGORIES", ())
        keywords: set[str] = set()
        for cat in categories:
            for kw in getattr(cat, "keywords", ()):
                keywords.add(str(kw).lower())
        return keywords
    except Exception as e:
        print(f"⚠ keyword inventory load failed: {e}", file=sys.stderr)
        return set()


def _normalize_uncovered_term(term: str) -> str:
    """Normalize uncovered-term fragments into canonical phrase forms."""
    t = re.sub(r"\s+", " ", term.strip().lower())
    if not t:
        return t

    connector_rewrites = {
        "databricks and": "databricks and adls",
        "and adls": "databricks and adls",
        "erp and": "erp and crm",
        "and crm": "erp and crm",
    }
    t = connector_rewrites.get(t, t)

    phrase_aliases = {
        "real time": "real-time",
        "near real time": "near-real-time",
        "on prem sql": "on-prem sql",
        "on prem sql server": "on-prem sql server",
        "from erp and": "data from erp",
        "erp source": "data from erp",
        "customer attrition": "customer churn",
        "retention risk": "customer churn",
        "python and": "python and sql",
        "and sql": "python and sql",
    }
    return phrase_aliases.get(t, t)


def find_uncovered_keywords(problems: list[dict], signal_mapper_path: Path) -> list[str]:
    """Find words in problem texts that aren't matched by signal mapper keywords."""
    existing_kws = _load_existing_keywords(signal_mapper_path)

    word_freq: Counter = Counter()
    for p in problems:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", p["text"].lower())
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)]
        for w in words:
            norm = _normalize_uncovered_term(w)
            if norm and norm not in _STOPWORDS and norm not in existing_kws:
                word_freq[norm] += 1
        for b in bigrams:
            norm = _normalize_uncovered_term(b)
            if norm and norm not in existing_kws:
                word_freq[norm] += 1
        for t in trigrams:
            norm = _normalize_uncovered_term(t)
            if norm and norm not in existing_kws:
                word_freq[norm] += 1

    uncovered = [word for word, count in word_freq.most_common(30) if count >= 2 and len(word) > 3]
    uncovered = [u for u in uncovered if not _is_generic_uncovered_term(u)]
    return uncovered[:15]
