"""
tests/test_api.py — unit tests for FastAPI routes.

Covers all 5 bugs from test report round 2.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.combine import CombineResult

BASE_ELEMENTS = ["fire", "water", "earth", "air"]


@pytest.fixture
def client():
    """Offline client: no Postgres, no Redis, no real logging setup."""
    quiet_redis = MagicMock()
    quiet_redis.set.return_value = True
    quiet_redis.exists.return_value = False
    with (
        patch("src.api.app.setup_logging"),
        patch("src.api.app.init_db"),
        patch("src.api.routes.get_all_elements", return_value=BASE_ELEMENTS),
        patch("src.api.routes._redis", quiet_redis),
        TestClient(create_app()) as c,
    ):
        yield c


# ── /health ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── /combine — happy path ────────────────────────────────────────────────────


@pytest.mark.unit
def test_combine_success(client):
    fake = CombineResult(result="steam", is_new=True, source="ai", elapsed_ms=42.0)
    with patch("src.api.routes.combine", return_value=fake):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200
    data = r.json()
    assert data["result"] == "steam"
    assert data["is_new"] is True
    assert data["source"] == "ai"


# ── BUG-1: same-element validation ──────────────────────────────────────────


@pytest.mark.unit
def test_combine_same_element_rejected(client):
    with patch("src.api.routes.combine") as mock_combine:
        r = client.post("/combine", json={"a": "fire", "b": "fire"})
    assert r.status_code == 422
    assert "same" in r.json()["detail"].lower()
    mock_combine.assert_not_called()


@pytest.mark.unit
def test_combine_same_element_case_insensitive(client):
    with patch("src.api.routes.combine") as mock_combine:
        r = client.post("/combine", json={"a": "Fire", "b": "FIRE"})
    assert r.status_code == 422
    mock_combine.assert_not_called()


# ── BUG-2: /recipes correct row mapping ─────────────────────────────────────


@pytest.mark.unit
def test_get_recipes_correct_mapping(client):
    rows = [
        {"element_a": "air", "element_b": "fire", "result": "smoke"},
        {"element_a": "earth", "element_b": "water", "result": "mud"},
    ]
    with patch("src.api.routes.get_all_recipes", return_value=rows):
        r = client.get("/recipes")
    assert r.status_code == 200
    data = r.json()
    assert data[0] == {"element_a": "air", "element_b": "fire", "result": "smoke"}
    assert data[1] == {"element_a": "earth", "element_b": "water", "result": "mud"}


@pytest.mark.unit
def test_get_recipes_not_placeholder(client):
    rows = [{"element_a": "lava", "element_b": "water", "result": "obsidian"}]
    with patch("src.api.routes.get_all_recipes", return_value=rows):
        r = client.get("/recipes")
    data = r.json()[0]
    assert data["element_a"] != "a"
    assert data["element_b"] != "b"
    assert data["result"] != "result"


# ── BUG-3: source attribution sanity ────────────────────────────────────────


@pytest.mark.unit
def test_source_corrected_when_not_new_but_ai(client):
    fake = CombineResult(result="steam", is_new=False, source="ai", elapsed_ms=10.0)
    with patch("src.api.routes.combine", return_value=fake):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.json()["source"] == "db"


@pytest.mark.unit
def test_source_preserved_when_new_and_ai(client):
    fake = CombineResult(result="steam", is_new=True, source="ai", elapsed_ms=10.0)
    with patch("src.api.routes.combine", return_value=fake):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.json()["source"] == "ai"


@pytest.mark.unit
def test_source_preserved_cache(client):
    fake = CombineResult(result="steam", is_new=False, source="cache", elapsed_ms=3.0)
    with patch("src.api.routes.combine", return_value=fake):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.json()["source"] == "cache"


# ── BUG-4: concurrency lock ──────────────────────────────────────────────────


@pytest.mark.unit
def test_lock_acquired_and_released(client):
    fake = CombineResult(result="steam", is_new=True, source="ai", elapsed_ms=10.0)
    mock_redis = MagicMock()
    mock_redis.set.return_value = True
    mock_redis.exists.return_value = False
    with (
        patch("src.api.routes._redis", mock_redis),
        patch("src.api.routes.combine", return_value=fake),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200
    mock_redis.set.assert_called_once()
    mock_redis.delete.assert_called_once()


@pytest.mark.unit
def test_lock_wait_then_proceed(client):
    fake = CombineResult(result="steam", is_new=False, source="cache", elapsed_ms=5.0)
    mock_redis = MagicMock()
    mock_redis.set.return_value = False
    mock_redis.exists.return_value = False
    with (
        patch("src.api.routes._redis", mock_redis),
        patch("src.api.routes.combine", return_value=fake),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200


@pytest.mark.unit
def test_lock_timeout_returns_503(client):
    mock_redis = MagicMock()
    mock_redis.set.return_value = False
    mock_redis.exists.return_value = True
    with (
        patch("src.api.routes._redis", mock_redis),
        patch("src.api.routes._LOCK_TIMEOUT", 0.01),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 503


# ── Input validation ─────────────────────────────────────────────────────────


@pytest.mark.unit
def test_combine_empty_element(client):
    r = client.post("/combine", json={"a": "", "b": "water"})
    assert r.status_code == 422


@pytest.mark.unit
def test_combine_too_long(client):
    r = client.post("/combine", json={"a": "x" * 31, "b": "water"})
    assert r.status_code == 422


@pytest.mark.unit
def test_combine_invalid_chars(client):
    r = client.post("/combine", json={"a": "fire!!", "b": "water"})
    assert r.status_code == 422


@pytest.mark.unit
def test_combine_server_error(client):
    with patch("src.api.routes.combine", side_effect=RuntimeError("ollama down")):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 500


# ── /elements ────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_get_elements(client):
    with patch(
        "src.api.routes.get_all_elements",
        return_value=["fire", "water", "earth", "air"],
    ):
        r = client.get("/elements")
    assert r.status_code == 200
    names = [e["name"] for e in r.json()]
    assert set(names) == {"fire", "water", "earth", "air"}


@pytest.mark.unit
def test_get_elements_db_error(client):
    with patch("src.api.routes.get_all_elements", side_effect=Exception("db down")):
        r = client.get("/elements")
    assert r.status_code == 500


@pytest.mark.unit
def test_get_recipes_db_error(client):
    with patch("src.api.routes.get_all_recipes", side_effect=Exception("db down")):
        r = client.get("/recipes")
    assert r.status_code == 500


# ── Element existence validation ─────────────────────────────────────────────


@pytest.mark.unit
def test_combine_unknown_element_rejected(client):
    """Panda + air must 404 if panda not in system."""
    with patch(
        "src.api.routes.get_all_elements",
        return_value=["fire", "water", "earth", "air"],
    ):
        r = client.post("/combine", json={"a": "panda", "b": "air"})
    assert r.status_code == 404
    assert "panda" in r.json()["detail"]


@pytest.mark.unit
def test_combine_both_elements_unknown(client):
    with patch(
        "src.api.routes.get_all_elements",
        return_value=["fire", "water", "earth", "air"],
    ):
        r = client.post("/combine", json={"a": "panda", "b": "dragon"})
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert "panda" in detail
    assert "dragon" in detail


@pytest.mark.unit
def test_combine_known_elements_pass_check(client):
    """Fire + water are both known — should proceed to combine."""
    fake = CombineResult(result="steam", is_new=False, source="cache", elapsed_ms=3.0)
    with (
        patch(
            "src.api.routes.get_all_elements",
            return_value=["fire", "water", "earth", "air"],
        ),
        patch("src.api.routes.combine", return_value=fake),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200


@pytest.mark.unit
def test_lock_uses_shared_redis_client():
    """Regression: a bad import once left _redis=None, silently disabling the lock."""
    from src.api import routes
    from src.cache.connection import get_redis

    assert routes._redis is get_redis()


@pytest.mark.unit
def test_lock_fails_open_when_redis_is_down(client):
    fake = CombineResult(result="steam", is_new=True, source="ai", elapsed_ms=10.0)
    broken_redis = MagicMock()
    broken_redis.set.side_effect = ConnectionError("redis down")
    broken_redis.delete.side_effect = ConnectionError("redis down")
    with (
        patch("src.api.routes._redis", broken_redis),
        patch("src.api.routes.combine", return_value=fake),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200


@pytest.mark.unit
def test_lock_wait_fails_open_when_redis_is_down(client):
    fake = CombineResult(result="steam", is_new=False, source="cache", elapsed_ms=5.0)
    broken_redis = MagicMock()
    broken_redis.set.return_value = False
    broken_redis.exists.side_effect = ConnectionError("redis down")
    with (
        patch("src.api.routes._redis", broken_redis),
        patch("src.api.routes.combine", return_value=fake),
    ):
        r = client.post("/combine", json={"a": "fire", "b": "water"})
    assert r.status_code == 200
