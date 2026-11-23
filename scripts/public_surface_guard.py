#!/usr/bin/env python3
"""Fail closed if anything beyond the explicitly synthetic public CI repository appears.

This detects common credentials, not every possible secret. Human review remains required.
"""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED = frozenset({
    '.github/workflows/public-safe-ci.yml',
    '.gitignore',
    'README.md',
    'SECURITY.md',
    'package.json',
    'fixtures/catalogue.json',
    'src/server.mjs',
    'test/catalogue.test.mjs',
    'sql/schema.sql',
    'sql/fixture.sql',
    'web/index.html',
    'scripts/public_surface_guard.py',
    'scripts/test_guard.py',
    'scripts/mysql-smoke.sh',
    'scripts/browser-smoke.sh',
    'scripts/mobile-smoke.sh',
})
BLOCKED_PATH = re.compile(r'(^|/)(\.env(?:\..+)?|id_rsa|id_ed25519|.*\.pem|.*\.p12|.*\.key|\.npmrc|\.netrc|\.ssh|\.git|node_modules|build|dist|\.dart_tool|\.gradle)(/|$)', re.I)
SECRET_PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'cloud-api-key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bAIza[0-9A-Za-z_-]{35}\b'),
    'live-payment-secret': re.compile(r'\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b'),
    'git-remote': re.compile(r'(?:git@github\.com:|https://github\.com/)[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?', re.I),
    'git-commit': re.compile(r'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])', re.I),
}


# Explicit public dependency pins; unexpected commit hashes are blocked.
APPROVED_PUBLIC_COMMITS = frozenset({
    '93cb6efe18208431cddfb8368fd83d5badbf9bfd',
    'a0853c24544627f65ddf259abe73b1d18a591444',
    'b8962555571d8c170cff8e76023ea7bf60e5ec4b',
})
APPROVED_PUBLIC_REMOTES = frozenset({
    'sudheeerrr/bulkgram-ci-public',
    'actions/checkout',
    'actions/setup-node',
    'flutter/flutter',
})


def check(root: pathlib.Path = ROOT) -> list[str]:
    problems: list[str] = []
    found: set[str] = set()
    for p in root.rglob('*'):
        rel = p.relative_to(root).as_posix()
        if '.git' in p.relative_to(root).parts:
            # GitHub-managed checkout metadata is not packaged or published as project files.
            continue
        # Do not skip __pycache__ or other generated directories: committed artifacts
        # must fail the allowlist, rather than silently bypass publication review.
        if p.is_symlink():
            problems.append(f'Unexpected symlink: {rel}')
            continue
        if not p.is_file():
            continue
        found.add(rel)
        if BLOCKED_PATH.search(rel):
            problems.append(f'Forbidden path: {rel}')
        if rel not in EXPECTED:
            problems.append(f'Unreviewed file: {rel}')
        if p.stat().st_size > 150_000:
            problems.append(f'Unexpectedly large file: {rel}')
            continue
        try:
            body = p.read_text('utf-8')
        except UnicodeDecodeError:
            problems.append(f'Binary or non-UTF8 file: {rel}')
            continue
        for name, regex in SECRET_PATTERNS.items():
            if name == 'git-commit':
                for match in regex.finditer(body):
                    if match.group().lower() not in APPROVED_PUBLIC_COMMITS:
                        problems.append(f'Unapproved commit hash in {rel} (value redacted)')
            elif name == 'git-remote':
                for match in regex.finditer(body):
                    remote = re.sub(r'^(?:git@github\.com:|https://github\.com/)', '', match.group(), flags=re.I)
                    remote = re.sub(r'\.git$', '', remote, flags=re.I)
                    if remote.lower() not in APPROVED_PUBLIC_REMOTES:
                        problems.append(f'Unapproved GitHub remote in {rel} (value redacted)')
            elif regex.search(body):
                problems.append(f'Potential {name} in {rel} (value redacted)')
    for missing in sorted(EXPECTED - found):
        problems.append(f'Missing required file: {missing}')
    return problems

if __name__ == '__main__':
    errors = check()
    for item in errors:
        print(f'BLOCK: {item}', file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print(f'PASS: {len(EXPECTED)} explicitly reviewed synthetic public-only files')
