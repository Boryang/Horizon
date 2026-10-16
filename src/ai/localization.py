"""Deterministic normalization for localized AI output."""

from opencc import OpenCC


_TO_TAIWAN_TRADITIONAL = OpenCC("s2twp")


def normalize_language(text: str, language: str) -> str:
    """Normalize generated text to the script implied by its language tag."""
    if language.lower() == "zh":
        return _TO_TAIWAN_TRADITIONAL.convert(text)
    return text
