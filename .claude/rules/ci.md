---
paths:
  - ".github/**"
  - "services/*/Dockerfile"
  - "frontend/Dockerfile"
  - "**/pyproject.toml"
  - "**/uv.lock"
  - "frontend/package.json"
  - "frontend/pnpm-lock.yaml"
  - "frontend/pnpm-workspace.yaml"
  - "infra/terraform/github.tf"
---

# Dependencies, images and CI

## Dependencies

- Every project commits its lockfile and installs only from it: `uv sync --locked` (fails when
  the lock no longer matches `pyproject.toml`; `--frozen` only for a deps-only Docker layer built
  before the project files are copied) and `pnpm install --frozen-lockfile`.
- pnpm guards in `pnpm-workspace.yaml`: `minimumReleaseAge` (a day), `allowBuilds` (only listed
  packages run install scripts), `trustPolicy: no-downgrade`, `blockExoticSubdeps`; a pnpm
  version that supports them.
- `prepza_common` is an editable path dependency without a pin (`.claude/rules/python-services.md`);
  pinning applies to third-party code.
- Dependabot watches every ecosystem (actions, docker, compose, npm, uv), grouped, majors by hand,
  with its cooldown; merge after CI passes, in a weekly batch.
- Scanning on pull requests, main and a weekly schedule: pip-audit and `pnpm audit --prod`, a
  secret scanner (gitleaks), and a scan of the built images' OS packages (Trivy or Artifact
  Analysis), failing on fixable high or critical.

## Images

- Base images pinned by tag and digest; multi-stage, so build tools (uv included) stay out of the
  final image, which gets only the `.venv` and the code; a non-root `USER`; `.dockerignore`
  keeps secrets and junk out; build secrets as secrets, never `ARG`s.

## GitHub Actions

- Every `uses:` pinned to a 40-character SHA with a `# vX.Y.Z` comment.
- `permissions: contents: read` at the top of each workflow; jobs add only what they need.
- No `${{ }}` with values a person can choose (or any outside value) inside `run:`: pass them
  through `env:` and quote `"$VAR"`.
- No `pull_request_target`; never check out untrusted code in a privileged job.
- `actions/checkout` with `persist-credentials: false` unless a later step pushes with git.
- `timeout-minutes` on every job.
- Workflows are linted (zizmor and actionlint, pinned) when `.github/` changes; their test is a
  green run of the changed workflow.
- Fast checks on every push (lint, types, unit tests of what changed), the whole stack when its
  parts change, slow and costly suites (evals, load) on a schedule.

## Cloud access and releases

- Keyless access through Workload Identity Federation, restricted by an `attribute_condition` on
  the numeric `repository_id` and `repository_owner_id` (names can be re-registered) plus the
  ref and workflow; separate accounts for building and deploying, each with only its roles.
- Build once and deploy the same image by digest (`image@sha256:…`), never by a mutable tag; the
  version tag is a label. One deploy at a time, a smoke test after it.
- Rollback redeploys an earlier release with migrations off (or moves traffic to an earlier
  revision), which additive migrations make safe.
- `main` and `v*` tags are protected by rulesets; the `production` environment needs a reviewer
  and deploys only from `main` and `v*`.
- No SLSA L3, signing or Binary Authorization (rule 4): pinned inputs and deploys by digest give
  the integrity that matters here.

Research (local notes, git-ignored): `internal_docs/best-practices/ci-supply-chain.md`.
