#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if command -v google-chrome >/dev/null; then chrome=$(command -v google-chrome)
elif command -v chromium >/dev/null; then chrome=$(command -v chromium)
else echo 'No Chromium-based browser installed; not a pass' >&2; exit 21; fi
# Isolated temporary profile, normal Chromium sandbox, no proxy or background networking.
profile=$(mktemp -d)
trap 'rm -rf -- "$profile"' EXIT
if ! output=$(timeout 35s "$chrome" --headless --disable-gpu --no-first-run --no-default-browser-check --disable-background-networking --disable-extensions --disable-sync --no-proxy-server --user-data-dir="$profile" --dump-dom "file://$root/web/index.html" 2>/dev/null); then
  echo 'Chromium failed or timed out; browser acceptance NOT PASSED' >&2
  exit 23
fi
[[ "$output" == *'id="ci-ready"'* && "$output" == *'Public synthetic test fixture'* ]] || { echo 'Browser did not render synthetic page' >&2; exit 22; }
echo 'PASS: Chrome rendered synthetic HTML; NOT BULKGRAM PWA/browser acceptance'
