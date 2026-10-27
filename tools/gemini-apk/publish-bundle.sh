#!/usr/bin/env bash
# Publish only verified Gemini output. Handle unrelated concurrent bot commits.
set -euo pipefail
: "${GITHUB_REF_NAME:?Set GITHUB_REF_NAME to the build branch}"
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -f bundles/gemini/gemini-target.mpp bundles/gemini/gemini-target.mpp.sha256 \
  bundles/gemini/patch-list.txt bundles/gemini/patch-result.json \
  bundles/gemini/validation.json bundles/gemini/google-patch-result.json \
  bundles/gemini/google-validation.json bundles/gemini/bundle.mpp bundles/gemini/bundle.mpp.sha256
if git diff --cached --quiet; then
  echo 'Verified Gemini bundle unchanged; nothing to publish.'
  exit 0
fi
git commit -m 'build: publish verified Gemini Google bundle (device testing pending)'
for attempt in 1 2 3; do
  if git push origin "HEAD:$GITHUB_REF_NAME"; then
    exit 0
  fi
  if [[ "$attempt" == 3 ]]; then
    echo '::error::Cannot publish bundle after three attempts; artifact remains available in this run.'
    exit 1
  fi
  git fetch origin "$GITHUB_REF_NAME"
  # Never resolve a conflicting artifact/source update by force pushing.
  # Git will stop on conflicts for review rather than silently discard work.
  git rebase FETCH_HEAD
done
