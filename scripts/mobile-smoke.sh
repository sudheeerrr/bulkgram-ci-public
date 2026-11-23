#!/usr/bin/env bash
set -euo pipefail
# Only generic Flutter template; never access the private BULKGRAM repository.
[[ "${RUNNER_OS:-}" == 'Linux' || "${RUNNER_OS:-}" == 'macOS' ]] || { echo 'Unsupported runner OS' >&2; exit 31; }
[[ "${PUBLIC_CI_MOBILE_OPT_IN:-}" == 'yes' ]] || { echo 'Mobile probe needs explicit opt-in' >&2; exit 32; }
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
flutter_dir="${RUNNER_TEMP:?}/flutter-public-ci"
# Flutter upstream GitHub tag 3.35.0 was resolved and verified on 2026-11-23.
# Fetch the immutable object; fail closed before executing SDK code.
flutter_commit=b8962555571d8c170cff8e76023ea7bf60e5ec4b
git init -q "$flutter_dir"
git -C "$flutter_dir" remote add origin https://github.com/flutter/flutter.git
# Fetch a public advertised ref, then require its exact independently reviewed commit.
# This avoids servers rejecting shallow requests for unadvertised raw Git objects.
git -C "$flutter_dir" fetch --no-tags --depth 1 origin refs/tags/3.35.0
git -C "$flutter_dir" checkout --detach -q FETCH_HEAD
[[ "$(git -C "$flutter_dir" rev-parse HEAD)" == "$flutter_commit" ]] || {
  echo 'Flutter upstream commit did not match locked revision' >&2
  exit 33
}
export PATH="$flutter_dir/bin:$PATH"
flutter --version
workspace="${RUNNER_TEMP}/synthetic_flutter_probe"
flutter create --project-name synthetic_flutter_probe "$workspace"
(cd "$workspace" && flutter test)
if [[ "$RUNNER_OS" == 'Linux' ]]; then
  (cd "$workspace" && flutter build apk --debug)
  apk="$workspace/build/app/outputs/flutter-apk/app-debug.apk"
  test -s "$apk"
  sha256sum "$apk" | tee "${RUNNER_TEMP}/synthetic-apk.sha256"
else
  (cd "$workspace" && flutter build ios --simulator --debug --no-codesign)
fi
printf 'PASS: generated public Flutter template only; NOT private app acceptance\n'
