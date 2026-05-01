"""Validation unit tests — fully offline."""

import pytest
from src.validation import validate_element, validate_inputs, ValidationError


class TestValidateElement:
    @pytest.mark.unit
    def test_normalises(self):
        assert validate_element("  Steam  ") == "steam"
        assert validate_element("lava rock") == "lava rock"
        assert validate_element("ice-9") == "ice-9"

    @pytest.mark.unit
    def test_rejects_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_element("   ")

    @pytest.mark.unit
    @pytest.mark.parametrize("name", ["fire!", "wat@r", "ear<th"])
    def test_rejects_invalid_chars(self, name):
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_element(name)

    @pytest.mark.unit
    def test_rejects_over_length(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_element("a" * 31)

    @pytest.mark.unit
    def test_rejects_same_as_input(self):
        with pytest.raises(ValidationError, match="same as one of the inputs"):
            validate_element("fire", inputs=("fire", "water"))

    @pytest.mark.unit
    def test_no_input_check_without_kwarg(self):
        assert validate_element("fire") == "fire"


class TestValidateInputs:
    @pytest.mark.unit
    def test_sorted_order_independence(self):
        assert validate_inputs("water", "fire") == ("fire", "water")

    @pytest.mark.unit
    def test_normalises(self):
        assert validate_inputs("  FIRE  ", "  Water  ") == ("fire", "water")

    @pytest.mark.unit
    @pytest.mark.parametrize("a,b", [("", "fire"), ("fire", ""), ("", "")])
    def test_rejects_empty(self, a, b):
        with pytest.raises(ValidationError, match="non-empty"):
            validate_inputs(a, b)

    @pytest.mark.unit
    def test_rejects_invalid_chars(self):
        with pytest.raises(ValidationError):
            validate_inputs("fire!", "water")

    @pytest.mark.unit
    def test_rejects_over_length(self):
        with pytest.raises(ValidationError):
            validate_inputs("a" * 31, "fire")
