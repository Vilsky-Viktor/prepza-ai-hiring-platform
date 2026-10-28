# Admin zone

The admin zone is for superadmins: prepza's own team, not a company's admins.

- Superadmins are the accounts in `SUPERADMIN_EMAILS`, signed in with Google (verified addresses; the ID token's sign-in provider is `google.com`, so Google's account security, two-step verification included, guards the zone). The same address signed in another way (GitHub, LinkedIn, a token a service signed for an AI app) isn't a superadmin.
- Only they see the Admin zone in the account menu.
- Everyone else gets "not found" from its pages and routes.

It has nine tabs, in this order: [Templates](#templates), [News](#news), [Campaigns](#campaigns), [Questions](#questions), [Pass rates](#pass-rates), [Verification](#verification), [Support](#support), [Stats](#stats) and [Controls](#controls). They're its side menu, as on a company's pages ([Companies](companies.md)); on a phone, three tabs and the rest under "…". Questions and Stats each have pages of their own, listed under them in the menu while open (on a phone, a bar across the screen under the tabs naming the open one, which opens a menu of them).

## Templates

Ready-made interviews by role (see [Templates and practice](templates-and-practice.md)).

- Generated from a role description, through the same topic review as a company's interview.
- Titles never name a company.
- Can be renamed, checked question by question, re-generated or deleted.
- Each topic shows how many practice and company questions it has ("30 practice · 60 company", see [the pools](templates-and-practice.md#the-question-bank)).
- **Top up** (while a topic is short of either) and **Add questions** (a number for every topic, 30 by default) write more in the background, with the run's progress on the page; see [Adding questions](templates-and-practice.md#adding-questions).

## News

The posts on the public [news page](site.md#news), newest first, like the templates list.

- **New post** opens a dialog: a title (up to 120 characters), a date (today unless changed) and the text (up to 500 characters, with a live count of the characters left). Library checks the limits (`MAX_NEWS_TITLE_LENGTH`, `MAX_NEWS_TEXT_LENGTH` in `prepza_common.config.constants`); the form only shows them.
- Posts are written in English only. Each row's pencil opens the same dialog to edit it; its bin deletes it after asking. Its send button, **Send as a campaign**, makes a new product update campaign from the post (its title, text and a button to it) and opens it to check and send.
- A published post goes in every user's bell (see [Notifications](notifications.md#the-bell)); deleting it takes it back.
- Each row says "translated" once the post is in every other language, "translating…" until then.

**Translation:** after a save, library asks generation (`POST /internal/news/{id}/translate`), which queues a worker job (Cloud Tasks). The job reads the post and the languages it lacks from library and queues one translation for each in generation's next OpenAI batch (the Batch API, half price; batches go out every 10 minutes and usually come back within an hour, at most 24 hours), with the translation model (meaning, not words: each language's hiring terms; "prepza" and product and ATS names kept). Each translation that comes back within the limits is saved (`PUT /internal/news/{id}/translations`).

- Until its translation is saved, a language shows the English post. A translation past the limits, or none, is asked for again in the next batch, up to 6 times, then given up; library's daily schedule sends every post that still lacks a language again. A language already waiting isn't queued twice.
- A changed title or text deletes the post's translations and starts a new translation; a new date alone keeps them. Translations of an older text that arrive after an edit are dropped, and saving the same translation again replaces it.
- While the emergency pause is on, generation refuses the request and the daily schedule sends the post later.
- Without an OpenAI key (locally), nothing is translated, and every language shows the English post.

Routes (library): `GET/POST /superadmin/news`, `PUT/DELETE /superadmin/news/{id}`.

## Campaigns

Product updates and offers emailed to the users who chose them, and important notices to everyone they concern (how they're sent: [Notifications](notifications.md#campaigns)). The list looks like the news tab: each campaign's subject, kind, day and, once sent, its counts, with a badge for where it stands (draft, sending, sent, stopped). **New campaign** opens a dialog: the kind (product update, offer or important notice), its audience, a subject, the text in an editor with bold, italic, links and lists (stored as Markdown), and an optional button with a link to a page on the site. Notifications checks the limits, the audience and that the link is on the site.

- **Important notice:** choosing it shows a warning that it reaches everyone in its audience whatever their email settings, can't be unsubscribed from, and is only for security incidents, planned downtime or changes to how prepza works, never to promote anything.
- **Audience:** a ticked list in the style of Slack's notification kinds: **Everyone**, or any of **Companies** (people on a company's team), **Candidates** (people who took a company's interview) and **Learners** (people who used free practice). Under Companies, **Owners and admins only**, and for an important notice **Only these companies**, a picker like the ATS link's interview picker (the site's pill with a search as the menu's first row, ticking several; empty means all companies). Under the list, how many it would reach now, as notifications counts them, updated as the choice changes.

A campaign's page shows its kind and audience as badges, the email exactly as it's sent, in any of the 23 languages, and, before sending, how many users would get it (an address, not suppressed, and the setting on for a product update or an offer). A draft can be edited (in English, which is translated again, or one language's own wording), deleted, tested (**Send a test to me**, to the superadmin's own address) and sent: **Send** asks to confirm with that number and starts at once; for an important notice it also shows the warning again and its button stays off until the superadmin ticks that the notice is about the service itself, not a promotion. Once sent it can't be changed; while it's going out, **Stop** skips everyone not sent yet. Its page then shows waiting, sent, skipped, failed, unsubscribed after it and spam complaints. At most `CAMPAIGNS_PER_KIND_DAY` product updates and offers of each kind go out a day (1 by default) and `NOTICES_PER_DAY` important notices (1 by default, at most 3), both limits in [Controls](#limits); one more is refused (429, "Today's limit of campaigns of this kind (1) is reached. Send the next one tomorrow.") and counted as a hit.

```
GET/POST   /notifications/superadmin/campaigns
GET/PUT/DELETE /notifications/superadmin/campaigns/{id}
PUT        /notifications/superadmin/campaigns/{id}/texts/{language}
GET        /notifications/superadmin/campaigns/{id}/preview?language=   /recipients
POST       /notifications/superadmin/campaigns/{id}/test?language=   /send   /stop
POST       /notifications/superadmin/campaigns/recipients
POST       /notifications/superadmin/campaigns/from-news/{news_id}
```

## Questions

Three tabs of its own, at `/superadmin/questions/flagged`, `/superadmin/questions/replaced` and `/superadmin/questions/patterns` (the older `/superadmin/flagged` and `/superadmin/replaced` lead there):

- **Flagged:** the flagged questions, each to fix now or dismiss. A superadmin's "Fix now" isn't counted towards the verifier's daily limit.
- **Replaced:** the questions the verifier replaced.
- Each replaced question has a "replaced with" button showing the question that took its place: the next kept version, or the question as it is now.
- **Patterns:** recurring mistakes the weekly job found in flagged and replaced questions, each written as a general rule, with the problem of the questions it comes from, how many questions showed it, and when it was first and last seen; most recently seen first. A status pill above the list shows the proposed ones (the default), approved, in use or dismissed. A proposed one is approved (a candidate rule, used only once an eval shows it helps) or dismissed (kept, so it's never proposed again, and never used), and leaves the list; who reviewed it and when is kept. One reviewed meanwhile is refused with "This pattern was already reviewed". On a phone the problem, the count and the buttons go under the rule. See [Patterns from bad questions](../generation.md#patterns-from-bad-questions).

See [Question quality](../generation.md#question-quality) for how questions get flagged.

## Verification

Companies waiting for review of their name and website (see [Companies](companies.md#verification)).

## Support

For a complaint about an account, a company's top-ups or spending, an interview or a candidate, for someone who asks prepza to stop its emails, and for a company that impersonates another or abuses prepza. A search finds what the complaint is about; its page shows what support needs, and puts a company's credits right. A candidate's questions and answers are never shown: only facts about them.

See [Admin zone: Support](admin-support.md): the search, the pages of an account, a company, an interview and a candidate, emails and logs.

## Pass rates

Lists company interviews with finished candidates, with:

- finished candidates,
- pass rate at the current passing grade,
- average grade,
- share of timed-out answers.

It sorts by lowest pass rate or most finished first. It marks the interviews outside the post-market monitoring triggers: below 10% or above 95%, with 20+ finished.

## Stats

Two tabs of its own: **General** (`/superadmin/stats/general`, below) and **AI costs** (`/superadmin/stats/ai-costs`). The older `/superadmin/stats` opens General, and `/superadmin/ai-costs` AI costs.

General has ten numbers as cards:

1. users who signed up,
2. companies created,
3. companies verified (in the month they were approved),
4. interviews created,
5. candidates invited (in the month they were invited),
6. candidates finished (also in the month they were invited),
7. talents' practice rounds,
8. top-ups,
9. what they paid, in each currency apart ("$12.3K, €4K"; tax included, refunds not taken off; a transaction counts once),
10. the credits spent on candidates.

Numbers show short from a thousand up, in the language's own way ("1.5K", "$12.3K"); money under $1,000 is exact.

### Period

- A UTC month or year, or all time with the "all time" checkbox.
- The period is one choice in a menu of two columns: a month with its year (the last 12, none before 2026) or a year.
- The menu is off while all time is on.
- The browser keeps the choice for the next visit (`localStorage`), not the address.

### How it counts

Companies, rounds and billing each count their own records, through the shared `prepza_common.db.stats`; accounts counts the sign-in accounts, which live in Firebase only, by when each was made (it reads them all, page by page; at `/library/superadmin/stats`, library's address, which the gateway and the load balancer send to accounts):

```
GET /superadmin/stats?period=2026-10   # a month
GET /superadmin/stats?period=2026      # a year
GET /superadmin/stats                  # all time
```

So the numbers are what is stored now: deleted companies and candidates past retention aren't counted.

### AI costs

What AI cost and why, for the same period as General (the choice is shared). Billing works it out from `ai_usage` and `limit_hits` (see [Credits and payments](billing.md#ai-usage-and-limit-hits)); the page only shows it:

1. **Totals:** spend in USD, AI calls, input, cached input and output tokens, and this month's spend against the monthly budget (`MONTHLY_BUDGET` in Controls, see [Limits](#limits); at 0, the month's spend alone).
2. **Who it was for:** paid companies, unpaid companies, people without a company and prepza's own work (templates, quality checks, batches, news), each with its spend and share.
3. **By action:** each action's calls, spend, paid and unpaid spend, and what one cost: one interview generation, one assistant message, one minute of transcription.
4. **By model:** calls, tokens and spend, with the share of input read from OpenAI's cache.
5. **Companies and users that cost most:** 20 of each, by spend, each opening its support page.
6. **By day,** for a month, or **by month,** for a year or all time.
7. **Shared budgets today:** today's (UTC) use of each limit for everyone: generation's new generations and quality checks, the assistant's messages and tokens and its help chat's questions and tokens, and the unpaid users' AI spend against its cap (`AI_SPEND_UNPAID_DAY`). Each owning service reads its own Redis counters.
8. **Limits hit:** ours and our providers' (OpenAI's rate limit and quota, waits in generation's own request limiter, Resend's, the ATSs', Firebase's), each with its hits in the period, its current value, and the 5 companies and users that hit it most, opening their support pages.

A service that doesn't answer leaves its part out.

```
GET /billing/superadmin/ai-costs?period=          # 1 to 6
GET /billing/superadmin/limit-hits?period=        # 8
GET /{generate|assistant}/superadmin/budgets   # 7
GET /billing/superadmin/ai-spend?company_id=|user_id=  # the support pages' line
```

## Controls

Two switches, the emergency pause and maintenance mode, the legal notices and the limits.

### Emergency pause

While it's on, every service answers these with a 503:

- new candidate interviews (invite and job-ad link starts),
- candidate invites (new, sent again or from a list),
- practice rounds,
- previews,
- generations and re-generations,
- verifier jobs,
- the help chat and the assistant (its messages and voice).

Also while it's on:

- The invite, job-ad link and new-interview pages say so; the new-interview box is turned off.
- The scheduled answer-key checks and invite reminders wait until it's off.
- Candidates already in an interview can finish.

The switch is one Redis key (`pause:on`, no expiry) that every service reads, at most every 5 seconds, so a change reaches every instance within 5 seconds. With Redis down, each instance keeps the state it last read (off if it never read one). Who turned it and when goes to companies' logs.

### Maintenance mode

Maintenance mode closes the whole site:

- Every page but the unsubscribe and legal pages (below) shows a maintenance screen. `proxy.ts` asks companies' public `GET /maintenance`, cached 10 seconds.
- Every service's API answers every request with a 503 (`prepza_common.limits.maintenance`, a middleware in each `main.py`).
- Superadmins still use the site, with a warning above each page.

These stay open, so no event, job or payment is lost:

- `/health` and `/ready`,
- the switch itself,
- `/internal/` (calls between services, Pub/Sub and Scheduler pushes),
- `/webhooks/` (Paddle, Resend, the ATSs).
- unsubscribing (`/unsubscribe/` in notifications, and its page): an email's one-click link must always work,
- the legal texts (`/help/legal/` in site, and the privacy, terms, DPA, documents and accessibility pages; `MAINTENANCE_OPEN_PAGES` in the frontend).

Billing isn't switched; its only public route is the price catalog.

Turning it on first asks to confirm, showing the number of candidates in an interview right now (a question shown in the last 15 minutes), whose time stops meanwhile.

Candidates lose no interview time to it. While it's on, rounds' expiry job finishes no interview. Turning it off first has rounds move every running interview's clocks on by the time it was on: each section's start (the interview's deadline counts from the first) and the shown time of the question on screen. Only then does it turn off. If rounds can't do it, the switch stays on and says so, and turning it off again gives the time back. A double turn-off gives it back once. The answer times recorded leave out the time it was on.

It's one Redis key (`maintenance:on`), with a second (`maintenance:started`) holding when it was turned on, which turning it off takes and removes at once. With Redis down, each instance keeps the state it last read (off if it never read one). Each service reads it at most every 5 seconds, so a change reaches every instance within 5 seconds. Who turned it goes to the logs.

### Legal notices

One row per legal document (terms, privacy policy, data processing agreement): its current version, the day it applies from, and where its notice stands. A superadmin decides whether a change is significant; **Email the change** (after a confirmation) has it emailed:

- the terms and the privacy policy to every account, the DPA to every company's owners and admins (the API says which: `audience`),
- only for a version that applies at least 14 days from now (`LEGAL_NOTICE_DAYS`), and once per version: notifications refuses otherwise, and the row says why,
- through the bulk sender, from the next sending hour (every minute from 8:00 to 18:59 UTC), nobody getting it twice, until everyone has it; it goes in the bell at once, and the site shows a banner until the version applies (see [Notifications](notifications.md#legal-notices)).

```
GET  /notifications/superadmin/legal-notices
POST /notifications/superadmin/legal-notices/{terms|privacy|dpa}
```

### Limits

Every usage limit of ours, grouped by the service that enforces it (`prepza_common.limits.limit_list.LIMITS`): the assistant (its help chat's `HELP_*` limits too), companies, generation, rounds, library (question feedback), accounts (data downloads), the API, ATS integrations, notifications (Resend's emails a day, campaigns of each kind a day, important notices a day) and billing (the unpaid users' daily AI spend cap). Among them, generous hourly limits that only stop floods of costly actions, each skipped while Redis is down: web hook test events (`WEBHOOK_TESTS_PER_HOUR`, 30 a company), interviews copied from templates (`TEMPLATE_COPIES_PER_HOUR`, 30 a company), "Download my data" (`DATA_EXPORTS_PER_HOUR`, 5 a user, as each asks every service) and ATS connections made or replaced (`ATS_CONNECTS_PER_HOUR`, 20 a company). Each shows:

- its name, window (an hour, a day, … or "at a time" for a count of what exists, such as API keys) and whom it counts (a user, a company, an address or everyone),
- its default and its hits in the last 7 days, so a change's effect shows,
- a field with its current value and **Save**, and **Reset to default** once it's changed; a limit with an unpaid counterpart (interviews a day, interviews waiting without candidates) shows both, paid and unpaid.

Only the number changes; the window stays. Billing refuses a value outside the limit's lowest and highest (422, "Use a value from … to …."), so a typo can't make it 0 or a billion; counts are whole numbers, USD keeps its cents. Saving the default removes the change.

Beside the limits, in the same groups, are the plain values the services work with (`counted=False` in the list): nothing counts against them, so they show only their default, with no window or hits, and are saved, reset and recorded the same way. A value in seconds shows "s" in its field, a share "%".

| Value | Default | Range | What it sets |
|---|---|---|---|
| `QUESTION_SECONDS_BASIC`, `_MEDIUM`, `_HARD` | 60, 60, 75 s | 10–600 | The seconds a question of a new test of that level starts with, and of a practice round on a template of that level. Existing tests keep theirs. |
| `GENERATION_CALLS_AT_ONCE` | 24 | 1–64 | The AI calls one generation (or a template's top-up) makes at once. |
| `GENERATION_CALLS_PER_SECOND` | 24 | 1–80 | The AI calls a second of every generation together, shared through Redis; OpenAI allows our account 5,000 requests and 1M tokens a minute. |
| `MULTI_ANSWER_PERCENT` | 10% | 0–50 | The share of each topic, and of each draw from it, that is "select all that apply" (see [Generation](../generation.md#select-all-that-apply)). |
| `INTERVIEW_QUESTIONS_PER_TOPIC`, `TEMPLATE_QUESTIONS_PER_TOPIC` | 70, 90 | 10–500 | The questions generated for each topic of a company's interview and of a template. A generation takes them when it starts (see [Generation](../generation.md#generation-settings)). |
| `MAX_TOPICS`, `MAX_SUBTOPICS` | 10, 5 | 1–20 | The topics an interview or template has, and the subtopics a topic has; the topic review follows them. |
| `MONTHLY_BUDGET` | $300 | 0–100,000 | The AI spend a month the AI costs tab compares this month's with; 0: no budget. |
| `RESEND_RESERVE_PERCENT` | 20% | 0–90 | The share of `RESEND_DAILY_LIMIT` bulk sends leave for invites and other service emails. |

Below them, our providers' limits, read-only with their hits, and the latest 50 changes: who, which limit, from what to what, when.

The values live in billing's `limit_settings` (only changed limits have a row), and every change in `limit_changes`. Billing writes them to the Redis hash `limits:values` on every change, at its start and every 5 minutes (`/internal/schedules/limits`), so a Redis wipe heals itself. Each service reads a limit with `limits.limit(redis, NAME)`, keeping the hash at most 30 seconds, so a change is in effect within that; with Redis down, a service keeps the values it last read (only while Redis is down; one started during the outage uses the defaults).

```
GET    /billing/superadmin/limits
PUT    /billing/superadmin/limits/{name}      {"value"}
DELETE /billing/superadmin/limits/{name}      # back to its default
GET    /billing/superadmin/limits/changes
```
