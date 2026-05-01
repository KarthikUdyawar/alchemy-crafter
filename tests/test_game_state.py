"""Game state unit tests — milestones, streaks, summary."""

import pytest
from src.game.state import GameState, MILESTONES


class TestGameState:
    @pytest.fixture
    def state(self):
        s = GameState()
        s.discovered = {"fire", "water", "earth", "air"}
        return s

    @pytest.mark.unit
    def test_record_new_increments_streak(self, state):
        state.record_combine("steam", is_new=True)
        state.record_combine("lava", is_new=True)
        assert state.discovery_streak == 2
        assert state.best_streak == 2

    @pytest.mark.unit
    def test_existing_resets_streak(self, state):
        state.record_combine("steam", is_new=True)
        state.record_combine("steam", is_new=False)
        assert state.discovery_streak == 0
        assert state.best_streak == 1

    @pytest.mark.unit
    def test_milestone_fires_once(self, state):
        state.discovered = set(f"el{i}" for i in range(9))
        state.record_combine("el9", is_new=True)  # hits 10
        msg = state.check_milestone()
        assert "Apprentice" in msg
        assert state.check_milestone() is None  # no double-fire

    @pytest.mark.unit
    def test_all_milestones_defined(self):
        thresholds = [t for t, _ in MILESTONES]
        assert thresholds == sorted(thresholds)  # ascending
        assert len(thresholds) == len(set(thresholds))  # unique

    @pytest.mark.unit
    def test_session_summary_contains_key_stats(self, state):
        state.record_combine("steam", True)
        state.record_combine("lava", True)
        state.record_combine("mud", False)
        lines = "\n".join(state.session_summary)
        assert "3" in lines  # 3 combines
        assert "2" in lines  # 2 new
