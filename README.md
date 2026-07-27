# Job Scanner — daily marketing & strategy job list

Every day at 9 PM it scans **LinkedIn** and **Naukri** for jobs posted in the
**last 24 hours**, scores each one against your resume (strategy + marketing),
builds an Excel of the best matches with clickable apply links, and emails it to
you with the subject **"Your List"**.

## How matching works

It queries the **public** LinkedIn and Naukri job-search endpoints (no login,
so your accounts are never touched or at risk) filtered to the last 24 hours,
then scores every posting 0–100 by how much its title and description overlap
with keywords pulled from your resume (see `job_scanner/profile.py`). Higher
score = better fit; the email lists best matches first. It ranks fit — it can't
literally guarantee you'll be selected. Tune the keywords and thresholds in
`config.yaml` and `profile.py` anytime.

## Setup (3 steps)

### 1. Create a Gmail App Password (so it can send the email)
Google no longer allows normal passwords for scripts. Create a 16-char app
password (2‑Step Verification must be on):
<https://myaccount.google.com/apppasswords> → app "Mail" → copy the 16 chars.

### 2. Give it the credentials
- **Local (Mac):** `cp .env.example .env` and paste your app password into `.env`.
- **GitHub Actions:** in your repo → Settings → Secrets and variables → Actions →
  add `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`.

### 3. Choose how it runs daily at 9 PM

**Option A — GitHub Actions (recommended, always-on, nothing to keep running).**
The workflow `.github/workflows/daily.yml` already runs at 15:30 UTC = 21:00 IST.
Just push this repo to GitHub and add the two secrets above. Run it once manually
from the **Actions** tab → *Daily job list* → *Run workflow* to test.

**Option B — Your Mac (launchd).** Runs at 9 PM local time whenever the Mac is awake:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp launchd/com.ajinkya.jobscanner.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ajinkya.jobscanner.plist
```

## Run it manually right now
```bash
python3 -m pip install -r requirements.txt
# Test without sending an email (just writes the Excel):
SKIP_EMAIL=1 python3 -m job_scanner.main
# Full run (needs .env with the app password):
set -a; source .env; set +a; python3 -m job_scanner.main
```

## Files
- `config.yaml` — search keywords, locations, thresholds, email subject.
- `job_scanner/profile.py` — resume keywords used for scoring.
- `job_scanner/sources/` — LinkedIn + Naukri fetchers.
- `job_scanner/matcher.py` — the 0–100 scoring.
- `job_scanner/report.py` — Excel builder + Gmail sender.
- `.github/workflows/daily.yml` — the 9 PM schedule for GitHub Actions.
- `launchd/…plist` — the 9 PM schedule for macOS.

## Notes / honesty
- These are public endpoints; they can rate-limit or change their markup, in
  which case a source is skipped for that run (the other still works). If matches
  ever drop to zero for days, the site likely changed — ping and it's a quick fix.
- Built for **your personal** job search, not bulk/commercial scraping.
