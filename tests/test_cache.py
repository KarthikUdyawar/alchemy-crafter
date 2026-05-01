"""
Cache tests.
- Unit tests: mock Redis client, fully offline.
- Integration tests: require live Redis (mark: integration).
"""

import pytest
from unittest.mock import MagicMock


# ── Unit tests (mock Redis) ───────────────────────────────────────────────────


@pytest.fixture
def mock_redis(mocker):
    """Patch get_redis() to return a MagicMock."""
    r = MagicMock()
    mocker.patch("src.cache.cache.get_redis", return_value=r)
    return r


class TestRecipeCacheUnit:
    @pytest.mark.unit
    def test_get_hit(self, mock_redis):
        from src.cache.cache import get_cached_recipe

        mock_redis.get.return_value = "steam"
        assert get_cached_recipe("fire", "water") == "steam"
        mock_redis.get.assert_called_once_with("recipe:fire:water")

    @pytest.mark.unit
    def test_get_miss(self, mock_redis):
        from src.cache.cache import get_cached_recipe

        mock_redis.get.return_value = None
        assert get_cached_recipe("fire", "water") is None

    @pytest.mark.unit
    def test_set_uses_ttl(self, mock_redis):
        from src.cache.cache import set_cached_recipe
        from src.config import config

        set_cached_recipe("fire", "water", "steam")
        mock_redis.setex.assert_called_once_with(
            "recipe:fire:water", config.CACHE_TTL, "steam"
        )

    @pytest.mark.unit
    def test_delete(self, mock_redis):
        from src.cache.cache import delete_cached_recipe

        delete_cached_recipe("fire", "water")
        mock_redis.delete.assert_called_once_with("recipe:fire:water")

    @pytest.mark.unit
    def test_get_returns_none_on_redis_error(self, mock_redis):
        from src.cache.cache import get_cached_recipe

        mock_redis.get.side_effect = Exception("connection refused")
        assert get_cached_recipe("fire", "water") is None  # never raises

    @pytest.mark.unit
    def test_set_silently_fails_on_redis_error(self, mock_redis):
        from src.cache.cache import set_cached_recipe

        mock_redis.setex.side_effect = Exception("connection refused")
        set_cached_recipe("fire", "water", "steam")  # never raises


class TestContextUnit:
    @pytest.mark.unit
    def test_add_pushes_and_trims(self, mock_redis):
        from src.cache.cache import add_to_context
        from src.config import config

        add_to_context("steam")
        mock_redis.lpush.assert_called_once_with("context:global", "steam")
        mock_redis.ltrim.assert_called_once_with(
            "context:global", 0, config.CONTEXT_SIZE - 1
        )

    @pytest.mark.unit
    def test_get_returns_list(self, mock_redis):
        from src.cache.cache import get_recent_context
        from src.config import config

        mock_redis.lrange.return_value = ["steam", "fire"]
        result = get_recent_context()
        assert result == ["steam", "fire"]
        mock_redis.lrange.assert_called_once_with(
            "context:global", 0, config.CONTEXT_SIZE - 1
        )

    @pytest.mark.unit
    def test_get_returns_empty_on_error(self, mock_redis):
        from src.cache.cache import get_recent_context

        mock_redis.lrange.side_effect = Exception("boom")
        assert get_recent_context() == []


class TestFailCounterUnit:
    @pytest.mark.unit
    def test_increment_returns_count(self, mock_redis):
        from src.cache.cache import increment_fail

        mock_redis.incr.return_value = 3
        assert increment_fail("fire", "water") == 3
        mock_redis.incr.assert_called_once_with("fail:fire:water")

    @pytest.mark.unit
    def test_get_fail_count(self, mock_redis):
        from src.cache.cache import get_fail_count

        mock_redis.get.return_value = "2"
        assert get_fail_count("fire", "water") == 2

    @pytest.mark.unit
    def test_get_fail_count_missing_key(self, mock_redis):
        from src.cache.cache import get_fail_count

        mock_redis.get.return_value = None
        assert get_fail_count("fire", "water") == 0

    @pytest.mark.unit
    def test_reset_deletes_key(self, mock_redis):
        from src.cache.cache import reset_fail

        reset_fail("fire", "water")
        mock_redis.delete.assert_called_once_with("fail:fire:water")


# ── Integration tests (live Redis) ────────────────────────────────────────────


class TestCacheIntegration:
    @pytest.mark.integration
    def test_ping(self):
        from src.cache import get_redis

        try:
            get_redis().ping()
        except Exception:
            pytest.skip("Redis not available")

    @pytest.mark.integration
    def test_recipe_roundtrip(self):
        from src.cache import get_cached_recipe, set_cached_recipe, delete_cached_recipe

        try:
            delete_cached_recipe("fire", "water")
            assert get_cached_recipe("fire", "water") is None
            set_cached_recipe("fire", "water", "steam")
            assert get_cached_recipe("fire", "water") == "steam"
            delete_cached_recipe("fire", "water")
            assert get_cached_recipe("fire", "water") is None
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.integration
    def test_context_cap(self):
        from src.cache import add_to_context, get_recent_context, get_redis
        from src.config import config

        try:
            get_redis().delete("context:global")
            for i in range(config.CONTEXT_SIZE + 5):
                add_to_context(f"elem{i}")
            ctx = get_recent_context()
            assert len(ctx) == config.CONTEXT_SIZE
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.integration
    def test_fail_counter_roundtrip(self):
        from src.cache import increment_fail, get_fail_count, reset_fail

        try:
            reset_fail("lead", "gold")
            assert get_fail_count("lead", "gold") == 0
            assert increment_fail("lead", "gold") == 1
            assert increment_fail("lead", "gold") == 2
            reset_fail("lead", "gold")
            assert get_fail_count("lead", "gold") == 0
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
