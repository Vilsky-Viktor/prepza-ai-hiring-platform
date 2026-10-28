---
paths:
  - "services/**"
  - "packages/**"
  - "frontend/**"
  - "infra/**"
---

# Personal data

prepza is the controller for its users' accounts and the processor for candidates' data, which
belongs to the company. Every retention, export and deletion of a candidate's data is something
the company can explain to the candidate. What is processed, why and for how long is in the
privacy policy (`services/site/src/site_content/constants/privacy.py`) and the records of
processing (`internal_docs/compliance/records-of-processing.md`, local).

## A new kind of personal data

A change that stores a new kind of personal data (a column, a table, a bucket, a queue, a log
line, a trace, a third-party call) does all of this in the same change:

- names its purpose in the records of processing (rule 9);
- gives it a retention enforced in code or Terraform (a constant and a scheduled job, partition
  expiry, topic retention) that matches the privacy policy, including rows that can get stuck
  (failed, parked, dead-lettered): "kept until published" otherwise means forever;
- adds it to the user's deletion and export in that service, idempotent, with tests;
- updates the policy's cookie list when it stores anything on the device.

## Minimisation

- Collect a field only for a named purpose. Send each processor (OpenAI, Resend, Paddle, an ATS,
  Langfuse, Sentry) only the fields its task needs: an allow-list per call, never the whole
  object.
- No inferred or special-category data about candidates: no protected characteristics, no
  imputed demographics, no proxies for them (zip codes).
- Integrity signals are only events the page itself sees (leaves, copy, fast answers); no device
  fingerprinting, and no IP address or user agent stored with a session. IPs live only as
  short-lived rate-limit keys.

## Pseudonymisation

- Pseudonymised data is still personal data: it needs a retention and a place in erasure and in
  the records.
- A hash that stands for a person (an email, an id) is keyed (`prepza_common.auth.person_hash` with
  `PERSON_HASH_KEY`, or `analytics` with its salt; both in Secret Manager), never a plain SHA-256
  anyone can recompute. The key lives apart from the data.

## Deletion and export

- One entry point fans out to every service; each service's delete and export cover every table
  holding the user's id or email. A new table with either joins both in the same change.
- Erasure reaches every copy: databases, caches, outboxes, queues, analytics, traces and error
  reports. Where a copy can't be deleted on request (backups, a processor's short log), the
  policy says how long it lasts and it's never read for anything else.
- Delete; don't "anonymise" by blanking a name while an id, an email hash or an invite id still
  links the rest.
- A deleted guest invite also deletes the guest's own accounts and records.
- The export gives the person's own data, its categories, sources and recipients; never other
  people's data or the answer key.
- Nothing is sold or shared for advertising, and no ad or cross-site tracking: that keeps "Do not
  sell or share" and Global Privacy Control moot.

## Backups and restores

- Erased data in backups is put beyond use: never restored for use, read or shared, and gone when
  the backups roll off (14 days).
- A restore or clone replays the erasures made since the backup (accounts' `erasures`, kept as
  long as the backups; the `erasures` job); dumps and clones made for a recovery are deleted when
  it's done.
- An on-demand backup is deleted once automated backups work again, so the policy's period stays
  true.

## Logs, traces, analytics

- Logs carry ids, counts and outcomes; never emails, names, tokens, session ids or secrets. A
  path that carries a secret is logged as its route template.
- Sentry: `send_default_pii=False`, scrubbing in `before_send`, no local variables, users by id.
- Langfuse: personal data masked before export, traces findable by id, and a retention that
  matches the policy.
- Analytics: keyed pseudonymous ids, no free text, a partition expiry.
- Logs of privileged access (superadmin views) go where they can't be edited and are kept for a
  stated, longer period.
- Audit logs record who did what with ids (resolved to names when read), never copies of
  people's data; a fixed retention stated in the policy; erasure replaces the person's id
  (`deleted-user`).

## Cookies and device storage

- Anything stored on or read from the device needs consent unless it's strictly necessary for
  what the person asked for (EU standard, applied everywhere): sign-in and the visitor's own
  choices are fine; anything else asks first, as the referral cookie does.

## Hiring law

- High-risk AI duties (EU AI Act: logs kept at least six months), NYC Local Law 144 (bias audit,
  notice of data, source and retention), California, Colorado and Illinois rules on automated
  hiring decide what companies must keep and tell candidates. prepza helps companies keep what
  their law requires with exports they can keep (reports, audit exports), not by storing longer by
  default. A change to retention of candidates' results is checked against them first.

Research (local notes, git-ignored): `internal_docs/best-practices/privacy-data.md`.
