"""Combine pipeline unit tests — all offline via conftest fixtures."""

import pytest

from src.combine import combine
from src.validation import ValidationError


class TestCombineCacheHit:
    @pytest.mark.unit
    def test_returns_from_cache(self, mocker):
        mocker.patch("src.combine.get_cached_recipe", return_value="steam")
        mocker.patch("src.combine.add_to_context")
        mocker.patch("src.combine.reset_fail")

        r = combine("fire", "water")
        assert r.result == "steam"
        assert r.source == "cache"
        assert not r.is_new
        assert r.elapsed_ms >= 0


class TestCombineDbHit:
    @pytest.mark.unit
    def test_returns_from_db_and_warms_cache(self, mocker):
        mocker.patch("src.combine.get_cached_recipe", return_value=None)
        mocker.patch("src.combine.get_recipe", return_value="steam")
        mock_set = mocker.patch("src.combine.set_cached_recipe")
        mocker.patch("src.combine.add_to_context")
        mocker.patch("src.combine.reset_fail")

        r = combine("fire", "water")
        assert r.result == "steam"
        assert r.source == "db"
        mock_set.assert_called_once_with("fire", "water", "steam")


class TestCombineAiPath:
    @pytest.mark.unit
    def test_ai_result_persisted(self, mocked_pipeline):
        r = combine("fire", "water")
        assert r.result == "steam"
        assert r.source == "ai"
        assert r.is_new

    @pytest.mark.unit
    def test_order_independence(self, mocker):
        mocker.patch("src.combine.get_cached_recipe", return_value="steam")
        mocker.patch("src.combine.add_to_context")
        mocker.patch("src.combine.reset_fail")

        r1 = combine("fire", "water")
        r2 = combine("water", "fire")
        assert r1.result == r2.result

    @pytest.mark.unit
    def test_ai_retry_on_invalid_result(self, mocker):
        """AI returns invalid result first, valid on second attempt."""
        mocker.patch("src.combine.get_cached_recipe", return_value=None)
        mocker.patch("src.combine.get_recipe", return_value=None)
        mocker.patch("src.combine.save_element", return_value=True)
        mocker.patch("src.combine.save_recipe")
        mocker.patch("src.combine.set_cached_recipe")
        mocker.patch("src.combine.add_to_context")
        mocker.patch("src.combine.reset_fail")

        calls = iter(["fire", "steam"])  # first invalid (same as input), second ok
        mocker.patch("src.combine.generate_recipe", side_effect=lambda a, b: next(calls))

        r = combine("fire", "water")
        assert r.result == "steam"

    @pytest.mark.unit
    def test_ai_failure_raises(self, mocker):
        mocker.patch("src.combine.get_cached_recipe", return_value=None)
        mocker.patch("src.combine.get_recipe", return_value=None)
        mocker.patch("src.combine.generate_recipe", return_value=None)
        mocker.patch("src.combine.increment_fail", return_value=1)

        with pytest.raises(ValidationError, match="AI"):
            combine("fire", "water")


class TestCombineBadInputs:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "a,b",
        [
            ("", "fire"),
            ("fire!!!", "water"),
            ("a" * 31, "b"),
        ],
    )
    def test_bad_inputs_raise_before_io(self, a, b, mocker):
        spy = mocker.patch("src.combine.get_cached_recipe")
        with pytest.raises(ValidationError):
            combine(a, b)
        spy.assert_not_called()


class TestCombineDiscoveredOnly:
    @pytest.mark.unit
    def test_undiscovered_input_rejected_before_io(self, mocker):
        from src.validation import UnknownElementError

        mocker.patch("src.combine.get_discovered", return_value=["fire", "water"])
        spy = mocker.patch("src.combine.get_cached_recipe")

        with pytest.raises(UnknownElementError, match="steam"):
            combine("fire", "steam")
        spy.assert_not_called()


class TestCombineMarksDiscovered:
    @pytest.mark.unit
    def test_ai_result_marked_discovered(self, mocked_pipeline, mocker):
        mark = mocker.patch("src.combine.mark_discovered")

        combine("fire", "water")

        mark.assert_called_once_with("steam")

    @pytest.mark.unit
    def test_db_hit_marked_discovered(self, mocked_pipeline, mocker):
        mocker.patch("src.combine.get_recipe", return_value="steam")
        mark = mocker.patch("src.combine.mark_discovered")

        combine("fire", "water")

        mark.assert_called_once_with("steam")

    @pytest.mark.unit
    def test_cache_hit_skips_mark(self, mocker):
        mocker.patch("src.combine.get_cached_recipe", return_value="steam")
        mocker.patch("src.combine.add_to_context")
        mocker.patch("src.combine.reset_fail")
        mark = mocker.patch("src.combine.mark_discovered")

        combine("fire", "water")

        mark.assert_not_called()

    @pytest.mark.unit
    def test_marked_before_cached(self, mocked_pipeline, mocker):
        order: list[str] = []
        mocker.patch("src.combine.mark_discovered", side_effect=lambda _n: order.append("mark"))
        mocked_pipeline["cache"]["set_cached_recipe"].side_effect = lambda *_a: order.append(
            "cache"
        )

        combine("fire", "water")

        assert order == ["mark", "cache"]
