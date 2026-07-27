#!/usr/bin/env bash
# Local runner for the daily job scan. Used by the launchd schedule (macOS).
set -euo pipefail
cd "$(dirname "$0")"

# Load secrets from .env if present (KEY=VALUE lines).
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# Use the project's virtualenv if it exists, else system python3.
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

exec "$PY" -m job_scanner.main >> job-scanner.log 2>&1
