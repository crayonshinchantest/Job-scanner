"""Tiny GitHub Contents-API client used by the dashboard to read/write JSON
files in your repo — this is what makes application state persist for free.

Needs a fine-grained Personal Access Token with Contents: Read and write on the
job-scanner repo, provided via Streamlit secrets (see README).
"""
from __future__ import annotations

import base64
import json

import requests

API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_json(repo: str, path: str, token: str, branch: str = "main"):
    """Return (data, sha). data is {} and sha is None if the file doesn't exist."""
    r = requests.get(f"{API}/repos/{repo}/contents/{path}",
                     headers=_headers(token), params={"ref": branch}, timeout=20)
    if r.status_code == 404:
        return {}, None
    r.raise_for_status()
    payload = r.json()
    content = base64.b64decode(payload["content"]).decode("utf-8")
    try:
        return json.loads(content), payload["sha"]
    except json.JSONDecodeError:
        return {}, payload["sha"]


def put_json(repo: str, path: str, token: str, data, sha: str | None,
             message: str, branch: str = "main") -> str:
    """Create/update a JSON file. Returns the new sha."""
    body = {
        "message": message,
        "content": base64.b64encode(
            json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        ).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    r = requests.put(f"{API}/repos/{repo}/contents/{path}",
                     headers=_headers(token), json=body, timeout=20)
    r.raise_for_status()
    return r.json()["content"]["sha"]
