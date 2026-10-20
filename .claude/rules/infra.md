---
paths:
  - "infra/**"
  - "compose/**"
  - "gateway/**"
  - "scripts/**"
  - "docker-compose.yml"
  - "services/*/Dockerfile"
  - "frontend/Dockerfile"
  - ".github/**"
---

# Infrastructure

Production is Terraform in `infra/terraform` (`versions.tf`, `variables.tf`, `locals.tf`,
`outputs.tf`, `terraform.tfvars.example`, one `<kind>.tf` per kind of resource, split past
rule 2); the local stack (`compose/`, `gateway/nginx.conf`) mirrors it; `scripts/` holds shell
tools.

- No values in code. Secret values live only in Secret Manager (Cloud Run reads them by
  `secret_key_ref`); never in tfvars, compose, images or logs. Each service account gets only
  the roles it needs.
- Near-identical resources: one resource with `for_each` over `locals`. CI runs
  `terraform fmt -check` and `terraform validate`. Every variable and output has a description.
- The local stack uses the same Dockerfiles and variable names (`.env.example`) and emulators;
  a new production resource gets its local counterpart in the same change.
- nginx: one `location` per service; upstreams as variables; security headers with `always`,
  repeated in any block that adds its own.
- Scripts: `set -euo pipefail` (`set -eu` in plain `sh`), a header comment, quoted variables,
  errors to stderr, safe to run twice; past ~100 lines, Python.
