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

## Dashboard (Streamlit web app)

A private, password-gated web dashboard to track applications: see every job the
scanner found, click **✅ Applied**, record **which resume** you used, and move
each role through a pipeline (New → Applied → Interview → Offer/Rejected). Your
history is saved in `data/applications.json` in this repo, so it persists forever
and stays private to you. All free — no database or extra service.

**How data flows:** the daily Action saves scanned jobs to `data/jobs.json` and
commits it. The dashboard reads that plus `data/applications.json` (your status
choices) live from the repo via a token.

### Deploy it (one-time, ~10 min, all free)

1. **Make the repo Private** (Settings → General → Change visibility). It holds
   your job-search activity.
2. **Create a fine-grained Personal Access Token** so the app can save your
   application status: GitHub → Settings → Developer settings → *Fine-grained
   tokens* → Generate. Repository access = only `job-scanner`. Permissions →
   **Contents: Read and write**. Copy the token.
3. **Deploy on Streamlit Community Cloud** (free): <https://share.streamlit.io>
   → sign in with GitHub → **Create app** → pick this repo, branch `main`, main
   file `app.py`.
4. In the app's **Advanced settings → Secrets**, paste:
   ```toml
   GITHUB_REPO = "your-username/job-scanner"
   GITHUB_TOKEN = "github_pat_...."     # the token from step 2
   GITHUB_BRANCH = "main"
   APP_PASSWORD = "pick-a-password"     # you'll type this to open the app
   ```
5. Deploy. Open the URL, enter your password — that's your private dashboard.
   Bookmark it on your phone. It auto-updates each day after the 9 PM scan.

Run it locally instead (uses the local `data/` files, no token needed):
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `config.yaml` — search keywords, locations, thresholds, email subject.
- `job_scanner/profile.py` — resume keywords used for scoring.
- `job_scanner/sources/` — LinkedIn + Naukri fetchers.
- `job_scanner/matcher.py` — the 0–100 scoring.
- `job_scanner/report.py` — Excel builder + Gmail sender.
- `.github/workflows/daily.yml` — the 9 PM schedule for GitHub Actions.
- `launchd/…plist` — the 9 PM schedule for macOS.
- `app.py` — the Streamlit tracking dashboard.
- `gh_api.py` — reads/writes the JSON data files in your repo (dashboard persistence).
- `job_scanner/store.py` — writes `data/jobs.json` for the dashboard.
- `data/jobs.json` — scanned jobs (written by the Action).
- `data/applications.json` — your Applied status + resume used (written by the dashboard).

## Notes / honesty
- These are public endpoints; they can rate-limit or change their markup, in
  which case a source is skipped for that run (the other still works). If matches
  ever drop to zero for days, the site likely changed — ping and it's a quick fix.
- Built for **your personal** job search, not bulk/commercial scraping.
