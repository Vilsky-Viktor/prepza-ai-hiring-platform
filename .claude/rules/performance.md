---
paths:
  - "frontend/**"
  - "infra/terraform/load_balancer.tf"
  - "infra/terraform/services.tf"
  - "infra/terraform/locals.tf"
  - "gateway/**"
---

# Web performance

## Targets

- Google's Core Web Vitals at the 75th percentile of real visits, phones and desktops apart:
  LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1. Field data (Sentry's Web Vitals, Search Console's
  report) decides; Lighthouse only explains. No second vitals reporter beside Sentry (rule 10).
- API latency targets in two grades (e.g. 90% under 100 ms, 99% under 400 ms); the services'
  targets and costs are in `internal_docs/operations/capacity-and-costs.md` (local).
- Adding a client dependency: `pnpm next analyze --output` before and after, and compare.

## Rendering and data

- Pages and layouts are Server Components; `"use client"` goes on the smallest leaf that needs
  state, effects or browser APIs. Work that only turns data into markup (markdown, highlighting)
  runs on the server.
- Independent requests run together (`Promise.all`), never one after another.
- A page that waits on a slow or possibly cold service shows its frame first (`loading.tsx` or
  `<Suspense>`, built from the page's existing frame, rule 7) or marks the clicked link as
  pending.
- Pages are rendered dynamically because of the nonce CSP: no Partial Prerendering, Cache
  Components or experimental SRI. Public API data is cached with `revalidate` (300 s) per
  instance and given up on after a few seconds, so the page shows without it; no shared cache
  handler (rule 4).
- The proxy skips `_next/*`, link prefetches (but those of a language's address, which only its
  rewrite finds) and static files.

## Images and fonts

- `next/image` with `width` and `height` (or `fill` and `sizes`), so room is reserved and a
  fitting size downloads; only the first screen's main image gets `preload`
  (`fetchPriority="high"`); `sizes` whenever the shown width differs from the file's. Small
  fixed-size logos and SVGs may stay `<img>`.
- Fonts through `next/font`; preload only what the first screen uses; script fonts per script,
  CJK only for those languages.

## JavaScript and third parties

- Heavy or rarely used code loads on demand (`import()`, `next/dynamic`), never eagerly in the
  root layout.
- INP: little script work during load, short event handlers that yield, a small DOM, no layout
  thrashing.
- A third party's script starts when the component that needs it appears, not at the click and
  not on every page: Paddle.js on the first purchase, Turnstile rendered explicitly when its form
  mounts (with a `preconnect`) and executed on submit, the video player only when its window
  opens (no-cookie domain). Sentry: low `tracesSampleRate`, no Session Replay.
- `next/script` strategies by need: `afterInteractive` by default, `lazyOnload` for widgets.

## Delivery

- Hashed build files are cached for a year (`immutable`); other static files in `public/` get an
  explicit `Cache-Control` (a day for logos, short with `stale-while-revalidate` for the embed
  script); responses are compressed (Brotli at the CDN where it's on).
- Streaming passes through every hop unbuffered (nginx: `X-Accel-Buffering: no`).
- HTTP/2 and HTTP/3 are left to the load balancer.
- Cold starts: startup CPU boost, lazy initialisation, and minimum instances where the cost is
  decided (`internal_docs/operations/capacity-and-costs.md`).

Research (local notes, git-ignored): `internal_docs/best-practices/web-performance.md`.
