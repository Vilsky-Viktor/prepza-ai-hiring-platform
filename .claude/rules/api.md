---
paths:
  - "services/api/**"
  - "services/*/src/*/api/v1/**"
  - "services/*/src/*/schemas/**"
  - "services/assistant/src/assistant/**/mcp*.py"
  - "services/assistant/src/assistant/constants/*_tools.py"
---

# HTTP APIs, the public API and MCP

The public API (`services/api`, `/api/v1`), its web hooks and the MCP server are a contract with
customers' code: changing them is a user-visible change (rule 14), even when no page changes,
and updates `docs/features/api.md` or `mcp.md` and the API description in the same change
(rule 9). The other services' routes follow the same HTTP rules.

## Resources and status codes

- Resources are plural nouns, nested only where the child can't exist without its parent
  (`/interviews/{id}/candidates`); a verb only for an action that isn't create, read, update or
  delete (`…/resend`).
- Status codes as RFC 9110 means them: `201` only when something new was made (`200` when it
  already existed), `204` without a body, `404` for what the caller may not see, `409` for a
  state conflict or a quota that waiting won't free, `422` for a well-formed but unacceptable
  body, `429` with `Retry-After` for a rate limit, `503` for a temporary stop.
- A `PATCH` changes all its fields or none: check every rule before writing anything.
- Request schemas are narrow: never `company_id`, `role`, `credits` or other authority from the
  body (OWASP API3).
- Personal data (emails) stays out of URLs and query strings; responses with it are
  `Cache-Control: no-store`.

## Errors

- Every refusal carries a stable machine-readable `code` beside its translated `detail`; clients
  branch on the code, never on the text. Validation errors name each bad field.

## Lists

- Lists page with `limit` (at most 100) and say when there's a next page (`Link: rel="next"`);
  sync uses `updated_since` + `after` on `(updated_at, id)`. A fixed, documented order. No
  unbounded lists and no call to another service per item.

## Idempotency

- Clients never manage idempotency keys; the server derives them, so every create is safe to
  retry as it is. A natural key where one exists (a candidate: the interview and the normalised
  email, returned as they are with `200`, no second email or credit); otherwise the API key, the
  route and a hash of the canonical body, kept for a short retry window (15 minutes) so a
  deliberate identical request later still creates. A retry while the first still runs gets
  `409`; a failure frees the key.
- An `Idempotency-Key` an older integration sends is still honoured (24 hours) but never
  documented, required or generated in examples or SDK code; the same key with a different body
  is refused with `422`.

## Versions

- Within `v1` only add: fields, optional parameters, enum values, event types. Removing or
  renaming waits for `v2`; a retired route first sends `Deprecation` (RFC 9745) and `Sunset`
  (RFC 8594) headers, and the docs' changelog says so.

## OpenAPI

- Generated from code, never edited by hand. Each public route has a summary, description, tag,
  a short stable `operationId` (it becomes SDK method and agent tool names), every response it
  can give and its permission. Closed sets are enums (`Literal[...]`); schemas carry
  descriptions and examples. Internal and management routes stay out.
- A change to routes or schemas refreshes the generated copies (the `api-types` skill).

## Keys and permissions

- API keys carry the `pz_` prefix, are shown once, stored as a SHA-256 hash, expire, and can be
  rotated by overlapping an old and a new key.
- Each key permission covers what it names and nothing more; a key never gains one after it's
  made, and its maker's role is rechecked. A new route declares its permission.
- Every call is scoped to the key's company (object-level authorization, OWASP API1);
  `/api/*/internal/` never reaches the internet.

## Web hooks we send

- Stable event `id`, a body `{type, timestamp, data}`, a timestamped HMAC-SHA256 signature,
  retries with exponential backoff and jitter over days, a pause after repeated failures, a
  delivery log and a test event.
- A secret can be rolled without losing the web hook: during the overlap both secrets sign.
- Sent only to public HTTPS addresses, connected to the address that was checked, no redirects,
  a hard timeout (SSRF; `.claude/rules/security.md`).

## MCP

- The MCP server, its OAuth server and its tools: `.claude/rules/mcp.md`.

Research (local notes, git-ignored): `internal_docs/best-practices/api-design.md`.
