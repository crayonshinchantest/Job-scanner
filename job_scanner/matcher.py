"""Score a job posting against the resume profile (0-100)."""
from __future__ import annotations

from . import profile


def _count_hits(text: str, terms: list[str]) -> tuple[int, list[str]]:
    hits = [t for t in terms if t in text]
    return len(hits), hits


def score_job(title: str, description: str) -> tuple[int, list[str]]:
    """Return (score 0-100, matched keywords).

    Score blends: title relevance + core skill overlap + supporting overlap.
    Jobs whose title is clearly off-lane are pushed to ~0.
    """
    title_l = (title or "").lower()
    text = f"{title_l} {(description or '').lower()}"

    # Hard reject obviously irrelevant roles.
    for bad in profile.NEGATIVE_TITLE:
        if bad in title_l:
            return 0, []

    core_n, core_hits = _count_hits(text, profile.CORE_SKILLS)
    supp_n, supp_hits = _count_hits(text, profile.SUPPORTING)
    title_n, _ = _count_hits(title_l, profile.TITLE_BOOST)

    # Weighted, then squashed into 0-100.
    raw = core_n * 6 + supp_n * 2 + title_n * 10
    score = min(100, raw)

    # Small bonus if the seniority looks right for an early-career MBA.
    if any(s in title_l for s in profile.PREFERRED_SENIORITY):
        score = min(100, score + 5)

    matched = list(dict.fromkeys(core_hits + supp_hits))  # de-dupe, keep order
    return score, matched
