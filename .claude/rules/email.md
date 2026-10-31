---
paths:
  - "services/notifications/**"
  - "packages/common/src/testee_common/events/notifications.py"
---

# Email

Service mail (invites, team invites, billing, legal notices) and optional mail (digests,
reminders, campaigns) through Resend, to a global audience in each recipient's language.

## Every email

- RFC 5322: Date, Message-ID, one From; a plain-text part next to the HTML.
- `Auto-Submitted: auto-generated`; a Reply-To that reaches a mailbox someone reads (its domain
  has MX records).
- An idempotency key derived from its event id, row or sent log, so a retry or redelivery never
  sends twice (rule 11).
- The operator's name and postal address in the footer; an honest subject and sender.
- No click or open tracking, no link rewriting, no tracking pixels.
- Subject, preheader, body and footer in the recipient's language (their setting, else the
  context's: the interview's language for candidates), with numbers and dates formatted for it
  and punctuation inside the translated text, never appended by code. Subjects short (about 40
  characters show on phones), meaning first.

## Accessible, right-to-left HTML

- `<html lang dir>` and `dir` on the content tables; `text-align` by direction; mirrored
  paddings; URLs, emails and the Latin wordmark wrapped `dir="ltr"`.
- Layout tables `role="presentation"`; one `<h1>`, then `<h2>` for sections (never a bold `<p>`);
  `alt` on every image (empty for decorative ones).
- Text, small footer text included, at least 4.5:1 contrast against its background.

## Streams and domains

- Service mail and optional mail go from their own subdomains, so complaints on one don't sink
  the other. Mail sent for many companies to addresses they supply (candidate invites) is
  watched apart, as one company's bad list hurts every sender on that identity.
- Service mail carries no promotion. Optional mail needs the user's setting (off by default, with
  a consent log), carries a visible unsubscribe link and one-click `List-Unsubscribe` (one HTTPS
  URI) with `List-Unsubscribe-Post: List-Unsubscribe=One-Click`, both covered by DKIM; the POST
  needs no cookies or auth, never redirects, answers 204 and takes effect at once (within 48
  hours at most).
- A spam complaint about optional mail turns it off.
- A new sending domain or a much larger volume is warmed up: start low, raise the cap weekly over
  about six weeks, watch deferrals, bounces and complaints per mailbox provider.

## DNS

- SPF and DKIM (at least 1024-bit, 2048 preferred) on every sending domain, SPF on the
  Return-Path subdomain and under 10 lookups; DMARC aligned, moving from `p=none` to
  `quarantine` and `reject` once every legitimate sender passes; reports go to a mailbox someone
  reads. Third parties that send as us (Firebase Auth) get their own SPF and DKIM on a subdomain.
- Email DNS (SPF, DKIM, DMARC, MX) changes in the same change as `infra/README.md`, which lists it
  as it is now (rule 9).
- Keep under 0.1% spam rate (never 0.3%), watched in Google Postmaster Tools and Microsoft SNDS.

## Sending through Resend

- Pace under Resend's limit (10 requests a second per team). A 429 goes back to Pub/Sub, which
  retries with backoff inside the 24-hour idempotency window; a final refusal isn't retried.
- A 409 `invalid_idempotent_request` (same key, changed payload) means it was already sent: don't
  retry. `concurrent_idempotent_requests` is safe to retry. Daily and monthly quota errors are
  counted as quota, not rate limits.
- Tagged mail (bounce routing) is sent one by one; the batch API has no tags.

## Bounces, complaints, suppression

- Resend's webhooks are verified with Svix on the raw body, with a 5-minute window, and handled
  idempotently: `email.bounced` (permanent), `email.complained`, `email.suppressed` and
  `email.failed` update testee's records (an invite shows as undelivered);
  `email.delivery_delayed` is temporary.
- Nothing is sent to a suppressed address: every send path checks testee's suppression list, not
  only bulk sends. Hard bounces and complaints suppress at once; repeated soft bounces over two
  weeks too.
- Removing an address from testee's list also removes it from Resend's, or says it stays there.

## Consent and law

- Marketing mail needs prior consent (EU ePrivacy, UK PECR), except the soft opt-in for existing
  customers with an opt-out every time; proof of consent is kept. US commercial mail (CAN-SPAM)
  needs honest headers, a postal address and an opt-out honoured within 10 business days.

Research (local notes, git-ignored): `internal_docs/best-practices/email.md`.
