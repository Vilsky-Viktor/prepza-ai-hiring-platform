---
paths:
  - "services/assistant/app/**/mcp*.py"
  - "services/assistant/app/**/oauth*.py"
  - "services/assistant/app/helpers/authorize_guard.py"
  - "services/assistant/app/routers/connect.py"
  - "services/assistant/app/services/connections.py"
  - "services/assistant/app/constants/key_tools.py"
  - "services/assistant/tests/**/test_mcp*.py"
  - "services/assistant/tests/**/test_oauth*.py"
  - "docs/features/mcp.md"
  - "e2e_tests/mcp.py"
  - "e2e_tests/helpers/mcp_client.py"
  - "frontend/content/mcp/**"
---

# The MCP server and its OAuth server

AI apps (Claude, ChatGPT, Cursor, VS Code, agents) call the assistant's tools as the user at
`<SITE_URL>/mcp`. The server is a contract with apps and customers' agents: changing what they
see (tools, names, schemas, results, auth) is a user-visible change (rule 14) and updates
`docs/features/mcp.md` and the developer docs' MCP tab (rule 9). CLAUDE.md wins on any conflict;
the HTTP rules are `api.md`'s, tool-writing rules `ai.md`'s, security `security.md`'s.

## Protocol revisions and transport

- The current revision is 2026-07-28 (stateless: no `initialize`, no `Mcp-Session-Id`, a
  `_meta` envelope on every request, `server/discover`); clients still send 2025-11-25 and
  older. The server answers both eras on one endpoint: legacy calls through `initialize`,
  modern ones per request (the SDK picks by `MCP-Protocol-Version`). `e2e_tests/mcp.py` calls
  both.
- Streamable HTTP only, stateless, plain JSON answers: any instance answers any request; no
  sessions to hijack, nothing to resume (`Last-Event-ID` is ignored). Not used (deprecated in
  2026-07-28): HTTP+SSE (2024-11-05), roots, sampling, logging.
- Every POST carries `MCP-Protocol-Version`, and in 2026-07-28 `Mcp-Method` and `Mcp-Name`
  matching the body (else `400`, `-32020`); an unsupported version is `400` with the supported
  ones; GET and DELETE are `405` in the modern era. The SDK enforces these; don't bypass it.
- The browser preflight allows every header a revision sends (`MCP_REQUEST_HEADERS`), so
  browser-based apps (MCP Inspector) work. CORS is `*` without credentials: access rides on the
  bearer header, never a cookie.
- Origin: the spec says to validate it against DNS rebinding. Not adopted for this remote server:
  every call needs a bearer token no page can read, and browser-based apps must work; local
  servers are where rebinding bites.
- Results that can be cached (`tools/list`, `server/discover`) carry `ttlMs` and `cacheScope`;
  `tools/list` varies by caller (API key permissions), so its scope is `private`. Its order is
  fixed (prompt caching). `listChanged` is declared only if the server emits it (it doesn't).

## Authorization

- prepza is both the authorization server (the site's root) and the resource (`/mcp`), from the
  MCP SDK's building blocks. OAuth 2.1, authorization code with PKCE `S256` only, advertised in
  `code_challenge_methods_supported`.
- A call without a valid token is `401` with `WWW-Authenticate: Bearer resource_metadata=…`;
  the protected resource metadata (RFC 9728) is at the path-inserted and the root well-known
  addresses, naming the site as the only authorization server; its `resource` is exactly the
  address users enter.
- Resource indicators (RFC 8707): an `/authorize` or token request for another resource is
  `invalid_target`; tokens are opaque, issued for `/mcp` only, so the audience check is
  "issued here". The server accepts only its own tokens (`pzm_`) or a company API key (`pz_`)
  checked by the api service, and never passes either to another service: services are called
  with a Firebase ID token minted for the user (no token passthrough).
- Tokens only in the `Authorization` header, never a query string; stored as SHA-256 hashes.
  Access 1 hour; refresh 90 days, rotated on every use (public clients), a replayed old refresh
  token after the grace minute revokes the connection; `invalid_grant` for a dead one.
- Registration: Client ID Metadata Documents (an HTTPS URL with a path as `client_id`;
  preferred by Claude and ChatGPT, advertised as `client_id_metadata_document_supported`) and,
  deprecated in 2026-07-28 but kept for apps that use it, dynamic client registration (RFC 7591).
  A document is read through `prepza_common.public_urls` (HTTPS, public addresses, pinned, no
  redirects, 5 s, 4,000 bytes), must name itself by its URL, have no secret and return only to
  app addresses; its copy is kept a day, and serves while its site is down.
- Redirect URIs match exactly what was registered, but a loopback one on any port (RFC 8252);
  schemes that run in the browser are refused; `/authorize` never redirects anywhere but the
  consent page (no open redirect).
- Consent: prepza's own page names the app by the site it returns to (not its claimed name),
  shows the redirect host and warns for unknown ones; only the browser that started the request
  may allow it (`prepza_connect` cookie: `HttpOnly`, `SameSite=Lax`, `Secure`, short-lived);
  codes are single-use, 5 minutes, bound to app, redirect URI and PKCE challenge; the page
  can't be framed. This is the confused-deputy defence.
- Every authorization answer names the issuer (`iss`, RFC 9207), advertised as
  `authorization_response_iss_parameter_supported` (the SDK's client then requires it).
- Scopes: `prepza` (everything, reading included) and `prepza:read`; the user may allow a full
  request as read only. Read-only connections list only reads; a write is an `isError` result.
  Connections from before keep `prepza`. Not adopted: a `403 insufficient_scope` step-up inside
  a tool call (hosts don't re-authorize mid-call; reconnecting does it). Never change a scope's
  meaning silently; `offline_access` is not listed.
- Non-interactive agents use a company API key with the `mcp` permission (`api.md` keys); it
  acts as its maker in its company, with only its permissions' tools (`key_tools.py`). ChatGPT
  supports no API keys; Claude's static headers are a beta.
- Every OAuth endpoint is rate-limited (`oauth_limits.py`) and answers in clients' timeouts.

## Tools

- A tool is the in-app assistant's registry tool (one behaviour, one permission check, one
  audit); MCP adds no business logic. Deleting the account or a company is never a tool.
- Names: 1–64 characters of `a-z0-9_` (the spec allows 128 of `A-Za-z0-9_-.`; Claude's
  directory caps at 64), stable: renaming or removing a tool or a parameter, making a parameter
  required or narrowing a type breaks apps and saved prompts; adding optional parameters or
  output fields doesn't. A retired tool stays, its description naming the replacement, for at
  least 12 months.
- Each tool has a `title` (Claude's directory and VS Code show it) and a description of what it
  does, when to use it, how it differs from its neighbours and its limits; descriptions describe,
  never instruct the model to call other tools or fetch instructions (tool-description injection;
  Claude's review rejects it).
- `inputSchema` is a strict JSON Schema object (`additionalProperties: false`, enums for closed
  sets, no network `$ref`). Results carry `structuredContent` and the same JSON as text for
  older clients. Not adopted: `outputSchema` (shapes vary per tool and are trimmed; it would
  bind every result to a schema the spec then requires).
- Annotations on every tool, all four explicit (the defaults are destructive and open world):
  `readOnlyHint` for reads, `destructiveHint` for what can't be undone, `idempotentHint` for
  repeat-safe writes, `openWorldHint: false` (prepza only). Hosts decide confirmations from them
  (Claude, VS Code skip it for reads; ChatGPT's review requires three); they are hints, never the
  security: every call is authorized server-side.
- Writes run at once: the host's own approval is the confirmation, and the server still applies
  the panel's checks (pause, subject, partial update, hourly actions, idempotency key).
  Elicitation (2026-07-28: `input_required` with an integrity-protected `requestState`) is not
  adopted: hosts confirm from the hints, and Claude's support is unverified.
- Errors: a business refusal, a limit or bad input is a result with `isError: true` and text
  that says what to do next; JSON-RPC errors only for the protocol. Not adopted: the spec's
  `-32602` for an unknown tool; it's a result, which the model reads and corrects itself by.
- Results are the tool's data as JSON, trimmed with `shown`/`more` and a narrowing hint, links
  built by code (absolute), only what the request needs (no internal trace ids or secrets);
  within Claude's limits (about 150,000 characters, 25,000 tokens in Claude Code, 240 s).
- Results are untrusted data for the model: candidates' answers and companies' text can hold
  instructions; the server instructions say so, and nothing returned is ever followed.
- How many: the list is filtered by the caller's permissions; large sets cost context (hosts
  switch to on-demand discovery past a few percent of it) and some clients cap active tools (the
  reported 40 in Cursor and 128 in VS Code are unverified). Prefer fewer tools that each do a
  whole job, split by read and write; no catch-all `api_request` tool.
- ChatGPT's deep research wants read-only `search` and `fetch` tools; not offered (prepza's data
  is private, per company).

## Security and operations

- Every call: token checked, account checked (disabled or deleted loses access within 5
  minutes), company membership and the AI apps switch checked by companies, secrets refused in
  arguments, calls and writes rate-limited per user, writes audited `via: "mcp"`.
- Never log tokens, codes, request ids or arguments; log refusals with ids.
- Not adopted: allowlisting Anthropic's or OpenAI's ranges: API-key agents call from anywhere.

## Testing

- Unit tests per behaviour (`tests/unit/test_mcp_*`, `test_oauth_*`), integration for storage
  (`scripts/integration.sh`), and `e2e_tests/mcp.py` through the gateway: discovery, register,
  consent, PKCE, both protocol eras, tools as the user, API keys, refresh, revoke, disconnect.
- The conformance suite (`npx @modelcontextprotocol/conformance server --url …`) targets an
  unauthenticated reference server and has no auth option, so against prepza only its
  rebinding refusal applies; `e2e_tests/mcp.py` covers the protocol instead. Check new tools in
  MCP Inspector (`--cli --method tools/list` with a token), Claude and ChatGPT themselves.

Research (local notes, git-ignored): `internal_docs/best-practices/mcp.md`.
