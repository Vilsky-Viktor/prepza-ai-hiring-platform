---
paths:
  - "frontend/public/embed/**"
  - "frontend/app/embedded/**"
  - "frontend/components/company/embed-view.tsx"
  - "frontend/lib/embed.ts"
  - "frontend/constants/embed.ts"
  - "frontend/proxy.ts"
  - "frontend/tests/lib/embed.test.ts"
  - "e2e_tests/signed-in/specs/i-api-embed.spec.ts"
---

# The hosted embed script

Companies show a guest candidate's interview on their own site with
`https://prepza.ai/embed/v1.js` and `Prepza.embed({element, url, theme, title, onReady, onStart,
onFinish})`, which frames `/embedded/{token}`. The script, its options, callbacks and messages
are a contract with customers' pages: any change to them is integrator-visible (rule 14) and
updates `docs/features/api.md` and the API description's snippet (rule 9). CLAUDE.md wins on any
conflict; CSP and headers are `security.md`'s, caching `performance.md`'s.

## Versions and compatibility

- The major version is in the path. Inside `v1` only add: new optional options, callbacks,
  message fields and kinds; never rename, remove or change the meaning of one, never make one
  required, never throw where v1 didn't. A breaking change is `/embed/v2.js`, served beside v1;
  v1 keeps working for at least 12 months after v2, then still loads and logs a console warning
  rather than a 404. The developer docs keep a changelog per major version.
- One file, no dependencies, no build step, ES5-level syntax plus `URL`; small (a few KB).
  Not adopted: a loader that injects content-hashed files (one small file needs no second
  request; adopt it if the script grows).
- `"use strict"` in an IIFE; exactly one global, `window.Prepza`; nothing on built-in
  prototypes; options read key by key, never merged into objects (prototype pollution).
- Including the script twice is harmless: a second copy keeps the first `Prepza`.
- Feature detection, never user-agent sniffing; what's missing degrades (no resize, a fixed
  height) instead of throwing.

## Delivery

- `Cache-Control: public, max-age=300, stale-while-revalidate=86400` (`EMBED_SCRIPT_HEADERS`):
  a fix reaches every site within minutes, visits don't wait for it. Hashed files would be
  `immutable` for a year.
- `Access-Control-Allow-Origin: *` on the script, so a site may load it with `crossorigin` and
  see its errors.
- SRI: not on `v1.js` (it changes with fixes; a pinned hash would break every site at the next
  deploy, as Stripe explains for Stripe.js). Offer SRI only for a pinned, immutable build if one
  ever ships; TLS and the site's CSP are the protection.
- The proxy skips `/embed/`: the script is served as it is, also during maintenance (the frame
  then shows the maintenance screen), with no per-request work.
- The docs tell integrators to load it with `async` (and wait for its `load` or call after it),
  and the CSP lines they need: `script-src https://prepza.ai` and `frame-src https://prepza.ai`.
  A stub that queues calls made before load (Intercom, Cal.com) would be a new API: approval.

## Who may frame it

- The embedded page sends `frame-ancestors` built per request from the company's verified
  website domain and its subdomains (`embedAncestors`, guest invites only; `'none'` when unsure,
  on a timeout or for anything else); every other page is `frame-ancestors 'none'`. Header
  only, never `<meta>`. The site's pages carry no `X-Frame-Options` (it can't list origins;
  `ALLOW-FROM` is obsolete); the API keeps `DENY`.
- The frame's address authorizes nothing by itself beyond the invite's token, which already is
  the candidate's link; the embedding domain is never trusted from `Referer` or
  `ancestorOrigins`.
- Not adopted: a separate embed origin (the frame's storage is partitioned per top-level site
  anyway and its sign-in is a guest's, apart from the main app's); `sandbox` on our own frame
  (it would only restrict our page; parents protect themselves); `loading="lazy"` (the interview
  is the page's main content).
- `allow` (Permissions Policy) grants only what the interview uses: nothing today. A feature
  that needs the camera, microphone, fullscreen or clipboard adds it to `allow` and the docs say
  the site's own `Permissions-Policy` must allow it too.

## Messages

- The frame posts only to the exact origin the script gave it (`?origin=`, checked by
  `originOf`), never `"*"`; the script accepts a message only when `event.origin` is prepza's,
  `event.source` is its own frame's window (so several embeds per page don't mix) and
  `source` is `"prepza"`.
- Every message is `{source: "prepza", version: 1, type, ...data}`; unknown types are ignored
  (forward compatible); payloads are type-checked before use (a height is a finite number,
  clamped to at least the minimum), never put in `innerHTML` or evaluated.
- No secrets in messages: only what the company may see (the candidate's id when finished, the
  height). Tokens never cross the frame boundary; the guest token comes from prepza's API
  inside the frame.
- Handshake: the frame says `ready` first; the parent attaches its listener before inserting
  the frame. The frame listens to nothing from the parent; a parent-to-frame message would need
  the same origin and source checks.

## Storage and sign-in inside the frame

- Assume no third-party cookies (Safari and Firefox block or partition them; Chrome lets users
  block them; CHIPS and the Storage Access API exist but a guest has never visited prepza first)
  and partitioned, wipeable storage (Chrome 115+, Firefox, Safari).
- The guest signs in with a custom token from the API (`signInWithCustomToken`), kept in the
  frame's partitioned storage or memory; never `signInWithRedirect` or popups in the frame.
  Calls send the ID token in a header; the `SameSite=Lax` token cookie isn't relied on there.
- Reloading the frame resumes from the server by the invite's token, never from local state.

## Size, accessibility, API

- The frame is `width:100%`, `border:0`, a 640 px minimum height so nothing jumps, and grows to
  the height a `ResizeObserver` inside reports. A maximum and scrolling inside would be new
  options.
- The frame has a `title` (the `title` option, else "Interview"); the content inside is the
  candidate's pages, which meet `accessibility.md`; no focus is taken on load and nothing traps
  focus; the theme passes through (`theme`), and color scheme and reduced motion follow the
  candidate's settings inside.
- `Prepza.embed` takes one options object and returns `{destroy}`, which removes the frame and
  the listener; several embeds per page work. A missing element throws, as v1 always did.
- Not yet adopted (new API, approval): `onError({code})` for a frame that never says `ready`
  within a timeout (an iframe's `error` event never fires) or a refused domain, typed `error`
  messages from the frame, a console warning for unknown options, `minHeight`/`maxHeight`, a
  declarative `data-prepza-url` element, and a `lang` option.

## Testing

- `i-api-embed.spec.ts` serves the company's page from another site (`jobs.acme-embed.com`), so
  partitioning and `SameSite` apply as in production: framing refused before verification and
  for email invites, the full interview in the frame, the callbacks in order, the script's
  headers. Unit tests cover `embedAncestors` and `originOf`.
- Chromium only today. WebKit and Firefox runs of the embed spec need those browsers in the
  test image (approval); Playwright's WebKit doesn't apply Safari's tracking prevention, so
  Safari is checked by hand before a change to sign-in or storage in the frame.

Research (local notes, git-ignored): `internal_docs/embed-sdk-best-practices.md`.
