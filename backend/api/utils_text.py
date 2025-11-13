"""
utils_text.py
Small text utilities used across parsing steps.
Author: you (@traqcheck take-home)
"""

import re
import string

_WHITESPACE_RE = re.compile(r"\s+")
_NONPRINTABLE = "".join(chr(c) for c in range(256) if chr(c) not in string.printable)

def normalize_space(s: str) -> str:
    """Collapse runs of whitespace to single spaces and strip ends."""
    if not s:
        return ""
    return _WHITESPACE_RE.sub(" ", s).strip()

def strip_nonprintable(s: str) -> str:
    """Remove non-printable characters."""
    if not s:
        return ""
    return s.translate(str.maketrans("", "", _NONPRINTABLE))

def truncate(s: str, max_len: int) -> str:
    """Truncate a string to max_len characters with a clear suffix."""
    if not s or len(s) <= max_len:
        return s or ""
    return s[: max_len - 10] + "...[truncated]"

def only_digits(s: str) -> str:
    """Keep only digits from a string."""
    return "".join(ch for ch in s if ch.isdigit())

def canonical_phone(s: str) -> str:
    """
    Normalize a phone-like string to a canonical digits-only form.
    Returns "" if not plausible (length <7 or >15).
    """
    digits = only_digits(s)
    return digits if 7 <= len(digits) <= 15 else ""

def clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0
