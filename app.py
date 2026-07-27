"""Job application dashboard (Streamlit).

Reads jobs the scanner found and lets you track applications: mark Applied,
record which resume you used, and move each role through a pipeline. State is
saved to data/applications.json in your GitHub repo, so it persists forever and
is private to you (the app is password-gated).

Run locally:   streamlit run app.py      (uses local data/ files)
Hosted:        Streamlit Community Cloud  (uses your repo via a token)
"""
from __future__ import annotations

import datetime as dt
import json
import os

import streamlit as st

from job_scanner.resumes import CATALOG

STATUSES = ["New", "Applied", "Interview", "Offer", "Rejected", "Skipped"]
STATUS_COLOR = {"New": "⚪", "Applied": "🔵", "Interview": "🟡",
                "Offer": "🟢", "Rejected": "🔴", "Skipped": "⚫"}
RESUME_OPTIONS = [e["label"] for e in CATALOG] + ["Other / custom"]

JOBS_PATH = "data/jobs.json"
APPS_PATH = "data/applications.json"

st.set_page_config(page_title="Job Tracker", page_icon="🎯", layout="wide")


# ── config: GitHub (hosted) vs local files (dev) ───────────────────────────
def cfg(key: str, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


REPO = cfg("GITHUB_REPO")        # e.g. "crayonshinchantest/Job-scanner"
TOKEN = cfg("GITHUB_TOKEN")
BRANCH = cfg("GITHUB_BRANCH", "main")
USE_GH = bool(REPO and TOKEN)


# ── password gate ──────────────────────────────────────────────────────────
def check_password() -> bool:
    pw = cfg("APP_PASSWORD")
    if not pw:
        return True  # no password configured (e.g. local dev)
    if st.session_state.get("authed"):
        return True
    st.title("🎯 Job Tracker")
    entered = st.text_input("Password", type="password")
    if entered and entered == pw:
        st.session_state["authed"] = True
        st.rerun()
    elif entered:
        st.error("Wrong password.")
    return False


# ── storage layer ──────────────────────────────────────────────────────────
def load_jobs() -> list[dict]:
    if USE_GH:
        from gh_api import get_json
        data, _ = get_json(REPO, JOBS_PATH, TOKEN, BRANCH)
    else:
        data = json.load(open(JOBS_PATH)) if os.path.exists(JOBS_PATH) else {}
    return data.get("jobs", []) if isinstance(data, dict) else []


def load_apps() -> tuple[dict, str | None]:
    if USE_GH:
        from gh_api import get_json
        return get_json(REPO, APPS_PATH, TOKEN, BRANCH)
    if os.path.exists(APPS_PATH):
        return json.load(open(APPS_PATH)), None
    return {}, None


def save_apps(apps: dict, sha: str | None, msg: str) -> str | None:
    if USE_GH:
        from gh_api import put_json
        return put_json(REPO, APPS_PATH, TOKEN, apps, sha, msg, BRANCH)
    os.makedirs(os.path.dirname(APPS_PATH) or ".", exist_ok=True)
    json.dump(apps, open(APPS_PATH, "w"), indent=2, ensure_ascii=False)
    return None


# ── app ────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

if "apps" not in st.session_state:
    st.session_state.apps, st.session_state.apps_sha = load_apps()


def persist(url: str, patch: dict, label: str):
    apps = st.session_state.apps
    rec = apps.get(url, {})
    rec.update(patch)
    rec["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    apps[url] = rec
    try:
        st.session_state.apps_sha = save_apps(apps, st.session_state.apps_sha, label)
        st.toast(f"Saved: {label}", icon="✅")
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not save (token/permissions?): {e}")


jobs = load_jobs()
apps = st.session_state.apps

st.title("🎯 Job Tracker")
if not USE_GH:
    st.caption("⚠️ Local mode — set GITHUB_REPO/GITHUB_TOKEN secrets to persist online.")

# ── metrics ────────────────────────────────────────────────────────────────
def n_status(s):
    return sum(1 for j in jobs if apps.get(j["url"], {}).get("status", "New") == s)


c = st.columns(6)
c[0].metric("Total", len(jobs))
c[1].metric("Applied", n_status("Applied"))
c[2].metric("Interview", n_status("Interview"))
c[3].metric("Offer", n_status("Offer"))
c[4].metric("Rejected", n_status("Rejected"))
c[5].metric("New", n_status("New"))

# ── filters ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    f_status = st.multiselect("Status", STATUSES, default=[])
    f_source = st.multiselect("Source", sorted({j["source"] for j in jobs}))
    f_min = st.slider("Min match %", 0, 100, 0, 5)
    f_text = st.text_input("Search title / company")
    st.divider()
    if st.button("🔄 Reload from GitHub"):
        st.session_state.apps, st.session_state.apps_sha = load_apps()
        st.rerun()


def visible(j):
    a = apps.get(j["url"], {})
    status = a.get("status", "New")
    if f_status and status not in f_status:
        return False
    if f_source and j["source"] not in f_source:
        return False
    if j.get("score", 0) < f_min:
        return False
    if f_text and f_text.lower() not in f"{j['title']} {j['company']}".lower():
        return False
    return True


shown = [j for j in jobs if visible(j)]
shown.sort(key=lambda j: (apps.get(j["url"], {}).get("status", "New") != "New",
                          -j.get("score", 0)))
st.caption(f"Showing {len(shown)} of {len(jobs)} jobs")

# ── job cards ──────────────────────────────────────────────────────────────
for j in shown:
    url = j["url"]
    a = apps.get(url, {})
    status = a.get("status", "New")
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"### [{j['title']}]({url})")
            st.write(f"**{j['company']}** · {j.get('location','')} · "
                     f"{j['source']} · 🎯 **{j.get('score',0)}% match** · "
                     f"🧑‍💼 {j.get('experience_req','')}")
            st.caption("Keywords: " + ", ".join(j.get("matched", [])[:8]))
            st.markdown(f"[↗ Open & apply]({url})")
        with right:
            st.write(f"{STATUS_COLOR.get(status,'⚪')} **{status}**"
                     + (f"  ·  applied {a['applied_at']}" if a.get("applied_at") else ""))
            default_resume = a.get("resume_used") or j.get("resume") or RESUME_OPTIONS[0]
            r_idx = RESUME_OPTIONS.index(default_resume) if default_resume in RESUME_OPTIONS else 0
            resume_used = st.selectbox("Resume to use", RESUME_OPTIONS, index=r_idx,
                                       key=f"r_{url}")
            new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(status),
                                      key=f"s_{url}")
            b1, b2 = st.columns(2)
            if b1.button("✅ Applied", key=f"ap_{url}", use_container_width=True):
                persist(url, {"status": "Applied", "resume_used": resume_used,
                              "applied_at": dt.date.today().isoformat()},
                        f"Applied: {j['title']} @ {j['company']}")
                st.rerun()
            if b2.button("💾 Save", key=f"sv_{url}", use_container_width=True):
                patch = {"status": new_status, "resume_used": resume_used}
                if new_status != "New" and not a.get("applied_at"):
                    patch["applied_at"] = dt.date.today().isoformat()
                persist(url, patch, f"Update: {j['title']} → {new_status}")
                st.rerun()
        notes = st.text_input("Notes", value=a.get("notes", ""), key=f"n_{url}",
                              placeholder="referral, recruiter, follow-up date…")
        if notes != a.get("notes", ""):
            persist(url, {"notes": notes}, f"Note: {j['title']}")
