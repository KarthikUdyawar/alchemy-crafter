"""Core combine pipeline — validation → cache → db → ai → persist."""

import time

from src.ai import generate_recipe
from src.cache import (
    add_to_context,
    get_cached_recipe,
    increment_fail,
    reset_fail,
    set_cached_recipe,
)
from src.db import get_recipe, save_element, save_recipe
from src.db.queries import get_discovered, mark_discovered
from src.logger import get_logger
from src.validation import (
    UnknownElementError,
    ValidationError,
    validate_element,
    validate_inputs,
)

log = get_logger("combine")

_AI_RETRY_LIMIT = 3  # max AI retries if result fails validation


class CombineResult:
    def __init__(self, result: str, is_new: bool, source: str, elapsed_ms: float) -> None:
        self.result = result
        self.is_new = is_new
        self.source = source  # "cache" | "db" | "ai"
        self.elapsed_ms = elapsed_ms  # total wall time

    def __repr__(self) -> str:
        return (
            f"<CombineResult result={self.result!r} "
            f"is_new={self.is_new} source={self.source} "
            f"elapsed={self.elapsed_ms}ms>"
        )


def combine(raw_a: str, raw_b: str) -> CombineResult:
    """Run the full combine pipeline.

    1. Validate + normalise inputs (sorted); both must be discovered
    2. Redis cache
    3. Postgres
    4. Ollama (with validation retry)
    5. Persist → DB + cache + context
    """
    t0 = time.monotonic()

    # 1. Validate inputs
    a, b = validate_inputs(raw_a, raw_b)
    log.debug("combine(%s, %s)", a, b)

    discovered = set(get_discovered())
    unknown = [name for name in (a, b) if name not in discovered]
    if unknown:
        missing = ", ".join(unknown)
        raise UnknownElementError(f"Unknown element(s): {missing}. Discover them first.")

    def _ms() -> int:
        return int((time.monotonic() - t0) * 1000)

    # 2. Cache
    cached = get_cached_recipe(a, b)
    if cached:
        add_to_context(cached)
        reset_fail(a, b)
        log.debug("cache hit → %s (%dms)", cached, _ms())
        return CombineResult(cached, is_new=False, source="cache", elapsed_ms=_ms())

    # 3. DB
    stored = get_recipe(a, b)
    if stored:
        mark_discovered(stored)
        set_cached_recipe(a, b, stored)
        add_to_context(stored)
        reset_fail(a, b)
        log.debug("db hit → %s (%dms)", stored, _ms())
        return CombineResult(stored, is_new=False, source="db", elapsed_ms=_ms())

    # 4. Ollama — retry loop if AI output fails validation
    result_name: str | None = None
    last_err: str = "AI failed to generate a result."

    for attempt in range(1, _AI_RETRY_LIMIT + 1):
        raw = generate_recipe(a, b)
        if raw is None:
            last_err = "AI did not respond. Try again."
            break
        try:
            result_name = validate_element(raw, inputs=(a, b))
            break
        except ValidationError as e:
            last_err = str(e)
            log.warning("AI result invalid (attempt %d): %s → %s", attempt, raw, e)

    if result_name is None:
        increment_fail(a, b)
        raise ValidationError(last_err)

    # 5. Persist
    is_new = save_element(result_name)
    save_recipe(a, b, result_name)
    mark_discovered(result_name)
    set_cached_recipe(a, b, result_name)
    add_to_context(result_name)
    reset_fail(a, b)

    log.info("ai → %s+%s = %s  new=%s  %dms", a, b, result_name, is_new, _ms())
    return CombineResult(result_name, is_new=is_new, source="ai", elapsed_ms=_ms())
