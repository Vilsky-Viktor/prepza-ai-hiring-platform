# ATS integrations

A company can connect its applicant tracking system (ATS): Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR. Candidates the company moves into a chosen stage in the ATS get the prepza invite, and their results go back to the ATS.

- [Connecting an ATS](#connecting-an-ats)
- [Linking a job](#linking-a-job)
- [The ATS pages](#the-ats-pages)
- [Candidates from Workable](#candidates-from-workable)
- [Candidates from Greenhouse](#candidates-from-greenhouse)
- [Candidates from Teamtailor](#candidates-from-teamtailor)
- [Candidates from Recruitee](#candidates-from-recruitee)
- [Candidates from Breezy HR](#candidates-from-breezy-hr)
- [Results back to the ATS](#results-back-to-the-ats)
- [How it's built](#how-its-built)

## Connecting an ATS

On a company's **Integrations** tab, an owner or admin connects an ATS with its key:

| ATS | What to paste | Permissions |
|---|---|---|
| Workable | Its address and an API access token | The scopes `r_jobs`, `r_candidates` and `w_candidates` |
| Greenhouse | A Harvest V3 (OAuth) API credential's client ID and secret | The Jobs, Job Posts, Job Interview Stages and Notes endpoints |
| Teamtailor | An API key (Settings → Integrations → API keys) | Admin permission, Read/Write |
| Recruitee | Its address and a personal API token (Settings → Apps and plugins → Personal API tokens) | The token acts as the person who made it: an admin who sees every job |
| Breezy HR | An API key (your name → My Settings → API Keys) | The key acts as the person who made it: an admin who sees every position. Breezy's API and web hooks come with its Pro plan |

- A company connects or replaces an ATS connection at most 20 times an hour by default (`ATS_CONNECTS_PER_HOUR`, `429` past it), as each is checked with the ATS.
- prepza checks the key with one read before saving it. A Teamtailor key is tried in each of Teamtailor's regions (EU, North America, Asia-Pacific) until one accepts it; the connection keeps that region.
- The key is saved encrypted with `ATS_ENCRYPTION_KEY`, the ats service's Fernet key. An empty key turns integrations off. To replace it, list the new key and the old one, comma-separated, new first (see [infra/README.md](../../infra/README.md), step 8). After the key that sealed them is gone, saved keys can't be read: their connections are marked for reconnecting, and reconnecting starts afresh (Greenhouse gets a new web hook secret key to paste; Teamtailor's and Recruitee's are pasted again).
- prepza never shows the key again.
- Disconnecting deletes the key and the linked jobs at once.
- A key the ATS stops accepting marks the connection for reconnecting. Only a refusal of the key counts (401 or 403; when connecting, also a wrong address): something deleted in the ATS, like one candidate, affects only that candidate.
- While a connection waits for reconnecting, its web hooks still count, checked with the secrets it keeps: the candidates it sends wait, and results are kept. Within 10 minutes of reconnecting, the `recover` job invites those candidates and sends those results. Teamtailor's events are the exception when its key is refused: ats can't read the application, so the event is answered with an error.

## Linking a job

**Link a job** links one of the ATS's jobs, and one of its stages, to an interview; linking reads that one job and its stages from the ATS, to check them and keep their names. A job deleted in the ATS meanwhile isn't linked: "That job or stage isn't in <ATS>". The interview is either:

- an existing one, chosen in a picker whose menu starts with a search: the newest 100 at first, and any of the company's interviews by part of its title (`GET /companies/interviews?q=` in companies, `components/company/interview-picker.tsx`),
- or a new interview made from the job's text in the ATS. The company checks and edits the text first, then reviews its topics as usual.

## The ATS pages

- The Integrations tab has three groups, in this order: messaging (Slack), the API and AI apps (MCP) in one list, then the ATSs, each with a "connected" tag once connected.
- Under a connected ATS's name, on its row and its page: the account it's connected as (Workable's and Recruitee's subdomain, Teamtailor's and Breezy HR's company name). Greenhouse names no account, so it shows the company's own name on prepza instead; no member's name is kept with a connection.
- Each ATS opens its own page: `/companies/<id>/integrations/<workable, greenhouse, teamtailor, recruitee or breezy>`. Before it's connected, the page says so in place of the linked jobs.
- The page lists its linked jobs. For each job:
  - how many of its candidates were invited (an icon and the number),
  - how many are waiting or weren't invited, above **Invite again**, which tries that job's again,
  - **Unlink**, after a confirmation. The job's candidates still waiting for the interview go with it, so none is invited or has credits set aside later; those already invited stay, for writing their results back.
- Each ATS has one **Instructions** button, on its row and its page. Its dialog holds everything to know: the candidate flow, starting with a stage just for prepza, and, for a connected Greenhouse, Teamtailor or Recruitee, the web hook to set up (owners and admins only). The dialog opens by itself right after connecting any of those three.
- Every member sees these pages; viewers change nothing.

## Candidates from Workable

**Subscription.** Linking a job subscribes to Workable's `candidate_moved` events for its stage, at an address of its own: `/api/ats/webhooks/workable/<link id>`, built from `SITE_URL`. Unlinking, disconnecting, or deleting the interview or the company cancels it, as far as Workable answers (the link goes either way).

**Signature.** An event counts only when its `X-Workable-Signature` is the HMAC-SHA256 of the body with the account's token.

**Inviting once.**

- The candidate is saved once per Workable candidate and interview (a unique key).
- The web hook is answered as soon as the candidate is saved: the same transaction saves an `ats.candidate_arrived` event (only for a new candidate, so a repeated web hook adds none), and ats invites them when Pub/Sub pushes it back; companies not answering fails the push, which Pub/Sub retries.
- With the candidate's name when the ATS sends one (the first event's is kept). It goes with the invite and fills the candidate's name only while it's unknown, so an event delivered again never replaces a name an owner or admin corrected (see [Candidate names](candidates.md#candidate-names)).
- It is then claimed in one update before the invite, so a repeated or simultaneous event invites once.
- An invite cut off midway can be claimed again after 10 minutes, by **Invite again**, a new event or the ats service's `recover` job, which runs every 10 minutes.
- An event or **Invite again** invites at most 50 candidates, so it ends in time; the rest wait for the `recover` job. Not-invited candidates are put back to waiting a batch at a time (`DELETE_BATCH`), each batch its own transaction. The job invites until 20 seconds into its run (`RECOVER_INVITE_SECONDS`), taking every connection's candidates in turn (each one's oldest, then each one's second...), at most 500 read a run, so one company's backlog doesn't hold up the others; the rest wait for its next run.

**The invite** is the usual one. Companies sends it as if whoever connected Workable sent it: their limits, the company's credits, the pause. If that member is no longer an owner or admin (removed, or made a viewer), companies refuses it and the connection is marked for reconnecting by a current editor. If that member deletes their prepza account, their connections stay without their id (`deleted-user`), marked for reconnecting; their data export lists the connections they made.

- A candidate for an interview still being made waits, and is invited once it's ready (`interview.ready`).
- A candidate refused (credits, limits, the pause) is kept as not invited, and every member of the company gets an `ats_not_invited` notification (several within 24 hours add up to one, see [Grouping](notifications.md#grouping)). **Invite again** puts that job's not-invited candidates back to waiting and invites them.
- When companies fails or doesn't answer, the candidate waits and the `recover` job tries again, 6 times in all (about an hour); only then are they kept as not invited, with the notification.
- Candidates refused for lack of credits are invited again by themselves once the company gets credits: billing publishes `credits.added` after a top-up (automatic ones too), a referral reward or a chargeback reversed, and ats invites the company's credit-refused candidates from every ATS, of jobs still linked and sent in the last 30 days, as far as the credits go (the rest stay not invited, with a new notification). Billing saves the event through its outbox with the credits, so it isn't lost.

**Retention.** The saved candidates, with their emails, are deleted:

- after 365 days, by the same `recover` job,
- with their interview (`interview.deleted`),
- with their company (`company.deleted`),
- when the company erases the candidate in prepza (`candidate.removed`),
- with the candidate's account. Account deletion and export include them.

## Candidates from Greenhouse

Greenhouse's API can't set up web hooks, so the company does it once in Greenhouse:

1. Go to Configure → Dev Center → Web Hooks.
2. Add the event "Candidate or Prospect Stage Change".
3. Paste the address and secret key the Instructions dialog shows.

- The address is the connection's own: `/api/ats/webhooks/greenhouse/<connection id>`.
- The secret key is made at the first connect, and kept on reconnecting.
- An event counts only when its `Signature` header is `sha256 ` followed by the HMAC-SHA256 of the body with that key.
- A candidate whose application moved into a linked job's stage (matched by id or name) is saved and invited exactly as from Workable, as `<candidate id>:<application id>`.

## Candidates from Teamtailor

Teamtailor's web hooks are an add-on, set up by hand in Teamtailor too:

1. Turn on Webhooks in Teamtailor's Add-on feature center.
2. Go to Settings → Integrations → Webhooks and add one for the event `job_application.update`, with the address the Instructions dialog shows.
3. Teamtailor makes the web hook's signature key: paste it into the Instructions dialog and save it.

- The address is the connection's own: `/api/ats/webhooks/teamtailor/<connection id>`.
- The signature key is kept on reconnecting. Until it's saved, every event is refused.
- An event counts only when its `TT-Signature` header is base64 of `t=<timestamp>,v2=<hex>`, the HMAC-SHA256 of `<timestamp>.<body>` with that key, and the timestamp is within 5 minutes of now (an older one is refused as a replay).
- The event only says an application changed (`job_application.update` or `.create`), so ats reads the application from Teamtailor: its job, stage and candidate as they are now. It does so only while the connection has a linked job.
- When Teamtailor answers that read with 429 (too many calls), the event is answered 429 too, so Teamtailor may send it again; Teamtailor's own docs disagree on whether it retries.
- A candidate whose application is in a linked job's stage is saved and invited exactly as from Workable, by their Teamtailor candidate id.

## Candidates from Recruitee

The company sets up Recruitee's web hook by hand too:

1. Go to Settings → Apps and plugins → Webhooks and add one for the event `candidate_moved`, with the address the Instructions dialog shows.
2. Recruitee shows the web hook's secret: paste it into the Instructions dialog and save it.

- The address is the connection's own: `/api/ats/webhooks/recruitee/<connection id>`.
- The secret is kept on reconnecting.
- Recruitee tests the web hook when it's created, before its secret can be saved: until the secret is saved, events are answered and ignored.
- An event counts only when its `X-Recruitee-Signature` is the HMAC-SHA256 hex digest of the body with that secret.
- A `candidate_moved` event of subtype `stage_changed` carries the candidate's emails, the job (offer) and the new stage: a candidate moved into a linked job's stage is saved and invited exactly as from Workable, by their Recruitee candidate id.

## Candidates from Breezy HR

prepza sets up Breezy HR's web hook itself, so the company only pastes the key:

- Connecting creates a web hook in Breezy (`candidateStatusUpdated`) at the connection's own address, `/api/ats/webhooks/breezy/<connection id>`, and keeps the signing secret Breezy gives then, once. Breezy refuses web hooks without its Pro plan; connecting then fails with that reason, and nothing is saved.
- Reconnecting replaces the web hook; disconnecting, or deleting the company, deletes it in Breezy, as far as Breezy answers. If the new web hook can't be made, the earlier connection stays, with its linked jobs and candidates, marked for reconnecting.
- A key's person in several Breezy companies connects the first one.
- An event counts only when its `X-Hook-Signature` is the HMAC-SHA256 hex digest of the raw body, as received, with that secret.
- The event carries the position, the new stage and the candidate's email: a candidate moved into a linked position's stage is saved and invited exactly as from Workable, as `<position id>:<candidate id>`.

## Results back to the ATS

When such a candidate finishes, companies publishes `candidate.finished` (grade, passed, flagged), and ats writes a comment about them in the ATS, for the company's team: in the interface language of the member who connected the ATS (saved on the connection when they connect, `language`; a reconnect updates it), else in the interview's language the event carries as `language` (one of the 23 the app speaks, with the app's own words for grade, passing grade, flags and scorecard), and in English when neither is known. The texts are in `services/ats/app/templates/languages/<language>.py`:

- their grade,
- whether they passed,
- any integrity flags,
- a link to their scorecard.

| ATS | Where it's written |
|---|---|
| Workable | As the Workable member of whoever connected it (or an admin) |
| Greenhouse | A note on the candidate's application |
| Teamtailor | A note on the candidate, as the Teamtailor user of whoever connected it (or an admin) |
| Recruitee | A note on the candidate, as the person whose token it is |
| Breezy HR | An internal note on the candidate in that position, as the person whose key it is |

- It's sent once (`reported_at`, set only once the ATS took it): claimed before writing, with the results (`report_claimed_at`), so of two events at once only one writes; results that can't go now free the claim. A write cut off midway (the server stopped) leaves a claim that goes stale after 10 minutes, and the `recover` job writes the results again.
- When the ATS fails or doesn't answer, the results are kept and the event is done, so one company's ATS doesn't hold up events for everyone. The `recover` job (every 10 minutes) sends kept results again, the longest kept first, every connection's in turn, none started past 35 seconds into the run (`REPORT_SECONDS`), until they go back or the candidate is deleted after 365 days.
- A key the ATS refuses marks the connection for reconnecting, and so does its connector losing editor rights or deleting their account. The company gets a `connection_broken` notification each time it stops working, once (the status change is the guard). Results are kept while it waits, and the `recover` job sends them once it's reconnected.
- A refused write (a candidate's results) while the key still reads is a key without write access, not a revoked one: an ATS doesn't always say which (Workable answers 401 to both), so ats asks for the jobs again with the same key. If that works, the connection keeps inviting, the results are kept for the `recover` job, which sends them once the key can write, and the company gets an `ats_cannot_write` notification, once (`write_refused_at` on the connection; a reconnect or a write that goes through clears it).
- Connecting Greenhouse checks write access too: its introspection lists the token's scopes, and a credential without `harvest:notes:create` is refused, asking for the Notes endpoints. Any other answer lets it connect. The other four ATSs document no way to check write access without writing something; their connect steps name the access the key needs.
- A candidate gone from the ATS (404) is given up, alone.

## How it's built

- All of it is the `ats` service (`services/ats`, its own database).
- It asks companies who is a member or editor, the interviews' titles, and to send invites.
- A candidate who couldn't be invited keeps when that first happened (`ats_candidates.failed_at`, migration 0012; a retry that fails again keeps it). The assistant's `get_updates` reads them one by one through `POST /internal/candidates/not-invited` (those who first failed after `since` and up to `until` and still aren't invited, with the interview's title, the ATS, the reason and a link to the ATS's page); only the assistant's service token may call it ([AI apps over MCP](mcp.md#whats-new-get_updates)).
- Each ATS's API is one client module (`app/integrations/workable.py`, `greenhouse.py`, `teamtailor.py`, `recruitee.py`, `breezy.py`) with the same functions. Each names the credentials it takes (`KEYS`), so a connection can keep others, like a web hook's secret key.
- `app/integrations/ats_clients.py` picks the module by provider. A new ATS adds its module there.
- The web hook handlers are in `app/services/ats_webhooks.py`, one per ATS.
- The webhook routes stay open in maintenance mode (see [Admin zone](admin-zone.md#maintenance-mode)).

See also [Architecture](../architecture.md) for the events ats consumes.
