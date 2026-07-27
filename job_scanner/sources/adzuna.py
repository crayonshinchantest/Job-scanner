"""Adzuna jobs API (India) — a legitimate free aggregator.

Adzuna indexes many Indian job boards (including Naukri-sourced postings) and
exposes a proper JSON API. It's optional: it only runs if you set a free API
key. Get one in ~2 minutes at https://developer.adzuna.com/ and export:

    ADZUNA_APP_ID=...      ADZUNA_APP_KEY=...

Without those env vars this source is skipped silently.
"""
from __future__ import annotations

import os
import time

import requests

from . import Job

BASE = "https://api.adzuna.com/v1/api/jobs/in/search/1"  # /in = India


def fetch(keyword: str, location: str, max_age_hours: int) -> list[Job]:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return []  # not configured — skip

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 50,
        "what": keyword,
        "max_days_old": max(1, round(max_age_hours / 24)),
        "sort_by": "date",
        "content-type": "application/json",
    }
    if location and location.lower() not in ("india", "remote"):
        params["where"] = location

    try:
        resp = requests.get(BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  [adzuna] '{keyword}' @ {location}: {e}")
        return []

    jobs: list[Job] = []
    for d in data.get("results", []):
        jobs.append(Job(
            title=d.get("title", ""),
            company=(d.get("company") or {}).get("display_name", ""),
            location=(d.get("location") or {}).get("display_name", location),
            url=d.get("redirect_url", ""),
            source="Adzuna",
            posted=d.get("created", ""),
            description=f"{d.get('title', '')} {d.get('description', '')}",
        ))
    time.sleep(0.5)
    return jobs
