#!/usr/bin/env bash
# One-time repo setup. Branch protection cannot live in a committed file; it lives on GitHub.
# Requires the gh CLI (`brew install gh`) and admin on the repo. Re-running is harmless.
set -euo pipefail
REPO="${1:?usage: scripts/protect.sh <owner/repo>}"

gh api --method PUT "repos/$REPO/branches/main/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "types", "unit", "integration", "spec-gate", "security", "workflows"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

gh api --method PATCH "repos/$REPO" \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true

echo "main is protected: squash-only, linear history, 7 required checks, merge through a PR (no approval needed: solo maintainer)."
