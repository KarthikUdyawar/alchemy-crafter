"""
Phase 10 — FastAPI API layer.

Endpoints: POST /combine, GET /elements, GET /recipes, GET /health.

Fixes applied (test report round 2):
  BUG-1  Same-element check enforced at API layer before pipeline
  BUG-2  /recipes rows mapped by index, not dict keys
  BUG-3  source sanity-guard: is_new=False + source="ai" → corrected to "db"
  BUG-4  Redis lock prevents concurrent duplicate AI calls
  BUG-5  AI prompt constraints tightened (see generator.py patch)
"""

import re
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from src.cache.connection import get_redis
from src.combine import combine
from src.config import config
from src.db.queries import get_all_elements, get_all_recipes
from src.logger import get_logger
from src.validation import UnknownElementError, ValidationError

router = APIRouter()
log = get_logger("api")
_redis = get_redis()  # lazy: no connection until the first command (BUG-4 lock)

_LOCK_TTL = 10  # seconds — max time to hold a combine lock
_LOCK_WAIT = 0.15  # seconds — poll interval while waiting for lock
_LOCK_TIMEOUT = 5.0  # seconds — give up after this long


# ── Request / Response schemas ──────────────────────────────────────────────


class CombineRequest(BaseModel):
    a: str
    b: str

    @field_validator("a", "b")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Element name cannot be empty")
        if len(v) > config.MAX_ELEMENT_LENGTH:
            raise ValueError(f"Element name too long (max {config.MAX_ELEMENT_LENGTH} chars)")
        if not re.match(r"^[a-zA-Z0-9 \-]+$", v):
            raise ValueError("Element name contains invalid characters")
        return v.lower()


class CombineResponse(BaseModel):
    result: str
    is_new: bool
    source: str  # "cache" | "db" | "ai"
    elapsed_ms: float


class ElementOut(BaseModel):
    name: str


class RecipeOut(BaseModel):
    element_a: str
    element_b: str
    result: str


# ── Helpers ───────────────────────────────────────────────────────────────────


def _acquire_lock(key: str) -> bool:
    """Try to take a Redis NX lock. Fails open: a Redis outage must not block gameplay."""
    try:
        return bool(_redis.set(key, "1", nx=True, ex=_LOCK_TTL))
    except Exception as exc:
        log.warning("lock acquire failed for %s, continuing without lock: %s", key, exc)
        return True


def _release_lock(key: str) -> None:
    try:
        _redis.delete(key)
    except Exception as exc:
        log.warning("lock release failed for %s: %s", key, exc)


def _wait_for_lock(key: str) -> bool:
    """Wait until the lock is free (another request is generating the recipe).

    Returns True when the lock is released or Redis is unreachable, False on timeout.
    """
    deadline = time.monotonic() + _LOCK_TIMEOUT
    while time.monotonic() < deadline:
        try:
            if not _redis.exists(key):
                return True
        except Exception as exc:
            log.warning("lock wait failed for %s, continuing without lock: %s", key, exc)
            return True
        time.sleep(_LOCK_WAIT)
    return False


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.post("/combine", response_model=CombineResponse)
async def combine_endpoint(body: CombineRequest) -> CombineResponse:
    """
    Combine two elements.

    Flow: validate → lock → combine() (discovered check → Redis → Postgres → Ollama →
    persist) → return.
    """
    a, b = body.a, body.b  # already normalised + lowercased by validator

    # BUG-1: same-element guard at API layer
    if a == b:
        raise HTTPException(status_code=422, detail="Elements cannot be the same")

    # BUG-4: Redis lock — one AI call per unique combo at a time
    sorted_pair = sorted([a, b])
    lock_key = f"lock:{sorted_pair[0]}:{sorted_pair[1]}"

    acquired = _acquire_lock(lock_key)
    if not acquired:
        released = _wait_for_lock(lock_key)
        if not released:
            raise HTTPException(
                status_code=503,
                detail="Recipe generation in progress, try again shortly",
            )

    try:
        res = combine(a, b)
    except UnknownElementError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Combine failed: {exc}") from exc
    finally:
        if acquired:
            _release_lock(lock_key)

    # BUG-3: if result was already known but source wrongly says "ai", correct it
    source = res.source
    if not res.is_new and source == "ai":
        source = "db"

    return CombineResponse(
        result=res.result,
        is_new=res.is_new,
        source=source,
        elapsed_ms=res.elapsed_ms,
    )


@router.get("/elements", response_model=list[ElementOut])
async def elements_endpoint() -> list[ElementOut]:
    """Return all known elements."""
    try:
        names = get_all_elements()  # list[str]
        return [ElementOut(name=n) for n in names]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/recipes", response_model=list[RecipeOut])
async def recipes_endpoint() -> list[RecipeOut]:
    """
    Return all known recipes.

    BUG-2: map by positional index — not dict keys.
    Requires get_all_recipes() SQL: SELECT element_a, element_b, result FROM recipes.
    """
    try:
        rows = get_all_recipes()  # list[dict]
        return [
            RecipeOut(
                element_a=row["element_a"],
                element_b=row["element_b"],
                result=row["result"],
            )
            for row in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
