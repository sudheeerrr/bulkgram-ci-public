# Public-safe CI sandbox — synthetic fixtures only

**Not an application checkout and not a substitute for private V1 release acceptance.** This standalone example contains *no private application code* and must never import private application repositories.

## What is included

- Manual-only (`workflow_dispatch`) GitHub Actions workflow with a reviewed-file security gate, Node 22 synthetic HTTP contracts, Python guard tests, ephemeral MariaDB 11 smoke/rollback, Chrome rendering of a synthetic HTML page, optional generated Flutter Android and iOS sample builds, and an aggregate report.
- Entirely synthetic catalogue and database fixtures. All services bind to an isolated runner/container; no external application endpoints.
- Node and Python tests run without any npm/pip third-party dependencies. Chromium, Docker/MariaDB, Flutter and Android/iOS environments are **not locally certified** unless their jobs run successfully on actual hosted runners.

## Local use

```bash
python3 scripts/public_surface_guard.py
python3 -m unittest discover -s scripts -p 'test_*.py' -v
npm test
bash -n scripts/*.sh
```

## To install *after explicit approval*

1. Create a separate new **empty** public repository, for example `bulkgram-ci-public`. Never import private application Git history or any private source ZIP.
2. Review the entire 16-file allowlist, copy only these files, and independently inspect the new repository contents and branches. The MariaDB service image is pinned to a Docker Hub amd64 manifest digest, Flutter SDK to its verified Git commit, and the database client runs inside the exact pinned service image instead of an unpinned host apt installation. Real hosted pulls/builds **remain unverified** until a disposable Actions run is explicitly authorized.
3. Turn on public Actions only after approval. The workflow has **no automatic triggers**. On the default branch, use **Actions → Public synthetic CI probe → Run workflow** to start a manual run.
4. The workflow enforces the proposed publication repository identity (`sudheeerrr/bulkgram-ci-public`), `main` branch, GitHub-hosted runners, and manual dispatch. Node is pinned via an SHA-verified setup-node action to 22.16.0. The optional `mobile_smoke` Boolean triggers immutable Flutter 3.35.0 commit (verified from GitHub) and creates *new* template apps for Android and iOS. Mobile jobs are skipped otherwise. **Never interpret synthetic Android/iOS passes as private application acceptance.**
5. Review failed jobs and run results. The summary fails if any required test fails or any optional mobile job runs and fails. Skipped opt-in mobile jobs are explicitly labelled skipped.

## Important limitations

- `mariadb:11.4.13` pinned to a manifest digest is the synthetic smoke image and tests rollback only; it **does not verify BULKGRAM's MariaDB 11 migrations, authorization or schema**.
- Browser job renders static synthetic HTML, **not authenticated private application/PWA flows**.
- Flutter job exercises generated Flutter template, **not the private application**, and requires public network access and native toolchains; mobile jobs have not been executed.
- The workflow reports standard job outcome, **not release readiness**, and never produces or uploads artifacts containing private data.
- A public repository's free runner allowance does **not** make private source testing automatically free, permitted or secure. Private release acceptance remains a separate dependency.
- Do not copy this `.github/workflows` tree into the private repository until manually reviewing triggers and the existing protected workflows.

## 2026-11-23 runner compatibility update

Based on the successful, separate DoorFresh synthetic CI reference: immutable checkout v5.0.1 SHA `93cb6efe18208431cddfb8368fd83d5badbf9bfd`, Ubuntu 22.04 for sandboxed Chromium; setup-node v5.0.0 SHA `a0853c24544627f65ddf259abe73b1d18a591444` (both upstream refs checked). Checkout is read-only, nonpersistent with fetch-depth 1. Linux jobs have 15-minute maximum timeouts. Optional generated Flutter builds may exceed that limit. This synthetic public package has not been published or hosted-executed. Public repository creation, file publication, and Actions dispatch each require separate explicit approval. It is NOT private application acceptance.
