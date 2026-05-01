"""
Redis cache helpers.

Key schema
──────────
recipe:<a>:<b>          → result string
context:global          → list  (recent element names, capped)
fail:<a>:<b>            → int   (failed combination attempts)
"""

from src.cache.connection import get_redis
from src.config import config


# ── Internal key builders ────────────────────────────────────────────────────


def _recipe_key(a: str, b: str) -> str:
    """Inputs must already be normalised (sorted)."""
    return f"recipe:{a}:{b}"


def _fail_key(a: str, b: str) -> str:
    return f"fail:{a}:{b}"


CONTEXT_KEY = "context:global"


# ── Recipe cache ─────────────────────────────────────────────────────────────


def get_cached_recipe(a: str, b: str) -> str | None:
    """Return cached result or None on miss."""
    try:
        return get_redis().get(_recipe_key(a, b))
    except Exception:
        return None


def set_cached_recipe(a: str, b: str, result: str) -> None:
    """Cache a recipe with the configured TTL."""
    try:
        get_redis().setex(_recipe_key(a, b), config.CACHE_TTL, result)
    except Exception:
        pass  # cache failure is non-fatal


def delete_cached_recipe(a: str, b: str) -> None:
    """Evict a recipe from cache (useful for testing / admin)."""
    try:
        get_redis().delete(_recipe_key(a, b))
    except Exception:
        pass


# ── Context memory (recent elements for AI prompt) ───────────────────────────


def add_to_context(element: str) -> None:
    """
    Push element to the front of the global context list.
    Keeps the list trimmed to CONTEXT_SIZE entries.
    """
    try:
        r = get_redis()
        r.lpush(CONTEXT_KEY, element)
        r.ltrim(CONTEXT_KEY, 0, config.CONTEXT_SIZE - 1)
    except Exception:
        pass


def get_recent_context(limit: int | None = None) -> list[str]:
    """Return the most recent elements seen (up to limit or CONTEXT_SIZE)."""
    n = limit if limit is not None else config.CONTEXT_SIZE
    try:
        return get_redis().lrange(CONTEXT_KEY, 0, n - 1)
    except Exception:
        return []


# ── Fail counter ─────────────────────────────────────────────────────────────


def increment_fail(a: str, b: str) -> int:
    """Increment and return the fail counter for a combination."""
    try:
        r = get_redis()
        key = _fail_key(a, b)
        count = r.incr(key)
        r.expire(key, config.CACHE_TTL)
        return count
    except Exception:
        return 0


def get_fail_count(a: str, b: str) -> int:
    """Return current fail count for a combination (0 if unknown)."""
    try:
        val = get_redis().get(_fail_key(a, b))
        return int(val) if val else 0
    except Exception:
        return 0


def reset_fail(a: str, b: str) -> None:
    """Clear the fail counter once a result is found."""
    try:
        get_redis().delete(_fail_key(a, b))
    except Exception:
        pass
