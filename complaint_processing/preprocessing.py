import hashlib
import re


def clean_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def fingerprint(customer_email: str, text: str) -> str:
    """Cheap near-duplicate signal: hash of email + normalized text.
    Catches exact repeats; pair with a similarity check downstream for
    near-duplicates (same issue, reworded)."""
    normalized = re.sub(r"[^a-z0-9 ]", "", text.lower())
    return hashlib.sha256(f"{customer_email}:{normalized}".encode()).hexdigest()


def _normalize_words(text: str) -> set:
    stripped = re.sub(r"[^a-z0-9 ]", "", clean_text(text).lower())
    return set(stripped.split())


def is_near_duplicate(text_a: str, text_b: str, threshold: float = 0.8) -> bool:
    """Jaccard similarity on word sets — simple, explainable, no external deps.
    Good enough as a first pass; revisit if the 500+ dataset needs more nuance."""
    words_a = _normalize_words(text_a)
    words_b = _normalize_words(text_b)
    if not words_a or not words_b:
        return False
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return (intersection / union) >= threshold
