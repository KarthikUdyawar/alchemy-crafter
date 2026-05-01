"""
Shared pytest fixtures — all offline, no real services needed.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ── DB fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db(mocker):
    """Patch all DB helpers to avoid real Postgres."""
    return {
        "get_recipe": mocker.patch("src.combine.get_recipe", return_value=None),
        "save_recipe": mocker.patch("src.combine.save_recipe"),
        "save_element": mocker.patch("src.combine.save_element", return_value=True),
    }


# ── Cache fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def mock_cache(mocker):
    """Patch all Redis helpers — default: all misses."""
    return {
        "get_cached_recipe": mocker.patch(
            "src.combine.get_cached_recipe", return_value=None
        ),
        "set_cached_recipe": mocker.patch("src.combine.set_cached_recipe"),
        "add_to_context": mocker.patch("src.combine.add_to_context"),
        "reset_fail": mocker.patch("src.combine.reset_fail"),
        "increment_fail": mocker.patch("src.combine.increment_fail", return_value=1),
    }


# ── AI fixture ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ai(mocker):
    """Patch Ollama — default: returns 'steam'."""
    return mocker.patch("src.combine.generate_recipe", return_value="steam")


# ── Convenience: full pipeline mocked ────────────────────────────────────────


@pytest.fixture
def mocked_pipeline(mock_db, mock_cache, mock_ai):
    """All external I/O patched. Useful for combine() unit tests."""
    return {"db": mock_db, "cache": mock_cache, "ai": mock_ai}
