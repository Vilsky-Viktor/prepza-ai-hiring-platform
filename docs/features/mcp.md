# AI apps over MCP (Claude, ChatGPT)

A user connects prepza to their own AI app (Claude, ChatGPT, Claude Code, or any app that speaks the Model Context Protocol) and asks it about their companies, interviews and candidates, or to make changes, in that app's chat. The app calls the in-app assistant's tools as the user, with exactly their permissions; no model runs on prepza's side. The MCP server and its OAuth authorization server are part of the assistant service (`services/assistant`).

- [Connecting](#connecting)
- [The authorization flow](#the-authorization-flow)
- [API keys](#api-keys)
- [Tools](#tools)
- [What's new (get_updates)](#whats-new-get_updates)
- [Calling the services as the user](#calling-the-services-as-the-user)
- [Connections and tokens](#connections-and-tokens)
- [Limits](#limits)
- [Audit and analytics](#audit-and-analytics)
- [Routes](#routes)
- [Settings](#settings)

## Connecting

- The server's address is `<SITE_URL>/mcp` (`https://prepza.ai/mcp`). The company's Integrations → AI apps page shows it with the steps for Claude (Settings → Connectors → Add custom connector) and ChatGPT (Settings → Apps & Connectors, developer mode), and Claude Code's one line: `claude mcp add --transport http prepza <SITE_URL>/mcp`, and links to the developer docs for the rest.
- The developer docs' **MCP** tab (`/api-docs?tab=mcp`, English like the rest of the docs) has it all: the server and both ways to sign in, the same steps for Claude and ChatGPT (the AI apps page's own sections, `components/company/ai-apps-setup.tsx`), Gemini CLI, Cursor, VS Code with GitHub Copilot and Le Chat, example agents in Python and TypeScript (a shared sign-in file, then LangGraph, LangChain and LlamaIndex, each pinning the versions it was run with; the files in `frontend/content/mcp/` are what the tab shows), the rules an agent meets, and every tool with its hints and the API key permission it needs. Tools and limits come from the server itself (`GET /api/assistant/mcp/tools`: the listed tools' names, descriptions, hints and `key_permission`, and the limits; public, no user data, cached an hour), so the tab never drifts from it.
- The app opens prepza's consent page, `/connect?request=…`, in the browser. A signed-out user signs in there first (the request is read only signed in). A request that expires (its 10 minutes include signing in) or was already answered shows the expired state, also when it runs out while the page is open. The page names the app, the site it returns to (`redirect_host`) and the user's account, lists what it can and can't do, and has Allow and Deny. An app whose site prepza doesn't know gets a warning. **Allow changes** (a switch, on by default) lets the user connect an app that asked for everything as read only; an app that asked only to read gets no switch, and the lists say it can't change anything.
- The app is known by the site it returns to, not by the name it gives itself (`app/constants/mcp.py` `KNOWN_CLIENTS`, `KNOWN_SCHEMES`): `claude.ai` and `claude.com` are Claude, `chatgpt.com` is ChatGPT, `chat.mistral.ai` is Le Chat, `vscode.dev` (its `/redirect`) and the `vscode://` scheme are VS Code, and `cursor://` is Cursor. Only `https` sites and exactly these schemes count. An app on the user's own computer (a `localhost` or `127.0.0.1` address: Claude Code, Claude Desktop, MCP Inspector) is known too and named as it says, since its code never leaves that computer. Any other site is unknown, named as it says.
- **Scopes.** `prepza` is everything the user may do, reading included; `prepza:read` is only reading (both in `scopes_supported` of both metadata documents, `MCP_SCOPES`). An app asks for one; the user may allow a full request as read only. The code, the connection (`mcp_grants.scope`, assistant migration 0009) and every token carry the granted scope, and a refresh keeps it. A read-only connection lists only the reads, and a write it calls anyway is a result with `isError`: "This connection can only read. To let the app make changes, connect it again and allow changes." Connections made before scopes existed keep `prepza` (the column's default), so apps already connected notice nothing. API keys have their permissions instead and act with both scopes.
- A connection belongs to the account, not to a company: the app acts in every company the user is in. The AI apps page lists the user's connected apps (name, site, when connected and last used) on every company's Integrations tab, and Disconnect stops one at once.

## The authorization flow

OAuth 2.1 with PKCE (`S256`) and dynamic client registration, from the MCP SDK's building blocks (`mcp` 2.x, `mcp.server.auth`), at the site's root:

1. The app calls `/mcp` and gets a `401` whose `WWW-Authenticate` names the resource metadata (`/.well-known/oauth-protected-resource/mcp`, also at `/.well-known/oauth-protected-resource`). That names the site as the authorization server, whose metadata is at `/.well-known/oauth-authorization-server`.
2. It registers at `/register` (public clients without a secret are welcome; `token_endpoint_auth_method: none`). Its registration is kept in Postgres (`oauth_clients`). A return address that would run or read something in the browser (`javascript:`, `data:`, `vbscript:`, `file:`) is refused (`invalid_redirect_uri`); a desktop app's own scheme (`cursor://`) is welcome, as an unknown app. Only an `https` address can be a known site (Claude, ChatGPT), and an app named after its host gets at most 80 characters of it. Instead of registering, an app may name itself by its Client ID Metadata Document (the metadata advertises `client_id_metadata_document_supported`; Claude and ChatGPT prefer it): its `client_id` is the document's HTTPS address (with a path). prepza reads it when the app first asks to connect (`app/services/client_documents.py`): only from a public address, connected to the address that was checked, no redirects, within 5 seconds and 4,000 bytes (`prepza_common.public_urls`); the document must name itself by that address, have no secret (`token_endpoint_auth_method: none`) and return only to addresses that open an app. Its copy is kept in `oauth_clients` (ids up to 512 characters, migration 0008) and read again once a day; while the site doesn't answer the kept copy serves, and a document no longer valid refuses the app. A return address on the user's own computer (`http://127.0.0.1` or `localhost`) matches its registered one on any port (RFC 8252), as such an app listens on whatever port is free.
3. `GET /authorize` (the SDK checks the client, the redirect URI, the scope and PKCE) keeps the request in Redis for 10 minutes and sends the browser to `/connect?request=<id>`. A `resource` other than `<SITE_URL>/mcp` is refused (`invalid_target`). Any other answer the SDK would redirect (an error, to the address the app registered) is a 400 page instead, as is a request missing its fields, so `/authorize` never sends a browser anywhere but the consent page (anyone can register an app with any address).
4. The consent page reads it (`GET /api/assistant/connect/{id}`) and answers with the user's Firebase token. Only the browser that asked can allow it: `/authorize`'s redirect sets an HttpOnly cookie, `prepza_connect`, with the request's id (path `/api/assistant/connect`, for the request's 10 minutes), and `approve` refuses without it (403, "started in another browser"), so a consent link someone started for their own app and sent can't connect it to the clicker's account; the request stays for its own browser. Then `POST …/approve` takes the request (Redis `GETDEL`, so it's answered once) and makes a single-use code bound to the user, the app, the redirect URI and the PKCE challenge (Redis, 5 minutes, kept as its hash); `POST …/deny` returns `error=access_denied`. Either answers `{"redirect_url"}`, where the page sends the browser; both name the issuer (`iss`, RFC 9207, advertised as `authorization_response_iss_parameter_supported`), so an app that talks to several authorization servers can tell the answer is prepza's.
5. `POST /token` exchanges the code with the PKCE verifier for an access token (1 hour) and a refresh token (90 days). The code works once. A code exchange or a refresh naming a `resource` other than `<SITE_URL>/mcp` is refused (`invalid_target`, checked before the SDK's handler, which doesn't pass `resource` on); one naming none is for `/mcp`.
6. A refresh replaces both tokens; the old refresh token then gets `invalid_grant`. Of two refreshes with one token only the first wins. The replaced token is remembered with when (`previous_refresh_hash`, `refreshed_at`): used again within a minute (`REFRESH_REUSE_GRACE_SECONDS`), it's an app refreshing twice at once and only refused; later, it's likely a stolen copy, and the connection is revoked, so the app asks the user again (OAuth 2.1).
7. `POST /revoke` (the app removed there) deletes the connection.

## API keys

An agent on a server, with no browser, signs in with a company's API key (`Authorization: Bearer pz_...`) instead of OAuth.

- Only a key with the **mcp** permission works here (ticked when it's made; [Permissions](api.md#permissions)); any other gets the same `401` as an unknown token, so OAuth apps notice nothing.
- The assistant's token check (`app/services/oauth_provider.py`) sends `pzm_` tokens to its own OAuth storage and `pz_` ones to the api service's `POST /internal/keys/verify` (`app/integrations/api_keys.py`), which checks the key as the API does: expired, deleted, or its maker no longer an owner or admin, it doesn't work.
- It acts as the member who made it, in its company only. The tools it's offered and may call are the ones its other permissions allow (`app/constants/key_tools.py`, a permission for each tool; the company's own details, the pause, the guide and prices need only `mcp`). The team, brand, settings, billing, integrations and the account's own tools are never listed for a key; one called anyway answers "This API key doesn't have the <permission> permission." or that there's no such tool. So `mcp` with `candidates:read` alone is a read-only agent.
- Kept to its company where membership is checked, not only in the assistant: the signed `X-Assistant` header carries the key's company and id, and companies refuses any other company with a `403` ("This API key works only in its own company.", `services/access.py`); the companies list answers only the key's.
- Its calls count against the company's API limit (60 a minute across its keys, shared with the API), and its maker's 30 writes an hour apply too. A company that turned AI apps off refuses keys too.
- Its actions are audited `via: "mcp"` with the key's id (`audit_events.key_id`, companies migration 0046), so the action log tells a key from an app; the funnel records `client: "api_key"`.

## Tools

- Every tool of the in-app assistant (`app/services/registry.py`), except `delete_account` and `delete_company` (`MCP_EXCLUDED`): deleting the account or a company (with its paid credits) is done in prepza itself, and calling them answers so. The panel's own `show` and `sign_out` aren't offered, nor the bell (`list_notifications`, `MCP_UNLISTED`): it names candidates of every company the user is in, past the companies that don't allow AI apps.
- A company's owners and admins can turn AI apps off for it (**Allow AI apps** on its AI apps page, on by default; `companies.ai_apps_off_at`, audited as `ai_apps_changed`). While it's off, every company route that checks membership answers an AI app (the signed `X-Assistant` header naming `mcp`) with a `403` saying so; the app itself and the in-app assistant go on as before. The setting is changed only in prepza itself, never through the assistant or an app.
- Each tool has its description and parameters as the assistant's model sees them (where the panel's description is only a route's short summary, an app gets a fuller one, `app/constants/mcp_descriptions.py`: what it does, when to use it, its key arguments; the panel keeps its own, as its evals measured worse with them), a `title` the app shows (`app/constants/mcp_titles.py`), and all four hints for the app's own approval prompt, never left to their defaults (destructive, open world): reads are `readOnlyHint` and `idempotentHint`, never destructive; writes carry `destructiveHint` (the actions the panel warns about) and `idempotentHint` (`PUT` and `DELETE`); none reaches the open web (`openWorldHint: false`).
- A write runs at once: the app asks the user before calling it, instead of the panel's confirmation card. It still passes the panel's checks (`app/services/mcp_tools.py`): the emergency pause, what it's about must be the user's (`subject`, else a `404`), a partial update sends only what changes (nothing to change is refused), and it counts against the user's 30 actions an hour. It runs once with a new `Idempotency-Key`.
- A string argument holding a secret, however deep in a list or an object, is refused with the chat's "secrets never through the chat" reply, before anything is sent.
- Every call counts against the user's calls limits, refused ones too (an excluded or unknown tool, a key without the permission, a write on a read-only connection, a secret in the arguments), so probing isn't free; only a call for an account that's gone isn't counted, as there's no user to count it for.
- A refused call (an excluded or unknown tool, a key without the permission, a write on a read-only connection, a secret in the arguments, an account that's gone, a company that isn't the user's) is logged with the user's and the connection's (or key's) ids and the tool's name only (an unknown one cut at 64 characters); tokens, codes, request ids and arguments are never logged. A request to `/authorize` that can't be read is logged by its error's type only.
- A result is the tool's data as `structuredContent`, and the same JSON as text for apps that read only text (trimmed as for the model, with `shown`/`more` on a cut list) and `links` to the prepza pages that show it, absolute. An error (the service's own, in the user's language, or a limit) is a result with `isError`.
- The server's instructions (`app/prompts/mcp.py`) tell the app to get ids from the companies tools, to call `get_updates` first when the user asks what's new or how hiring is going, to use `get_platform_guide` for how-to and pricing and `list_guides` and `get_guide` for hiring advice, never to ask for secrets, that deletions are done in prepza, and the same parent rule as the panel (`app/prompts/parents.py`): never mix candidates of different interviews or interviews of different companies in a list or an action; ask for the company, then the interview, unless the user named it or there's only one.
- Streamable HTTP, stateless, with plain JSON answers: no sessions and no streams held open, so any assistant instance answers any request. It speaks every revision up to 2026-07-28: older apps start with `initialize`, newer ones send each request on its own (the protocol version and capabilities in its `_meta`, `Mcp-Method` and `Mcp-Name` headers). Browser-based apps (MCP Inspector) may call it: its CORS answer allows every revision's headers (`MCP_REQUEST_HEADERS`), with no credentials, as access rides on the bearer header.
- `tools/list` and `server/discover` tell an app how long it may reuse them (`ttlMs`: 5 minutes, `CACHE_TTL_MS`, so a changed tool or a key's new permissions reach it soon): the tools only for the same caller (`cacheScope: private`, as they vary by an API key's permissions and a read-only connection), the server's description for anyone (`public`). The tools' order is fixed, so an app's prompt cache holds.

## What's new (get_updates)

MCP can't push: an app connects for a call and disconnects, and doesn't show a server's notification as a message. So the app asks, and `get_updates` makes asking cheap; a daily scheduled task in the app (ChatGPT's scheduled tasks) turns it into a morning summary. The developer docs' MCP tab has a **Daily updates** section with that tip. Real push stays Slack, email digests and web hooks.

- **What it tells**, newest first, grouped by company and then interview, each with a link to its prepza page: each candidate who started or finished (with their grade and whether it reached the pass mark), invites not delivered, each ATS candidate who couldn't be invited, each question flagged or fixed, and the bell's other notifications (interviews ready or cancelled, automatic top-ups, ...). Before them, a summary with a count of each kind and of those who passed. Companies running low on credits that no automatic top-up refills come with every check while it lasts, for their owners and admins only.
- **Where it comes from** (`app/services/update_sources.py`): each service tells its own, one per candidate or question, through an internal route only the assistant's service token may use (others get `403`): companies `POST /internal/candidates/updates` (the invites' `started_at`, `finished_at`, `undelivered_at`), ats `POST /internal/candidates/not-invited` (`failed_at`, kept from the first failure), library `POST /internal/questions/updates` (`flag_raised_at` and revisions marked `fixed`), notifications `POST /internal/updates` (the bell's company notifications), and billing `GET /internal/companies/low?ids=`. The bell's own notifications of the kinds the services tell one by one (which it groups) are left out, so nothing is told twice. Reading marks nothing as seen in the bell.
- **Since the last check, per connection:** each app connection (its grant) and each API key keeps the time of its last call (`update_checks`, assistant migration 0007). A call covers from there (the first one, the last 7 days) up to 30 seconds before it was made, and the next one starts there: a step saved in a transaction still open when a check runs is stamped before it can be read, so it reaches the next check instead of none. So each update reaches each connection once, and one app's check hides nothing from another. A `since` argument (ISO 8601; without a zone, UTC) asks for a period instead and doesn't count as a check; anything else is refused with "since must be an ISO 8601 time, like 2026-10-01T09:00:00Z." `company_id` keeps to one company. The daily retention deletes checks unused for 90 days.
- **What it may read:** only companies that allow AI apps; an API key only its own company and needs `candidates:read`, and `credits:read` to hear about credits. At most 50 updates are listed (`shown`, `more`); the summary counts them all. It's a read (`readOnlyHint`) and counts against the same limits.
- In the in-app panel it reads the last 7 days (or `since`) of every company of the user's, and keeps no check.

## Calling the services as the user

The tools call the other services' user-facing routes exactly as the panel does, with a Firebase ID token of the user's, so every role, rule and the language apply unchanged. The assistant gets one per user (`app/integrations/firebase_tokens.py`): it reads the account with the Admin SDK (a deleted or disabled one gets nothing, and a custom token is never made for an unknown uid, which would create that user), signs a custom token for it and exchanges it at Firebase's `accounts:signInWithCustomToken` with the public web key (the Auth emulator's locally). The token is kept in memory for at most 5 minutes (`MAX_KEEP_SECONDS`), so an account disabled or deleted meanwhile loses an AI app's access within 5 minutes on every instance, and dropped after `update_language` so the next calls use the new language. In Google Cloud the assistant's account needs `roles/firebaseauth.viewer` and to sign as itself (the custom role `prepzaTokenSigner`, only `iam.serviceAccounts.signBlob`, on itself; `infra/terraform/iam.tf`).

## Connections and tokens

- `mcp_grants` (Postgres `assistant`), one row a connection: the user, the app, the name and site the user saw, when it was connected and last used (written at most once an hour), and the SHA-256 hashes of its tokens (`pzm_…`, opaque) with their expiry. A leaked database gives no working tokens.
- `GET /api/assistant/connections` lists the user's own; `DELETE /api/assistant/connections/{id}` disconnects one (a `404` for one that isn't theirs).
- Deleting an account deletes its connections; "Download my data" lists them (`connected_ai_apps`: name, site, dates).
- The daily retention (`/internal/schedules/retention`) deletes connections whose refresh token expired and registered apps that have had no connection for 30 days.

## Limits

Counted in Redis; with Redis down they're skipped rather than refusing everything. Each is one of `prepza_common.limit_list`'s, at the default below until a superadmin changes it in the admin zone's Controls tab (see [Admin zone](admin-zone.md#limits)); the developer docs' MCP tab reads the current calls and writes limits from the assistant.

| Limit | Default |
|---|---|
| Calls of a user's apps | 60 a minute, 3,000 a day |
| Writes (with the panel's actions) | 30 a user an hour |
| Registrations | 300 an address an hour, 20,000 a day for everyone, above what one address can reach (Claude and ChatGPT register from their own servers); one over 4,000 bytes is refused (`invalid_client_metadata`) |
| Requests to connect (`/authorize`) | 120 an address an hour (429, `invalid_request`); a `state` over 512 characters is refused |
| Token requests (`/token` and `/revoke`) | 30 an app from one address a minute (429, `invalid_request`), counting failed exchanges (a bad code or refresh token) too; counted per address as well, so naming a well-known app's public id can't use up its limit for everyone |
| Connections a user allows | 20 an hour |

The services' own limits (generation, emails, credits) apply as they do in the app, and so do the emergency pause and maintenance mode.

## Audit and analytics

- Calls to companies carry the signed `X-Assistant` header issued as `mcp`: a candidate's results read through an app are audited with `via: "mcp"` and kept out of the "results viewed" funnel.
- Funnel events (`internal_docs/business/measurement.md`): `mcp_connected {client}`, `mcp_disconnected {by: user|client}`, `mcp_action {tool, ok}` for writes, and `mcp_active {client}` at most once a day for each user and app (`client` is `claude`, `chatgpt`, `le_chat`, `cursor`, `vscode`, `api_key` or `other`).

## Routes

| Route | What |
|---|---|
| `/mcp` | The MCP endpoint (bearer token) |
| `/.well-known/oauth-protected-resource/mcp`, `/.well-known/oauth-protected-resource` | The resource's metadata |
| `/.well-known/oauth-authorization-server` | The authorization server's metadata |
| `/authorize`, `/token`, `/register`, `/revoke` | OAuth |
| `/api/assistant/connect/{id}` (`GET`, `…/approve`, `…/deny`) | The consent page's API (Firebase token) |
| `/api/assistant/connections` (`GET`, `DELETE …/{id}`) | The user's connected apps (Firebase token) |
| `/api/assistant/mcp/tools` | The listed tools and the limits, for the developer docs (public) |

The root paths are exact matches in the gateway (`gateway/nginx.conf`) and the load balancer (`infra/terraform/locals.tf` `mcp_paths`), sent to the assistant as they are; no frontend page may use them.

## Settings

| Setting | What it sets |
|---|---|
| `SITE_URL` | The issuer (the site's root) and the resource (`<SITE_URL>/mcp`); where the consent page is |
| `FIREBASE_WEB_API_KEY` | Firebase's public web key (the frontend's `NEXT_PUBLIC_FIREBASE_API_KEY`), to sign the user in for the services |
