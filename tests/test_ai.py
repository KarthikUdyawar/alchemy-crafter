"""AI generator tests — offline parser + live marker."""

import pytest
from src.ai.generator import _build_prompt, _parse_response, generate_recipe


class TestPromptBuilder:
    @pytest.mark.unit
    def test_contains_inputs(self):
        p = _build_prompt("fire", "water", ["fire", "water", "earth"])
        assert "fire + water" in p
        assert "fire, water, earth" in p

    @pytest.mark.unit
    def test_fallback_context(self):
        p = _build_prompt("fire", "water", [])
        assert "none" in p                      # empty context → "none"
        assert "fire + water" in p              # inputs still present


class TestResponseParser:
    @pytest.mark.unit
    def test_standard(self):
        assert _parse_response("result: steam") == "steam"

    @pytest.mark.unit
    def test_case_insensitive(self):
        assert _parse_response("Result: Steam") == "steam"

    @pytest.mark.unit
    def test_trims_whitespace(self):
        assert _parse_response("result:   lava  ") == "lava"

    @pytest.mark.unit
    def test_multiline(self):
        assert _parse_response("Sure!\nresult: mud\nDone.") == "mud"

    @pytest.mark.unit
    def test_no_match_returns_none(self):
        assert _parse_response("I don't know") is None


class TestGenerateLive:
    @pytest.mark.integration
    def test_live_generate(self):
        result = generate_recipe("fire", "water")
        if result is None:
            pytest.skip("Ollama not available or model not pulled")
        assert isinstance(result, str) and len(result) > 0
        assert result not in ("fire", "water")
