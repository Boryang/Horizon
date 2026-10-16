"""Deterministic normalization for localized AI output."""

from opencc import OpenCC


_TO_TAIWAN_TRADITIONAL = OpenCC("s2twp")

# OpenCC s2twp phrase conversion is tuned for software UI text and
# over-converts some words in news/finance contexts. Fix the known cases.
_TAIWAN_FIXES = {
    "擴充套件": "擴充",
    "引數": "參數",
    "半導體裝置": "半導體設備",
    "製造裝置": "製造設備",
    "封裝裝置": "封裝設備",
    "裝置大廠": "設備大廠",
    "裝置市場": "設備市場",
}


def normalize_language(text: str, language: str) -> str:
    """Normalize generated text to the script implied by its language tag."""
    if language.lower() == "zh":
        out = _TO_TAIWAN_TRADITIONAL.convert(text)
        for wrong, right in _TAIWAN_FIXES.items():
            out = out.replace(wrong, right)
        return out
    return text
