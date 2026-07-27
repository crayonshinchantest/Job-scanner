"""Entry point: scan LinkedIn + Naukri, score, build Excel, email it.

Run:  python -m job_scanner.main
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import yaml

from .experience import within_cap
from .geo import is_india
from .matcher import score_job
from .report import build_excel, send_email
from .resumes import recommend
from .sources import Job, adzuna, linkedin, naukri

CONFIG_PATH = os.environ.get("JOB_SCANNER_CONFIG", "config.yaml")

# How many unique LinkedIn jobs to enrich with full descriptions (bounded so we
# stay polite / avoid rate limits). Enriched jobs match far more accurately.
ENRICH_CAP = int(os.environ.get("JOB_SCANNER_ENRICH_CAP", "120"))


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect(cfg: dict) -> list[Job]:
    """Gather unique postings across all sources (no scoring yet)."""
    seen: set[str] = set()
    out: list[Job] = []
    for keyword in cfg["keywords"]:
        for location in cfg["locations"]:
            for src in (linkedin, naukri, adzuna):
                for job in src.fetch(keyword, location, cfg["max_age_hours"]):
                    key = (job.url or f"{job.title}|{job.company}").lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(job)
    return out


def main() -> int:
    cfg = load_config()
    print(f"Scanning LinkedIn + Naukri for {len(cfg['keywords'])} role types "
          f"across {len(cfg['locations'])} locations (last "
          f"{cfg['max_age_hours']}h)...")

    jobs = collect(cfg)
    print(f"Collected {len(jobs)} unique postings. Enriching LinkedIn "
          f"descriptions (up to {ENRICH_CAP})...")

    # Enrich LinkedIn jobs with full descriptions for accurate matching.
    enriched = 0
    for job in jobs:
        if enriched >= ENRICH_CAP:
            break
        if job.source == "LinkedIn":
            linkedin.enrich(job)
            enriched += 1

    cap = int(cfg.get("max_experience_years", 3))
    kept: list[Job] = []
    dropped_geo = dropped_exp = dropped_score = 0
    for job in jobs:
        job.score, job.matched = score_job(job.title, job.description)
        if not is_india(job.location):
            dropped_geo += 1
            continue
        ok, exp_label = within_cap(job.description, cap)
        job.experience_req = exp_label
        if not ok:
            dropped_exp += 1
            continue
        if job.score < cfg["min_match_score"]:
            dropped_score += 1
            continue
        job.resume, job.resume_path = recommend(job.title, job.description, job.company)
        kept.append(job)

    kept.sort(key=lambda j: j.score, reverse=True)
    jobs = kept[: cfg["max_results"]]
    print(f"Kept {len(jobs)} jobs (dropped {dropped_geo} non-India, "
          f"{dropped_exp} over {cap} yrs exp, {dropped_score} low-match).")

    out_dir = os.environ.get("JOB_SCANNER_OUT", ".")
    os.makedirs(out_dir, exist_ok=True)
    fname = f"Your_List_{dt.date.today():%Y-%m-%d}.xlsx"
    path = os.path.join(out_dir, fname)
    build_excel(jobs, path)
    print(f"Wrote {path}")

    email_cfg = cfg.get("email", {})
    if os.environ.get("SKIP_EMAIL") == "1":
        print("SKIP_EMAIL=1 set — not sending email.")
        return 0
    try:
        send_email(
            path, jobs,
            subject=email_cfg.get("subject", "Your List"),
            to_addr=email_cfg.get("to", ""),
            from_addr=email_cfg.get("from", ""),
        )
        print("Email sent.")
    except Exception as e:  # noqa: BLE001 - report and exit non-zero
        print(f"Email NOT sent: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
