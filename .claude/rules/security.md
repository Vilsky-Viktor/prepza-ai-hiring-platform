---
paths:
  - "services/**"
  - "packages/**"
  - "frontend/**"
  - "gateway/**"
  - "infra/**"
---

# Security and rate limiting

The yardstick is OWASP ASVS 5.0 level 2, the OWASP Top 10:2025, the API Security Top 10 2023 and
the Top 10 for LLM applications 2025.

## Sign-in and access

- Every Firebase ID token is verified server-side (`prepza_common.auth`: signature, `aud`,
  `iss`, `exp`); a certificate fetch failure is a 503, never a pass. Deleting an account
  revokes its refresh tokens; a check that must see revocation at once uses `check_revoked`.
- Decisions that rely on an email (starting an invite, accepting a member invite, the admin
  zone, data export, what a link reveals about an address) need a verified email.
- Every route resolves its object and checks the caller's company and role on it (`interview_for`,
  `candidate_for`, `require_company`, `require_editor`); an unguessable id never replaces the
  check. Test access with a second account that must be refused.
- Each service's `test_route_guards.py` (`prepza_common.route_guards`) fails on a route that runs
  no guard; a route public on purpose is listed there with why.
- Superadmin routes answer 404 to everyone else.
- Service-to-service calls carry short-lived (60 s), audience-bound tokens with one key per
  callee (`service_auth`); Google-signed pushes have their audience and account checked;
  `/internal` is blocked at the edge and the gateway, and Cloud Run takes traffic only from the
  load balancer.

## Web hooks we receive

- Verify the HMAC over the raw body in constant time (`tokens.same_secret`), reject old
  timestamps, and make the handler idempotent on the event id (providers redeliver). Paddle's
  (window, idempotency on Paddle's object ids, reconciliation): `.claude/rules/payments.md`.

## Requests to addresses users give

- Sending to a customer's URL is SSRF by design: HTTPS only, resolve and check the address is
  public, connect to that checked address (DNS rebinding), no redirects, a hard timeout.

## Browser

- A nonce CSP with `'strict-dynamic'`, `object-src 'none'`, `base-uri` and `frame-ancestors`
  (`frontend/lib/csp.ts`); `nosniff`, `Referrer-Policy`, `Permissions-Policy` and HSTS on every
  response; no `X-Powered-By`; `Cache-Control: no-store` on responses with private data.
- No CORS (same origin; exact origins only if one is ever needed); writes need a bearer token in
  a header, never a cookie alone (a cookie used for writes would need SameSite plus a token or
  Fetch Metadata checks).
- HSTS gains `includeSubDomains` only once every subdomain serves HTTPS; a
  `Cross-Origin-Opener-Policy` must keep the sign-in providers' popups working
  (`same-origin-allow-popups`).
- Authorization lives in the backend; the frontend has no server actions, and per-user data is
  never in a shared cache.
- Rendered markdown from a model or a user allows only in-app links.

## Files

- Uploads are checked by content (magic bytes) against an allowlist of types, with size limits
  before and after decoding (an image's pixels, not only its bytes); names are made by the
  server; decoding runs off the event loop and its errors are a 422, not a 500.

## Transport and secrets

- TLS 1.2 or later only, at the load balancer and to the database.
- Secrets live in Secret Manager only (`.claude/rules/infra.md`); never in code, images, logs,
  tfvars or compose beyond local placeholders.
- Never log tokens, keys, session ids, a URL path that carries a secret token (log the route
  template) or unneeded personal data; log authentication and authorization failures.
- `packages/common/tests/unit/test_log_calls.py` fails on a log call passing an email, a name, a
  token or a key; every log line is scrubbed of emails and URL paths (`prepza_common.scrub`).

## AI

- Instructions apart from data; user and company text in a marked section; tools act with the
  caller's own permissions; the model picks from ids the code gave; links built by code; writes
  need the user's confirmation; rate and spend limits on every model-calling route
  (`.claude/rules/ai.md`).

## Rate limiting

- Every route that costs money or can be abused (AI, emails, invites, exports, checkouts,
  integrations, anonymous endpoints) has a limit from `prepza_common.rate_limit`, with its
  default, window and scope in `limit_list.LIMITS`, editable in the admin zone.
- Pick the key by what it protects: per user or company for fairness and spend, per IP for
  anonymous traffic, a global cap for shared budgets (the AI bill). Normalise keys built from
  input (case; plus-addressing for an email recipient).
- Count a request only after the cheap checks that would refuse it anyway, and check the
  narrower key (one address) before the shared one (a whole link), so one abuser can't use up
  everyone's quota.
- A limit answers `429` with `Retry-After` (the seconds left in its window), kept when a service
  relays it; a daily cap's `503` carries `Retry-After` to the reset. A quota that waiting won't
  free (a count of keys or companies) is a `409`, not a `429`.
- Fixed windows in Redis, check-and-count in one transaction. Limits against floods fail open
  (`hit_or_skip`); limits that cap spend (AI, emails, credits) fail closed (`hit`).
- Business flows people could abuse (sign-up, a first company, link starts, the help chat, the
  contact form) also pass a Turnstile check.
- Outbound: back off with jitter, honour `Retry-After` as the minimum wait, retry at one layer
  only, and keep a provider-side spend cap (OpenAI's hard limit) as the last line.

Research (local notes, git-ignored): `internal_docs/best-practices/security.md`,
`internal_docs/best-practices/rate-limiting.md`.
