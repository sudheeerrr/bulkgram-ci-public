# Public safety boundary

This is a synthetic runner fixture. Never publish source, exports, migrations, credentials, business data, user identifiers, Git history, or source ZIPs from any private application repository here.

All data and database names are fabricated. The MariaDB credential in the workflow is **only** for a container instantiated by that job, not a reusable password. No GitHub secrets, cross-repo tokens, cloud service credentials, external database URLs, production API endpoints, third-party self-hosted runners, deployment or artifact uploads are allowed.

The allowlist gate rejects added files by default. It does **not** prove zero secret leakage; review every added line, commit, branch, workflow modification and pull request before public publication. Do not paste private source into workflow logs or issues. Public repo history is permanently observable even after later deletion.

Public-standard runner minutes are separate from private caller billing. Never check out private source, fork it into public, or use a public runner as a proxy for private application acceptance. Production and staging are out of scope.

Workflow is `workflow_dispatch` only, with `contents: read` and persistent checkout credentials disabled. Editing the workflow requires explicit review and separate authorization. Keep GitHub Actions disabled until approval.

## Final pre-publication review (2026-11-23)

**Dependency-reference hardening (2026-11-23):** checkout is commit-pinned. The MariaDB 11.4.13 linux/amd64 service is pinned to the Docker Hub-published manifest digest `sha256:9c8b5172fa219e01913060f26c5498029999657fb9b7e7bbd0ca9e87f51020e2` (Docker Hub image details for `mariadb:11.4` on linux/amd64). Flutter `3.35.0` was resolved through the upstream GitHub Git reference and commits API to `b8962555571d8c170cff8e76023ea7bf60e5ec4b`; the script checks out the SHA and verifies HEAD before running it. MariaDB client installation with a mutable Ubuntu package was **removed**: the script executes the built-in client of the exact pinned database container, verifies its actual service image and container identity, and rejects remote database targets. Container pull / Flutter fetch and hosted platform behavior have **not** been executed in this environment. `ubuntu-22.04`/`macos-15` are mutable hosted runner labels and may change toolchain versions. Do not publish or run without explicit authorization and a final hosted verification of the published digest and script compatibility.

Review the actual future repository identity and branch restrictions before enabling manual dispatch. The public sample has no private code or secrets; do not use it as a relay for private-source tests. The allowlist checks paths and common secret patterns but cannot replace human source review.

## Publication/runner approval gates (unpublished proposal)

- **Approved identity:** `sudheeerrr/bulkgram-ci-public`, default branch `main`. The safety job rejects a different repository, branch, non-manual event, or self-hosted runner; changing these values requires a new review.
- **Source separation:** create a new empty repository; do not transfer private BULKGRAM commits, PRs, tags, Git LFS, ZIPs, secrets, .env files, signing files, or production data. Check initial repository tree and all refs before enabling Actions.
- **Account controls:** explicitly review visibility, member/write permissions, Actions allowed actions policy, default `GITHUB_TOKEN` read-only settings, self-hosted runner availability, environment protection, public logs/artifacts, and branch rules. These GitHub account settings are **NOT VERIFIED** by local static analysis.
- **Dependency immutability:** `actions/checkout` and `actions/setup-node` pinned to upstream verified full SHAs; Node is fixed at `22.16.0`. Flutter fetches an advertised `refs/tags/3.35.0` ref and checks its resolved Git commit against the preapproved full SHA **before executing Flutter**. Database uses fixed Docker manifest. Ubuntu and macOS runner labels and Xcode/Android SDK preinstalls remain moving external dependencies.
- **Runner execution:** test on authorized hosted `ubuntu-22.04` and `macos-15` only. Synthetic browser uses ordinary Chromium sandbox and temporary profile. No public/private cross-repository read, token, secret or remote endpoint is permitted.
- **Approval boundary:** package validation does not authorize publication. Before any public repository creation, publication, or workflow dispatch, obtain explicit approval for that specific action. Synthetic jobs never certify the private application itself.

## 2026-11-23 runner compatibility update

Based on the successful, separate DoorFresh synthetic CI reference: immutable checkout v5.0.1 SHA `93cb6efe18208431cddfb8368fd83d5badbf9bfd`, Ubuntu 22.04 for sandboxed Chromium; setup-node v5.0.0 SHA `a0853c24544627f65ddf259abe73b1d18a591444` (both upstream refs checked). Checkout is read-only, nonpersistent with fetch-depth 1. Linux jobs have 15-minute maximum timeouts. Optional generated Flutter builds may exceed that limit. This synthetic public package has not been published or hosted-executed. Public repository creation, file publication, and Actions dispatch each require separate explicit approval. It is NOT private application acceptance.
