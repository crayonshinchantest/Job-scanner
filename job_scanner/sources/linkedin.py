"""LinkedIn jobs via the public 'guest' job-search endpoint.

This is the same unauthenticated endpoint the public jobs page calls to load
more cards — no login, no account, so your LinkedIn profile is never touched.
It can rate-limit; we back off and fail gracefully rather than hammering it.
"""
from __future__ import annotations

import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from . import Job

GUEST_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(keyword: str, location: str, max_age_hours: int) -> list[Job]:
    # f_TPR=r<seconds> restricts to jobs posted in the last N seconds.
    params = {
        "keywords": keyword,
        "location": location or "India",
        "f_TPR": f"r{int(max_age_hours) * 3600}",
        "sortBy": "DD",   # date, descending
        "start": 0,
    }
    jobs: list[Job] = []
    for page in range(2):  # 2 pages (~50 cards) is plenty per query
        params["start"] = page * 25
        try:
            resp = requests.get(
                f"{GUEST_URL}?{urllib.parse.urlencode(params)}",
                headers=HEADERS, timeout=20,
            )
            if resp.status_code == 429:
                time.sleep(5)
                break
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [linkedin] '{keyword}' @ {location}: {e}")
            break

        cards = BeautifulSoup(resp.text, "html.parser").select("li")
        if not cards:
            break
        for c in cards:
            title_el = c.select_one("h3.base-search-card__title")
            comp_el = c.select_one("h4.base-search-card__subtitle")
            link_el = c.select_one("a.base-card__full-link") or c.select_one("a")
            loc_el = c.select_one(".job-search-card__location")
            date_el = c.select_one("time")
            if not (title_el and link_el):
                continue
            url = link_el.get("href", "").split("?")[0]
            jobs.append(Job(
                title=title_el.get_text(strip=True),
                company=comp_el.get_text(strip=True) if comp_el else "",
                location=loc_el.get_text(strip=True) if loc_el else location,
                url=url,
                source="LinkedIn",
                posted=date_el.get("datetime", "") if date_el else "",
                # Seed with title; enrich() adds the full description later.
                description=title_el.get_text(strip=True),
            ))
        time.sleep(1.5)  # be polite
    return jobs


def enrich(job) -> None:
    """Fetch the full public job description so matching isn't title-only.

    Mutates job.description in place. Silently leaves the title-only
    description if the page can't be fetched.
    """
    if job.source != "LinkedIn" or not job.url:
        return
    try:
        resp = requests.get(job.url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return
        soup = BeautifulSoup(resp.text, "html.parser")
        desc = (soup.select_one("div.show-more-less-html__markup")
                or soup.select_one(".description__text"))
        if desc:
            job.description = f"{job.title} {desc.get_text(' ', strip=True)}"
    except requests.RequestException:
        return
    time.sleep(1.0)  # be polite between detail fetches
