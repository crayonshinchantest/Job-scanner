"""Job application dashboard (Streamlit) — colourful, filter-rich tracker.

Reads the jobs the scanner found and lets you track applications, filter by
company tier / experience / source / match, search freely, and copy a referral
message or a LinkedIn invite note per job. State persists to
data/applications.json in your GitHub repo (private, password-gated).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import re
import time

import streamlit as st

from job_scanner.companies import company_tier
from job_scanner.resumes import CATALOG

STATUSES = ["New", "Applied", "Interview", "Offer", "Rejected", "Skipped"]
STATUS_COLOR = {"New": "⚪", "Applied": "🔵", "Interview": "🟡",
                "Offer": "🟢", "Rejected": "🔴", "Skipped": "⚫"}
TIER_BADGE = {
    "Premium": ("💎 Premium", "#7c3aed"),
    "Established": ("⭐ Established", "#2563eb"),
    "Other": ("• Other", "#6b7280"),
}
RESUME_OPTIONS = [e["label"] for e in CATALOG] + ["Other / custom"]

QUOTES = [
    "Opportunities don't happen. You create them.",
    "The future depends on what you do today.",
    "Your dream job is one bold application away.",
    "Rejections are redirections. Keep going.",
    "Great things never came from comfort zones.",
    "You miss 100% of the roles you don't apply to.",
    "Consistency beats intensity. Apply. Every. Day.",
    "The expert in anything was once a beginner.",
    "Doubt kills more dreams than failure ever will.",
    "One yes erases a hundred nos. Chase the yes.",
    "Your only limit is the one you set yourself.",
    "Discipline is choosing what you want most over what you want now.",
    "Hard work beats talent when talent doesn't work hard.",
    "You are one referral, one message, one apply away.",
    "Show up today. Future-you is watching.",
]

JOBS_PATH = "data/jobs.json"
APPS_PATH = "data/applications.json"

st.set_page_config(page_title="Job Tracker", page_icon="🎯", layout="wide")

# ── clean, minimal theme + subtle animations ────────────────────────────────
st.markdown("""
<style>
:root { --accent:#4f46e5; }
.block-container { padding-top: 1.1rem; max-width: 1100px; }
h1 { font-weight: 700; letter-spacing: -0.5px; }
.quote { text-align:center; color:#64748b; font-style:italic; font-size:15px;
  margin: 0 0 4px; animation: fade .5s ease both; }
.badge { display:inline-block; padding:1px 9px; border-radius:999px; color:#fff;
  font-size:11px; font-weight:700; letter-spacing:.2px; }
/* metric tiles: quiet */
div[data-testid="stMetric"] { background:transparent; padding:2px 0; }
div[data-testid="stMetricValue"] { font-size:26px; }
div[data-testid="stMetricLabel"] { opacity:.7; }
/* job cards: soft border, fade-in, gentle hover lift */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:14px; border-color:#eceef2 !important;
  transition: box-shadow .2s ease, transform .2s ease; animation: fade .35s ease both;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 8px 24px rgba(15,23,42,.07); transform: translateY(-2px);
}
.stButton button { border-radius:9px; transition: transform .12s ease; }
.stButton button:hover { transform: translateY(-1px); }
@keyframes fade { from{opacity:0; transform:translateY(6px)} to{opacity:1; transform:none} }
@media (prefers-color-scheme: dark) {
  div[data-testid="stVerticalBlockBorderWrapper"] { border-color:#22262e !important; }
  .quote { color:#94a3b8; }
}
</style>
""", unsafe_allow_html=True)


# ── config: GitHub (hosted) vs local files (dev) ───────────────────────────
def cfg(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


REPO = cfg("GITHUB_REPO")
TOKEN = cfg("GITHUB_TOKEN")
BRANCH = cfg("GITHUB_BRANCH", "main")
USE_GH = bool(REPO and TOKEN)


def check_password() -> bool:
    pw = cfg("APP_PASSWORD")
    if not pw or st.session_state.get("authed"):
        return True
    st.title("🎯 Job Tracker")
    entered = st.text_input("Password", type="password")
    if entered and entered == pw:
        st.session_state["authed"] = True
        st.rerun()
    elif entered:
        st.error("Wrong password.")
    return False


# ── storage ────────────────────────────────────────────────────────────────
def _read_public(path):
    """Read a JSON file straight from the public repo (no token needed)."""
    if not REPO:
        return {}
    try:
        import requests
        r = requests.get(f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}", timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def load_jobs() -> list[dict]:
    data = {}
    if USE_GH:
        try:
            from gh_api import get_json
            data, _ = get_json(REPO, JOBS_PATH, TOKEN, BRANCH)
        except Exception:
            data = _read_public(JOBS_PATH)  # token issue → public read still works
    elif os.path.exists(JOBS_PATH):
        data = json.load(open(JOBS_PATH))
    else:
        data = _read_public(JOBS_PATH)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    for j in jobs:  # backfill tier for older entries
        if not j.get("tier"):
            j["tier"] = company_tier(j.get("company", ""))
    return jobs


def load_apps():
    if USE_GH:
        try:
            from gh_api import get_json
            return get_json(REPO, APPS_PATH, TOKEN, BRANCH)
        except Exception:
            st.warning("Couldn't read saved applications — check the GITHUB_TOKEN secret. "
                       "The dashboard still works; the ✅ Applied button won't save until it's fixed.")
            return _read_public(APPS_PATH), None
    if os.path.exists(APPS_PATH):
        return json.load(open(APPS_PATH)), None
    return _read_public(APPS_PATH), None


def save_apps(apps, sha, msg):
    if USE_GH:
        from gh_api import put_json
        return put_json(REPO, APPS_PATH, TOKEN, apps, sha, msg, BRANCH)
    os.makedirs(os.path.dirname(APPS_PATH) or ".", exist_ok=True)
    json.dump(apps, open(APPS_PATH, "w"), indent=2, ensure_ascii=False)
    return None


# ── copy helpers ────────────────────────────────────────────────────────────
def referral_message(j: dict) -> str:
    skills = ", ".join(j.get("matched", [])[:3]) or "strategy and marketing"
    return (
        "Hi [Name],\n\n"
        "I hope you're doing well. I'm Ajinkya Kolhe, an MBA from IIM Visakhapatnam "
        "currently running strategic planning and analytics in the MD's office at "
        "Avighna Group, with earlier experience across strategy and analytics.\n\n"
        f"I came across the {j['title']} role at {j['company']} and it lines up "
        f"closely with my background in {skills}. Would you be open to referring me, "
        "or pointing me to the right person on the team? I'd gladly share my resume "
        "and a short note on why I'm a strong fit.\n\n"
        "Thank you so much for considering it — I really appreciate your time.\n"
        "Best,\nAjinkya Kolhe | linkedin.com/in/ajinkyakolhe27"
    )


def linkedin_note(j: dict, limit: int = 250) -> str:
    """≤250 chars, job-specific, for the LinkedIn connect note box."""
    title = j["title"]
    while True:
        note = (f"Hi, I'm Ajinkya — an MBA (IIM Vizag) in strategy & marketing, currently in "
                f"the MD's office at Avighna Group. I'm keen on the {title} role at "
                f"{j['company']} and would love to connect and learn more about your team. Thanks!")
        if len(note) <= limit or len(title) <= 6:
            return note if len(note) <= limit else note[:limit - 1] + "…"
        title = title.rsplit(" ", 1)[0]  # trim last word and retry


def job_years(j: dict):
    if isinstance(j.get("exp_years"), int):
        return j["exp_years"]
    m = re.search(r"(\d+)", j.get("experience_req", "") or "")
    return int(m.group(1)) if m else None


# ── app ────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

if "apps" not in st.session_state:
    st.session_state.apps, st.session_state.apps_sha = load_apps()


def persist(url, patch, label):
    apps = st.session_state.apps
    rec = apps.get(url, {})
    rec.update(patch)
    rec["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    apps[url] = rec
    try:
        st.session_state.apps_sha = save_apps(apps, st.session_state.apps_sha, label)
        st.toast("Saved ✅", icon="✅")
    except Exception as e:
        st.error(f"Could not save (token/permissions?): {e}")


jobs = load_jobs()
apps = st.session_state.apps

# ── motivational quote (rotates every 5 min; button for a new one) ──────────
if "quote_override" not in st.session_state:
    st.session_state.quote_override = None
auto_idx = int(time.time() // 300) % len(QUOTES)
q = st.session_state.quote_override if st.session_state.quote_override is not None else QUOTES[auto_idx]
qc1, qc2 = st.columns([12, 1])
qc1.markdown(f'<div class="quote">“{q}”</div>', unsafe_allow_html=True)
if qc2.button("🔄", help="New quote (auto-rotates every 5 min)"):
    st.session_state.quote_override = random.choice([x for x in QUOTES if x != q])
    st.rerun()

st.title("🎯 Job Tracker")
if not USE_GH:
    st.caption("⚠️ Local mode — set GITHUB_REPO/GITHUB_TOKEN secrets to persist online.")


def n_status(s):
    return sum(1 for j in jobs if apps.get(j["url"], {}).get("status", "New") == s)


c = st.columns(5)
c[0].metric("Total", len(jobs))
c[1].metric("💎 Premium", sum(1 for j in jobs if j.get("tier") == "Premium"))
c[2].metric("Applied", n_status("Applied"))
c[3].metric("Interview", n_status("Interview"))
c[4].metric("Offer", n_status("Offer"))

st.divider()

# ── primary filters (up top, always visible) ────────────────────────────────
st.text_input("🔎 Search company, role, or keyword — e.g. 'ceo office', 'brand', 'Amazon'",
              key="search", placeholder="Type and results filter instantly…")
fc1, fc2, fc3 = st.columns([2, 2, 1])
with fc1:
    f_maxyears = st.slider("💼 Max experience (years)", 0, 6, 2,
                           help="Default 2 hides 3+ yr roles. Slide up to see senior roles.")
with fc2:
    f_tier = st.multiselect("💎 Company tier", ["Premium", "Established", "Other"],
                            default=["Premium", "Established", "Other"])
with fc3:
    f_min = st.slider("🎯 Min match %", 0, 100, 0, 5)

# ── secondary filters (sidebar) ─────────────────────────────────────────────
with st.sidebar:
    st.header("More filters")
    f_unstated = st.checkbox("Include 'experience not stated'", value=True)
    f_status = st.multiselect("Status", STATUSES, default=[])
    f_source = st.multiselect("Source", sorted({j["source"] for j in jobs}))
    f_resume = st.multiselect("Recommended resume", sorted({j.get("resume", "") for j in jobs if j.get("resume")}))
    st.divider()
    if st.button("🔄 Reload from GitHub"):
        st.session_state.apps, st.session_state.apps_sha = load_apps()
        st.rerun()

search = (st.session_state.get("search") or "").lower().strip()


def visible(j):
    a = apps.get(j["url"], {})
    if f_tier and j.get("tier", "Other") not in f_tier:
        return False
    yrs = job_years(j)
    if yrs is None:
        if not f_unstated:
            return False
    elif yrs > f_maxyears:
        return False
    if f_status and a.get("status", "New") not in f_status:
        return False
    if f_source and j["source"] not in f_source:
        return False
    if f_resume and j.get("resume", "") not in f_resume:
        return False
    if j.get("score", 0) < f_min:
        return False
    if search:
        hay = " ".join([j.get("title", ""), j.get("company", ""), j.get("location", ""),
                        j.get("resume", ""), " ".join(j.get("matched", []))]).lower()
        if search not in hay:
            return False
    return True


shown = [j for j in jobs if visible(j)]
tier_rank = {"Premium": 0, "Established": 1, "Other": 2}
shown.sort(key=lambda j: (apps.get(j["url"], {}).get("status", "New") != "New",
                          tier_rank.get(j.get("tier", "Other"), 2), -j.get("score", 0)))
st.caption(f"Showing {len(shown)} of {len(jobs)} jobs")

# ── job cards ──────────────────────────────────────────────────────────────
for j in shown:
    url = j["url"]
    a = apps.get(url, {})
    status = a.get("status", "New")
    label, colr = TIER_BADGE.get(j.get("tier", "Other"), TIER_BADGE["Other"])
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(
                f'<span class="badge" style="background:{colr}">{label}</span>'
                f'&nbsp;&nbsp;🎯 <b>{j.get("score",0)}%</b>&nbsp;·&nbsp;🧑‍💼 {j.get("experience_req","")}',
                unsafe_allow_html=True)
            st.markdown(f"### [{j['title']}]({url})")
            st.write(f"**{j['company']}** · {j.get('location','')} · {j['source']}")
            st.caption("Keywords: " + ", ".join(j.get("matched", [])[:8]))
            st.markdown(f"[↗ Open & apply]({url})")
            with st.expander("✉️ Referral message  ·  🔗 LinkedIn note"):
                st.caption("Referral request (copy with the icon top-right):")
                st.code(referral_message(j), language=None)
                note = linkedin_note(j)
                st.caption(f"LinkedIn connect note ({len(note)}/250 chars):")
                st.code(note, language=None)
        with right:
            st.write(f"{STATUS_COLOR.get(status,'⚪')} **{status}**"
                     + (f"  ·  applied {a['applied_at']}" if a.get("applied_at") else ""))
            default_resume = a.get("resume_used") or j.get("resume") or RESUME_OPTIONS[0]
            r_idx = RESUME_OPTIONS.index(default_resume) if default_resume in RESUME_OPTIONS else 0
            resume_used = st.selectbox("Resume to use", RESUME_OPTIONS, index=r_idx, key=f"r_{url}")
            new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(status), key=f"s_{url}")
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
                              placeholder="referral contact, recruiter, follow-up date…")
        if notes != a.get("notes", ""):
            persist(url, {"notes": notes}, f"Note: {j['title']}")
