"""
Phase 4 — Validation layer.

All AI-generated (and user-supplied) element names pass through here
before being stored or returned to the player.
"""

import re

from src.config import config

# Only letters, digits, spaces, and hyphens
_VALID_CHARS_RE = re.compile(r"^[a-z0-9 \-]+$")


class ValidationError(Exception):
    """Raised when an element name fails validation."""


def validate_element(name: str, inputs: tuple[str, str] | None = None) -> str:
    """
    Validate and normalise an element name.

    Args:
        name:   Raw element name (from AI or user input).
        inputs: The two source elements, used to catch same-as-input results.

    Returns:
        Cleaned, lowercased element name.

    Raises:
        ValidationError: with a human-readable reason.
    """
    # 1. Normalise first so every subsequent check works on clean data
    cleaned = name.strip().lower()

    # 2. Not empty
    if not cleaned:
        raise ValidationError("Result is empty.")

    # 3. Length limit
    if len(cleaned) > config.MAX_ELEMENT_LENGTH:
        raise ValidationError(
            f"Result is too long ({len(cleaned)} chars, max {config.MAX_ELEMENT_LENGTH})."
        )

    # 4. Valid characters only
    if not _VALID_CHARS_RE.match(cleaned):
        raise ValidationError(
            f"Result '{cleaned}' contains invalid characters "
            "(only letters, digits, spaces, hyphens allowed)."
        )

    # 5. Must not repeat an input element
    if inputs:
        a, b = inputs
        if cleaned in (a.lower(), b.lower()):
            raise ValidationError(f"Result '{cleaned}' is the same as one of the inputs.")

    return cleaned


def validate_inputs(a: str, b: str) -> tuple[str, str]:
    """
    Validate and normalise the two player-supplied input elements.

    Returns the normalised (a, b) pair sorted alphabetically.

    Raises:
        ValidationError: with a human-readable reason.
    """
    a_clean = a.strip().lower()
    b_clean = b.strip().lower()

    if not a_clean or not b_clean:
        raise ValidationError("Both element names must be non-empty.")

    if not _VALID_CHARS_RE.match(a_clean) or not _VALID_CHARS_RE.match(b_clean):
        raise ValidationError(
            "Element names may only contain letters, digits, spaces, and hyphens."
        )

    if len(a_clean) > config.MAX_ELEMENT_LENGTH or len(b_clean) > config.MAX_ELEMENT_LENGTH:
        raise ValidationError(
            f"Element names must be {config.MAX_ELEMENT_LENGTH} characters or fewer."
        )

    # Sort for order-independence: fire+water == water+fire
    return tuple(sorted([a_clean, b_clean]))  # type: ignore[return-value]
