"""Estimate the minimum years of experience a job requires, and filter on it.

You have ~1 year of experience and want roles asking for at most 0-3 years.
We parse the description for phrases like "5-7 years", "minimum 4 years",
"3+ years experience" and take the *lowest* bar mentioned. If that lowest bar
is above the cap, the job is dropped. Jobs that don't state experience are kept.
"""
from __future__ import annotations

import re

# Ranges first (2-4 years), then singles (3+ years / 3 years).
_RANGE = re.compile(r"(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)
_SINGLE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)


def required_min_years(text: str) -> int | None:
    """Lowest lower-bound of experience mentioned, or None if none found.

    Using the *minimum* is deliberately lenient — we only reject when even the
    smallest experience number in the posting is above your cap.
    """
    if not text:
        return None
    t = text.lower()
    # Only look at experience-flavoured text to avoid matching random numbers.
    if "exp" not in t and "year" not in t and "yr" not in t:
        return None

    candidates: list[int] = []
    for m in _RANGE.finditer(t):
        lo = int(m.group(1))
        if 0 <= lo <= 20:
            candidates.append(lo)
    # Remove range spans before scanning singles so "2-4" isn't re-counted as 4.
    t_singles = _RANGE.sub(" ", t)
    for m in _SINGLE.finditer(t_singles):
        n = int(m.group(1))
        if 0 <= n <= 20:
            candidates.append(n)

    return min(candidates) if candidates else None


def within_cap(text: str, cap_years: int) -> tuple[bool, str]:
    """Return (keep?, human label). Keep if unknown or min requirement <= cap."""
    n = required_min_years(text)
    if n is None:
        return True, "not stated"
    return n <= cap_years, f"{n}+ yrs"
