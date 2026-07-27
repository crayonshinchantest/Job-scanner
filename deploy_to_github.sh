#!/usr/bin/env bash
# One-shot: push the complete job-scanner code to your GitHub repo and make it
# private. The ONLY interactive step is a browser "authorize" click during
# `gh auth login` — you do that, nothing else. Safe to re-run.
set -e

PROJECT="/Users/ajinkya/Coding Projects/job-scanner"
REPO_NAME="Job-scanner"

cd "$PROJECT"

# 1. Make sure the GitHub CLI is installed.
if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing GitHub CLI via Homebrew..."
    brew install gh
  else
    echo "Homebrew not found. Install it from https://brew.sh then re-run this script."
    exit 1
  fi
fi

# 2. Log in (opens your browser to authorize — this is the one click you make).
if ! gh auth status >/dev/null 2>&1; then
  echo ">>> A browser window will open. Sign in and click Authorize, then come back here."
  gh auth login --hostname github.com --git-protocol https --web
fi

USER=$(gh api user -q .login)
echo "Logged in as: $USER"

# 3. Create the repo if it doesn't exist yet (harmless if it already does).
gh repo view "$USER/$REPO_NAME" >/dev/null 2>&1 || \
  gh repo create "$USER/$REPO_NAME" --private --disable-wiki -y

# 4. Push the complete, correct code (overwrites the earlier partial upload).
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER/$REPO_NAME.git"
git branch -M main
git push -u origin main --force

# 5. Ensure it's private.
gh repo edit "$USER/$REPO_NAME" --visibility private \
  --accept-visibility-change-consequences 2>/dev/null || true

echo ""
echo "============================================================"
echo " GitHub side DONE."
echo "  Repo:    https://github.com/$USER/$REPO_NAME   (private)"
echo "  Secrets: add GMAIL_ADDRESS + GMAIL_APP_PASSWORD at:"
echo "           https://github.com/$USER/$REPO_NAME/settings/secrets/actions"
echo ""
echo " Next (only you can do these 2 — they involve a security token):"
echo "  A) Make a token: https://github.com/settings/tokens?type=beta"
echo "     - Repository access: only '$REPO_NAME'"
echo "     - Permissions: Contents = Read and write"
echo "  B) Deploy the dashboard: https://share.streamlit.io"
echo "     - New app -> repo '$USER/$REPO_NAME', branch main, file app.py"
echo "     - Advanced -> Secrets: paste the block printed below"
echo ""
echo "  Paste this into Streamlit 'Secrets' (fill the two blanks):"
echo "  ----------------------------------------------------------"
echo "  GITHUB_REPO   = \"$USER/$REPO_NAME\""
echo "  GITHUB_TOKEN  = \"PASTE_YOUR_TOKEN_FROM_STEP_A\""
echo "  GITHUB_BRANCH = \"main\""
echo "  APP_PASSWORD  = \"PICK_ANY_PASSWORD\""
echo "  ----------------------------------------------------------"
echo "============================================================"
