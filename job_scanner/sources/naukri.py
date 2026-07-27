"""Naukri jobs via its public search JSON API (the same one the website calls).

No login required. Returns rich JSON incl. a freshness label we use to keep
only the last-24h postings.

NOTE: Naukri now protects this API with reCAPTCHA for many requests. When that
happens the call returns HTTP 406 and this module degrades gracefully to an
empty list (we do NOT attempt to bypass the CAPTCHA). For reliable Naukri-style
coverage, configure the Adzuna source, which indexes Naukri and other Indian
boards through a proper API. See job_scanner/sources/adzuna.py.
"""
from __future__ import annotations

import time

import requests

from . import Job

API = "https://www.naukri.com/jobapi/v3/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "appid": "109",
    "systemid": "Naukri",
    "Accept": "application/json",
    "Referer": "https://www.naukri.com/",
}


def _is_recent(label: str, max_age_hours: int) -> bool:
    """Naukri gives labels like 'Just now', 'Few hours ago', '1 Day Ago'."""
    l = (label or "").lower()
    if any(k in l for k in ("just now", "few hours", "hours ago", "today")):
        return True
    if "day" in l:
        # "1 Day Ago" -> 1
        num = "".join(ch for ch in l if ch.isdigit())
        try:
            return int(num) * 24 <= max_age_hours if num else max_age_hours >= 24
        except ValueError:
            return max_age_hours >= 24
    return False


def fetch(keyword: str, location: str, max_age_hours: int) -> list[Job]:
    params = {
        "noOfResults": 100,
        "urlType": "search_by_keyword",
        "searchType": "adv",
        "keyword": keyword,
        "sort": "f",           # sort by freshness
        "pageNo": 1,
        "seoKey": f"{keyword.replace(' ', '-')}-jobs",
    }
    if location and location.lower() != "india":
        params["location"] = location
    try:
        resp = requests.get(API, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  [naukri] '{keyword}' @ {location}: {e}")
        return []

    jobs: list[Job] = []
    for d in data.get("jobDetails", []):
        label = d.get("footerPlaceholderLabel") or d.get("createdDate") or ""
        if not _is_recent(label, max_age_hours):
            continue
        jd_url = d.get("jdURL", "")
        if jd_url and not jd_url.startswith("http"):
            jd_url = "https://www.naukri.com" + jd_url
        desc = " ".join(filter(None, [
            d.get("title", ""), d.get("jobDescription", ""),
            " ".join(t.get("label", "") for t in d.get("tagsAndSkills", []) if isinstance(t, dict))
            if isinstance(d.get("tagsAndSkills"), list) else str(d.get("tagsAndSkills", "")),
        ]))
        jobs.append(Job(
            title=d.get("title", ""),
            company=d.get("companyName", ""),
            location=", ".join(
                p.get("label", "") for p in d.get("placeholders", [])
                if isinstance(p, dict) and p.get("type") == "location"
            ) or location,
            url=jd_url,
            source="Naukri",
            posted=label,
            description=desc,
        ))
    time.sleep(1.0)  # be polite
    return jobs
