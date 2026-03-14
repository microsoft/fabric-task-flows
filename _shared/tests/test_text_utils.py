"""Tests for text_utils.py — verifies slugify and slugify_phase transforms."""

from lib.text_utils import slugify, slugify_phase


# ── slugify: basic conversion ─────────────────────────────────────────────


def test_slugify_basic():
    assert slugify("My Cool Project!") == "my-cool-project"


def test_slugify_single_word():
    assert slugify("Hello") == "hello"


def test_slugify_already_slugified():
    assert slugify("already-slugified") == "already-slugified"


# ── slugify: whitespace handling ──────────────────────────────────────────


def test_slugify_leading_trailing_whitespace():
    assert slugify("  hello  ") == "hello"


def test_slugify_multiple_spaces():
    assert slugify("a   b   c") == "a-b-c"


def test_slugify_tabs_and_newlines():
    assert slugify("\thello\nworld\t") == "hello-world"


# ── slugify: special characters and symbols ───────────────────────────────


def test_slugify_symbols():
    assert slugify("  Hello   World  ") == "hello-world"


def test_slugify_punctuation():
    assert slugify("hello, world! how's it?") == "hello-world-hows-it"


def test_slugify_mixed_symbols():
    assert slugify("foo@bar#baz$qux") == "foobarbazqux"


def test_slugify_numbers_preserved():
    assert slugify("Phase 3 Setup") == "phase-3-setup"


def test_slugify_preserves_existing_hyphens():
    assert slugify("a---b___c...d") == "a---bcd"


def test_slugify_collapses_whitespace_to_single_hyphen():
    assert slugify("a   b   c") == "a-b-c"


# ── slugify: edge cases ──────────────────────────────────────────────────


def test_slugify_empty_string():
    assert slugify("") == ""


def test_slugify_only_whitespace():
    assert slugify("   ") == ""


def test_slugify_only_symbols():
    assert slugify("@#$%^&*") == ""


def test_slugify_single_char():
    assert slugify("A") == "a"


def test_slugify_single_number():
    assert slugify("7") == "7"


def test_slugify_vs_slugify_phase_hyphens():
    """slugify preserves hyphens; slugify_phase collapses them."""
    assert slugify("a--b") == "a--b"
    assert slugify_phase("a--b") == "a-b"


# ── slugify_phase: basic conversion ──────────────────────────────────────


def test_slugify_phase_basic():
    assert slugify_phase("Phase 1: Foundation") == "phase-1-foundation"


def test_slugify_phase_whitespace_and_symbols():
    assert slugify_phase("  ML & Analytics  ") == "ml-analytics"


def test_slugify_phase_single_word():
    assert slugify_phase("Ingestion") == "ingestion"


def test_slugify_phase_already_slugified():
    assert slugify_phase("already-slugified") == "already-slugified"


# ── slugify_phase: edge cases ────────────────────────────────────────────


def test_slugify_phase_empty_string():
    assert slugify_phase("") == ""


def test_slugify_phase_only_symbols():
    assert slugify_phase("!@#") == ""


def test_slugify_phase_consecutive_separators():
    assert slugify_phase("a :: b -- c") == "a-b-c"


def test_slugify_phase_numbers():
    assert slugify_phase("Step 2b - Transform") == "step-2b-transform"


# ── escape_for_python_string ─────────────────────────────────────────────

from lib.text_utils import escape_for_python_string


def test_escape_for_python_string_basic():
    assert escape_for_python_string('hello') == 'hello'


def test_escape_for_python_string_quotes():
    assert escape_for_python_string('say "hi"') == 'say \\"hi\\"'


def test_escape_for_python_string_backslash():
    assert escape_for_python_string('path\\to\\file') == 'path\\\\to\\\\file'


def test_escape_for_python_string_newline():
    assert escape_for_python_string('line1\nline2') == 'line1\\nline2'
