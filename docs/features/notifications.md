# Notifications and emails

The `notifications` service sends prepza's emails and keeps the bell's notifications. Both are driven by events (see [Architecture](../architecture.md#events)).

- [The bell](#the-bell)
- [Slack](#slack)
- [Emails](#emails)
- [How it's built](#how-its-built)

## The bell

A bell next to the account menu shows notifications live: it updates within a second, without reloading. Each open tab holds a stream; one user may hold 10 at once (`MAX_STREAMS_PER_USER`), so one account can't take every slot. A tab past that is refused, and keeps trying (at most once a minute) until a slot frees. A closed tab gives its slot back at once; a slot left by a crash frees itself an hour after the user's last stream opened (`STREAM_SLOT_SECONDS`), and refused tabs don't extend that. A user's companies are kept for a minute (`COMPANY_IDS_SECONDS`), so tabs reconnecting don't each ask companies; a stream ends after 5 minutes and reconnects, to hear a company joined meanwhile, and joining or creating one reconnects the bell at once with the companies read fresh (`?fresh=true`). While companies doesn't answer, a stream still opens with the user's own notifications and tries again after a minute. Tabs reconnect at spread-out times, so a deploy doesn't bring them all back at once.

- A badge counts the unread ones.
- It shows the latest 10.
- Each person or company keeps at most 100, none older than 90 days.
- A deleted company's notifications go with it.
- AI apps hear what reached a company's bell through the assistant's `get_updates` ([AI apps over MCP](mcp.md#whats-new-get_updates)), which reads `POST /internal/updates`: the company notifications of the given companies after `since` and up to `until`, newest first. Only the assistant's service token may call it (others get `403`), and reading marks nothing as seen.

### What gets a notification

Only what matters, for every member of a company:

- a candidate finished (with their grade),
- an invite not delivered,
- an interview ready or cancelled,
- a flagged and fixed interview question,
- a referral reward,
- an automatic top-up charged or failed,
- an ATS candidate who couldn't be invited (`ats_not_invited`, see [ATS integrations](ats.md#candidates-from-workable)),
- an ATS that takes the company's key but refuses the results written back (`ats_cannot_write`, once until the company reconnects or a write goes through; in the bell only),
- an ATS or Slack connection that stopped working and needs reconnecting (`connection_broken`, once each time it stops; in the bell only, opening its page),
- an API web hook that stopped because the member who added it is no longer an owner or admin (`webhook_stopped`, once; in the bell only, opening the API page).

Companies' verification decisions reach only the owner and admins, one notification each, as viewers can't act on them (see [Companies](companies.md#verification)).

For everyone, one notification each (recipient `all`, a single row, not one per user): a user's bell shows those newer than their account (library's `GET /internal/accounts/{id}`, kept an hour), read and seen like their own, and announced live to every open tab.

- **News:** a published news post ("News: <title>", opening it on the news page). The bell names it in the user's language (library's `POST /internal/news/titles`), in English until it's translated; a post deleted meanwhile isn't shown. Library saves the notification with the post in its outbox, and deleting the post sends `news.deleted`, which removes it. News has no email setting: the bell isn't email. A post can still be emailed by hand as a product update (see [Campaigns](#campaigns)).
- **Legal changes:** when a notice of new terms or a new privacy policy is sent ("New terms apply from <date>", opening the document). The DPA's notice goes to each company owner's and admin's own bell instead.

A member who accepts their team invite is announced to the owner, who invited them: "{email} joined “{company}” as a viewer" (or an admin), opening the company's Team tab. It's saved with the join itself, once per member, and isn't posted to Slack or in the digest.

## Slack

A company can send its notifications to one Slack channel too, from its integrations tab (Messaging, above the ATSs).

- An owner or admin clicks "Add to Slack", allows prepza in Slack and picks the channel. Back on the company's Slack page, they choose which notifications go there. Each "Add to Slack" link works once, for 15 minutes, and only while whoever clicked it is still an owner or admin. By default: finished candidates, ATS candidates that weren't invited, undelivered invites and failed automatic top-ups; ready interviews and charged top-ups can be added.
- prepza gets only an incoming web hook for that channel (the `incoming-webhook` scope): it can post there and can't read anything.
- Each notification is posted once, in English, with a link back to prepza: a finished candidate, or an invite that wasn't delivered, opens the candidate's page; an ATS candidate who wasn't invited opens that ATS's page, where they're retried; the rest open their notification's page. What people wrote (titles, emails) shows as typed: a title like `<!channel>` doesn't ping anyone. Every notification is posted, also one the bell groups with others (see [Grouping](#grouping)); a redelivered event doesn't post again.
- A message is a plain-text block, which Slack doesn't format, with an **Open in prepza** button (`helpers/slack.py`). What people wrote (a title, a candidate's name from an ATS) can't ping anyone (`<`, `>` and `&` are escaped), become a link (a dot inside a word gets an invisible zero-width space, so `www.evil-login.com` or an email isn't linked) or change the formatting.
- The bell gets the notification first, whatever happens in Slack. If Slack is busy or down (rate limited, a server error, a timeout), the event is retried with Pub/Sub's backoff and the retry posts the message; the bell doesn't get it twice.
- If Slack says the web hook is gone (the app was removed or the channel deleted), the page shows "Reconnect". A message Slack refuses for good is logged and skipped.
- Disconnecting, or deleting the company, removes the channel from prepza, and prepza's app from the workspace unless another company still posts there. Reconnecting to the same workspace keeps the app; reconnecting to another workspace removes it from the earlier one (again, unless another company uses it).
- Members who can't edit see the channel and its notifications without changing them.
- The channel works while whoever connected it is still an owner or admin; once they're removed or made a viewer, it's marked for reconnecting by a current editor. If they delete their prepza account, the channel stays without their id (`deleted-user`), marked for reconnecting; their data export lists the channels they connected. Each time a channel stops working, the company gets a `connection_broken` notification in the bell (not in Slack, which is what broke).

### Setting up Slack

1. At api.slack.com/apps, create an app "From a manifest" with:
   ```yaml
   display_information:
     name: prepza
     description: Hiring notifications from prepza
   features:
     bot_user:
       display_name: prepza
       always_online: false
   oauth_config:
     redirect_urls:
       - https://<your domain>/api/notifications/slack/callback
     scopes:
       bot:
         - incoming-webhook
   settings:
     org_deploy_enabled: false
     socket_mode_enabled: false
     token_rotation_enabled: false
   ```
   Slack asks for the bot user: bot scopes, `incoming-webhook` among them, need one. A publicly distributed app takes only `https` redirect URLs, so local development uses a second app, "prepza (dev)", made from the same manifest with only `http://localhost:8090/api/notifications/slack/callback`, not distributed: it works in your own workspace, and its keys go in the local `.env`.
2. Under **Manage Distribution**, tick that the app has no hard-coded tokens or web hooks (prepza gets each company's through OAuth) and activate public distribution, so other companies' workspaces can add it.
3. Put its **Client ID** and **Client Secret** (Basic Information) in `.env` as `SLACK_CLIENT_ID` and `SLACK_CLIENT_SECRET`.
4. Set `SLACK_ENCRYPTION_KEY`, the Fernet key that encrypts the web hooks:
   ```bash
   python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
   ```
   Keep it: a new key makes every company reconnect. To replace it, list the new key and the old one, comma-separated, new first (see [infra/README.md](../../infra/README.md), step 8).
5. Restart notifications.

Until all three are set, "Add to Slack" answers "Slack isn't set up yet" and nothing is posted.

### Erased candidates

When a company erases a candidate (`candidate.removed` from companies), its notifications about them (their email and grade) go. When a candidate deletes their prepza account, every company's notifications about them go too (matched by their email when it's verified).

### Grouping

Bursts are grouped. Another finished candidate, undelivered invite, flagged or fixed question, or ATS candidate who couldn't be invited, about the same page and title (for example the same interview) within 24 hours, adds to the last notification ("3 candidates finished …") instead of making a new one.

## Emails

The service sends, as HTML with a plain-text version:

- candidate invites,
- candidates' reminders,
- to a candidate who started through a shareable link, their own invite link to continue,
- team invites: the owner's invite to join the company as an admin or a viewer, with the join link, the role named in the email's language (see [Companies](companies.md)),
- emailed reports, with the PDF attached, in the language of the member who sends them (the test's when theirs isn't known); the PDF is named in that language, its heading and then the candidate or the test, without characters that break a file name (`helpers/attachments.py`),
- contact page messages, to `CONTACT_EMAIL` (hello@prepza.ai by default),
- to company members: the activity digest, reminders, and failed automatic top-ups (see [Emails to company members](#emails-to-company-members)).

Invites and reminders from a company prepza hasn't verified say so in a small line at the bottom. Every invite and reminder names its interview: an interview without its title (its questions not made yet) takes no invite (409), and its reminders wait for the title. The bell and Slack name an interview without a title in words, without empty quotes, in every language.

`SITE_URL` is the site address that links in emails point to; emails link only there (no shorteners or tracking redirects).

- **Three senders:** service emails come from `MAIL_FROM`, and the emails a user may turn off (the digest, reminders and campaigns) from `MAIL_FROM_UPDATES`, on a subdomain of its own, so spam complaints about them can't hurt the service emails' reputation. Candidates' emails (invites, reminders, a shareable link's own link), sent for many companies to addresses they supply, come from `MAIL_FROM_CANDIDATES` so they can be watched apart; while it's empty (today), from `MAIL_FROM`. The DNS records both need are in [infra/README.md](../../infra/README.md#email-deliverability).
- **Replies** go to the member who shared a report (when their email is verified), to the visitor for contact messages, and otherwise to `CONTACT_EMAIL`, prepza's inbox, rather than to an unread no-reply address.
- **Pacing:** every request to Resend, from an event, a scheduled run or a bulk send on any instance, takes a turn in one per-second count in Redis (`prepza_common.http.pacing`, 8 a second, `RESEND_PER_SECOND`), so a burst of invites or two runs at once stay under Resend's 10 a second a team; with Redis down, sending goes on unpaced and a 429 is retried as usual.
- **Headers:** every email has `Auto-Submitted: auto-generated` (no out-of-office replies); only those the recipient may stop carry the one-click unsubscribe headers (see [Unsubscribing](#unsubscribing)).

### Emails to company members

All three follow the invites' layout, with a plain-text version, in the member's interface language (their sign-in's language, from library). What they list links into the app.

- **Activity digest** (optional, `digest`): one email a day per person, covering every company they're a member of (any role). It lists what reached the companies' bells in the 24 hours before 7:00 UTC that day (the same for the catch-up hour's runs), only of the kinds the person gets, grouped by company: candidates who finished and undelivered invites, each with its count and interview; candidates not invited, with their count, one line per ATS they came from; interviews ready. Nothing happened, or every kind is off: no email. It shows counts and titles only, no candidate's address or grade. Its "Unsubscribe" stops the whole digest; "Change your email settings" chooses kinds.
- **Reminders** (optional, the one `reminders` setting), to owners and admins, each kind at most once in 7 days to a person:
  - credits running low: companies whose available credits can't pay for another candidate and that no automatic top-up refills (billing decides), again each week while that lasts,
  - waiting for candidates: an interview nobody was invited to, 3 days after it got its questions (not one marked hired); each interview once, and none ready more than 10 days ago,
  - topics waiting for review: to whoever started the interview, while they're still an owner or admin, once its topics have waited a day; each interview once. Generation cancels a review after 14 days, which the email says.
- **Automatic top-up failed** (a service email, always sent): at once to the company's owners and admins, with the bell's notification. No unsubscribe link; its footer says it's about the company's billing, so it's sent whatever their email settings. A retried event doesn't send it twice (Resend's key is the event and the person).

The digest and reminders are sent by `notifications` on a schedule: `POST /internal/schedules/digest` every minute from 7:00 to 7:59 UTC and `/internal/schedules/reminders` from 8:00 to 8:59, each again for a catch-up hour three hours later (10:00 and 11:00) that sends what the first hour missed, such as while Resend was down (`infra/terraform/jobs.tf`, `scripts/local/crontab`). The digest works through the companies with activity a page of 100 at a time (`services/member_pages.py`): the page's members, every other company of theirs (companies' `GET /internal/users/{id}/companies`), and those companies' names, members and activity, so a member's one digest covers all their companies whichever page found them; addresses, languages and settings come from library. A page's digests go out before the next page is read, and where the day's runs have got to is kept in Redis (`member_emails:after:<job>:<day>`, for two days), so each run goes on after the last page a run finished; a page cut short by the deadline is done again by the next run, whose claims skip who got theirs. Reminders go the same way, a page of 100 companies at a time: the companies running low on credits (billing) and those with waiting interviews (companies' `GET /internal/interviews/waiting/companies`, a page after the last company id), in order, never past the end of a full page of waiting companies; then the page's owners and admins, every other company of theirs, and those companies' waiting interviews (`POST /internal/interviews/waiting`), review statuses (generation), addresses, languages and settings (library), so a person's reminder covers all their companies whichever page found them. A run sends for at most 40 seconds, one email every 0.6 seconds to stay under Resend's per-second limit; the next run goes on with the rest. That's about 4,000 of each a day; when an hour's last run still leaves some unsent, it logs an error (Sentry), as sending is too slow for its hour; the catch-up hour sends the rest, and only what it misses too waits for the next day.

- **Never twice:** each email is claimed in a sent log (`sent_emails`: the person, the kind, the day or what a reminder named) under a per-person lock and a unique constraint, so a re-run or two runs at once send it once. A send that fails gives its claim back for the next run; Resend's idempotency key (the person, the kind and the email's content) keeps a send that failed but went through from going out again.
- **Resend busy** (429): the run gives back its claim and stops; the next run sends the rest. Any other failure fails the run (and the scheduler's alert) after giving the claim back.
- The log keeps 30 days: the reminders' runs delete older rows (and soft bounces past their 14 days) in batches, none started later than 50 seconds after the run began, and the next run deletes the rest; deleting an account removes the person's rows.

### Email preferences and consent

Each user chooses, in Settings > Emails, which emails they get beyond service emails (invites, reports, billing problems, legal changes), which always go out. `library` stores the choices (`/library/me/email-preferences`; other services read them at `/internal/users/{id}/email-preferences`):

- the activity digest, one setting per kind: a candidate finished, an invite wasn't delivered, an ATS candidate wasn't invited, an interview is ready; on by default, with one checkbox in Settings that turns all four on or off,
- reminders (low credits, an interview with no candidates, topics waiting for review); on by default,
- product updates and news: a soft opt-in for prepza's own users. The sign-in dialog offers an unticked "Don't send me product updates and news"; a first sign-in without it ticked turns updates on, with it ticked leaves them off. A later sign-in never turns them back on, and users who haven't signed in since (no stored preferences) have them off,
- offers and promotions: off until the user ticks them, in Settings or on the sign-in dialog. Signing in only turns them on: an unticked box there changes nothing.

The sign-in dialog shows both checkboxes only on a browser where no one has signed in yet (a `prepza:signed-in-before` flag in local storage, set at every sign-in): an existing account's choices are in its Settings.

Every change is logged and never edited (`email_consents`): the setting, on or off, where (`sign_in`, `settings`, `unsubscribe`, or `admin` with the superadmin's id in `changed_by`), on what basis (`choice`, or `soft_opt_in` for updates turned on at a first sign-in that showed the opt-out), the wording's version (`CONSENT_TEXT_VERSION` in `services/library/src/library/constants/emails.py`, changed whenever the checkboxes' wording changes) and the time. The account export includes both; deleting the account removes them.

### Unsubscribing

Emails carry signed unsubscribe links (`EMAIL_LINK_SECRET`, an HMAC-SHA256; `services/notifications/src/notifications/helpers/unsubscribe.py`). A link names what it stops and whom, never expires, and can't be made for anyone else:

- optional emails to a prepza user (the activity digest or one of its kinds, reminders, updates, offers) name the user and the email; they show "Unsubscribe" and "Change your email settings" (Settings) under the footer, and carry the one-click headers (`List-Unsubscribe`, `List-Unsubscribe-Post: List-Unsubscribe=One-Click`) that mail clients show as their own unsubscribe button. `optional_email` in `services/notifications/src/notifications/helpers/emails.py` builds such an email from a template and the type,
- a candidate's invite, and the link sent to someone who started through a shareable link, link to "Don't email me for <company>", and their one-click headers stop the company's emails; a reminder links to that and to "Don't send me reminders for this interview", and its one-click headers stop that interview's reminders. These links name the candidate's address as its keyed hash (HMAC with `PERSON_HASH_KEY`, `prepza_common.auth.person_hash`; links end up in request logs), the company, and for reminders the invite. Opt-outs keep the same keyed hash; a link sent before the hashes were keyed carries the plain SHA-256, keyed when it's used.

A link opens `/unsubscribe?token=…` (no sign-in, not indexed): it says what stops ("You won't get the activity digest anymore", "You won't get reminders for this interview anymore", "You won't get emails from Acme anymore") and changes nothing until "Confirm", since mail scanners open links. Then it says "You're unsubscribed", with "Email settings" for a signed-in user. The page reads the link at `GET /api/notifications/unsubscribe/{token}` and confirms with a `POST` there; mail clients' one-click `POST` (body `List-Unsubscribe=One-Click`) goes to the same address and needs nothing more. Repeating either changes nothing.

- A user's link turns the setting (or the digest's four kinds) off in `library`, logged with the source `unsubscribe`. Marking the digest or reminders as spam does the same: those emails are tagged with the user and what they are, and Resend's `email.complained` webhook (see [Undelivered emails](#undelivered-emails)) turns that email off as its link would.
- A candidate's link is kept in notifications (`candidate_opt_outs`, by the address's hash). An invite to an address that stopped the company's emails isn't sent, and the company sees it as undelivered, as with a bounce. A reminder isn't sent when the address stopped the company's emails or that interview's reminders; the company isn't told. Marking a reminder as spam stops that invite's reminders as its link would: reminders are tagged with the invite and the company (`candidate_reminder`), and Resend's `email.complained` adds the opt-out. An opt-out stays when the company erases the candidate, and goes with the company.

Someone who asks by email instead: a superadmin turns their settings off, or stops or resumes a company's emails to their address, on the admin zone's [Support](admin-support.md#emails) tab (an account's page, or a candidate's). Companies' invites tell which companies invited the address (`POST /internal/invites/companies`, the address in the body).

Changing `EMAIL_LINK_SECRET` breaks the links in emails already sent; opt-outs already made stay.

### Sending real emails

Without `RESEND_API_KEY`, emails go to `SMTP_HOST` and `SMTP_PORT`: Mailpit locally (http://localhost:8125). To send real emails through [Resend](https://resend.com):

1. Verify your domain at resend.com/domains.
2. In `.env`, set `RESEND_API_KEY` (with full access: a sending-only key sends, but can't take an address off Resend's suppression list), `MAIL_FROM` with an address on that domain, for example `prepza. <no-reply@yourdomain.com>`, and `MAIL_FROM_UPDATES` with one on a subdomain verified too, for example `prepza. <updates@mail.yourdomain.com>`. Keep click and open tracking off for both domains in Resend.
3. Restart the service: it reads `.env` only when it starts.

With `RESEND_API_KEY` set, a message sent from the local contact page reaches the real `CONTACT_EMAIL` inbox.

### Emails to many users

Legal notices and campaigns go through one bulk sender (`services/bulk.py`); who a send goes to is worked out by `services/audiences.py`:

- **Recipients are worked out a page at a time** (5,000 ids, `prepza_common.db.paging`) and saved (`bulk_sends`, one row a send; `bulk_recipients`, one row per user, unique per send): the first page when a send starts, the rest by the runs, each going on after the last id saved (`bulk_sends.prepared_after`) until its time is up. The send's row is locked while a page is saved, and a page another run saved already is left alone, so two runs at once save each user once. Each run then takes the next pending rows rather than reading every account again; addresses, languages and settings are read 100 at a time just before sending, so a changed address or a deleted account counts. Guest candidates are never recipients.
- **Schedule:** `POST /internal/schedules/bulk` every minute from 8:00 to 18:59 UTC (`infra/terraform/jobs.tf`, `scripts/local/crontab`). A run sends for 40 seconds, one email every 0.6 seconds, about 2,400 an hour, so a large send finishes the same day.
- **Never twice:** a row is claimed under a lock (`FOR UPDATE SKIP LOCKED`), so two runs at once never send the same one; Resend's idempotency key is `bulk/<send>/<user>`. A run that dies halfway leaves its row pending, and the next run sends it under the same key.
- **Failures:** a failed send is tried again in two later runs, then marked `failed` with the reason; one Resend refuses for good fails at once. A 429 from Resend stops the run, and the next one goes on.
- **Daily quota:** bulk emails stop for the day at Resend's daily quota (`RESEND_DAILY_LIMIT`) less the share kept for invites and other service emails (`RESEND_RESERVE_PERCENT`, 20% by default; both editable in the admin zone's Controls); the rest go the next day, and the limit hit is recorded.
- **Skipped,** with the reason: an account or address that's gone (`gone`), an address on the suppression list (`suppressed`), a product update's or offer's setting turned off since it started (`unsubscribed`; never for an important notice), a stopped or deleted campaign (`stopped`).
- A send is finished once nothing is pending. Deleting an account removes its rows.

#### Legal notices

A notice of a significant change to the terms, the privacy policy or the DPA, asked for in the admin zone (see [Legal notices](admin-zone.md#legal-notices)). It's a service email, sent whatever the email settings, in each recipient's language: the terms and privacy notices to every account (library's `GET /internal/users/ids`), the DPA's to every company's joined owners and admins (companies' `GET /internal/companies/member-ids?editors_only=true`). It says the day the new version applies, written as the recipient's language writes dates (8 November 2026, 8. November 2026), and links to it. Counts in the digest and reminders are formatted for the language too (1,234 or 1.234). Asking twice, or two superadmins at once, starts it once. It also goes in the bell (see [The bell](#the-bell)).

Until the new version applies, the site shows a thin banner above the page to whom it concerns (`GET /me/legal-changes`: the terms and the privacy policy to everyone, the DPA to those it was sent to), with a link to it. Closing it keeps it closed in that browser for that version.

#### Campaigns

Product updates, offers and important notices, written by a superadmin in the admin zone (see [Campaigns](admin-zone.md#campaigns)) and sent at once, without scheduling:

- **Kinds:** a product update (`updates`) and an offer (`promotions`) are optional emails, reaching only users with that setting on (checked again when each email goes out; promotions never reach soft opt-in users, as their setting stays off until they tick it). An **important notice** (`notices`) is a service email about prepza itself (a security incident, a vulnerability needing action, a breach notification, planned downtime, a change to how it works): it goes whatever the email settings and can't be unsubscribed from, but never to a suppressed address or a deleted account, and never carries promotion.
- **Audience** (every kind): everyone, or any of these groups, someone in several getting one email (`bulk_recipients` is unique per send and user):
  - **Companies:** everyone who joined a company's team (companies' `GET /internal/companies/member-ids`), or with "owners and admins only" its owners and admins; for an important notice, optionally only some companies (up to 50, `MAX_NOTICE_COMPANIES`; their members from `POST /internal/companies/members`), for an incident that affects them.
  - **Candidates:** accounts that took a company's interview, from rounds' interview sessions (a member's own try, a preview, doesn't count; guest candidates never); rounds' `GET /internal/users/ids?group=candidates`.
  - **Learners:** accounts that took a free practice round, from rounds' practice sessions (`?group=learners`).
  - Only account ids cross between services; for a product update or an offer to some groups, library keeps those with the setting on (`POST /internal/users/with-setting`). "Everyone" is every account for a notice (library's `GET /internal/users/ids`) and the users with the setting on for the others (`?setting=`).
  - Each group is read a page at a time, one after the other; the send's cursor names the group and its last id (`<group>:<id>`). The dialog's count (`POST /superadmin/campaigns/recipients`) reads the same pages, then who has an address and isn't suppressed (and, for an optional kind, the setting on).
- **The email:** a product update or an offer is an optional email from `MAIL_FROM_UPDATES` with the unsubscribe link and one-click headers of that one setting; an important notice comes from `MAIL_FROM`, with no unsubscribe link or `List-Unsubscribe`, and its footer says it's sent whatever the email settings as an important notice about the service. Each is in the user's language (English until translated). The text is Markdown (bold, italic, links, lists), rendered with inline styles; raw HTML stays text and unsafe links (`javascript:`) aren't links (`helpers/markdown.py`). The button opens a page on the site, or the site.
- **Day limits:** at most `CAMPAIGNS_PER_KIND_DAY` product updates and as many offers a day (UTC; 1 by default), and at most `NOTICES_PER_DAY` important notices (1 by default, at most 3), both editable in the admin zone's Controls: the kind is locked while one is marked sent, so a double click or two superadmins at once can't pass the limit. A campaign whose kind changed between its checks and being marked sent is refused (409, "This campaign's kind was changed meanwhile. Check it and send it again.").
- **Guarding notices:** an important notice is sent only with the superadmin's confirmation that it's about the service itself, not a promotion (`{"acknowledged": true}`; otherwise 422, "Confirm that this notice is about the service itself, not a promotion, before sending it."). Who sent each campaign, its kind and its groups are logged (a warning, "Superadmin … sent campaign … (notices, to members)") and kept on its send (`bulk_sends.asked_by`).
- **Counts:** sent, skipped, failed, unsubscribed after it (the user's last campaign of that kind) and spam complaints (Resend's tag carries the send's id).
- **Translation:** saving the English asks generation to translate it into the other 22 languages (a `translate-campaign` job); a changed English drops the old translations, and a translation that arrives for an English changed meanwhile is dropped. A language edited by hand keeps its wording.

#### The suppression list

Resend's `email.bounced`, `email.complained` and `email.suppressed` (Resend's own list holds the address after an earlier bounce or complaint) for any email, a candidate's invite included (an address that bounced or complained does so whichever company writes), put the address on prepza's own suppression list (`suppressed_addresses`), kept as its keyed hash with the reason and the date, never in the clear. Only a permanent bounce (Resend's `bounce.type` `Permanent`) suppresses at once; a temporary one (a full mailbox, a server down) is counted (`soft_bounces`, once per email, kept 14 days), and the third within 14 days suppresses the address too (`soft_bounced`). Nothing is sent to those addresses: bulk sends skip them (`suppressed`), and every other email checks the list before it goes (`services/delivery.py`), except the contact page's messages to prepza's own inbox. A candidate's invite or reminder skipped so shows as undelivered, as with a bounce; any other email is logged. A complaint also turns that email's setting off, as before. A superadmin sees it, and takes it off the list, on the account's support page: off Resend's own suppression list first (`DELETE /suppressions/{address}`; one not on it is fine), then off prepza's. When Resend keeps it, the address stays on both, the request answers 502 and the page says the action failed, to try again.

### Failed sends

- A failed send answers Pub/Sub's push with an error, so Pub/Sub retries it.
- Over Resend's per-second limit (a burst of invites) or its daily or monthly quota, it answers 429 instead: Pub/Sub retries with backoff, and it doesn't count as a server error in the alerts. Each is recorded as a limit hit of Resend's: its rate limit, or its quota (`RESEND_DAILY_QUOTA`, the daily and the monthly one alike).
- A key Resend already sent with, whose email changed since (409 `invalid_idempotent_request`: a retry after the recipient's language changed, say), counts as sent and is logged, never retried; the same key still being sent by another try (409 `concurrent_idempotent_requests`) is retried like a 429. The same holds for the scheduled and bulk sends: the row stays sent, its claim kept.
- After the subscription's maximum attempts, Pub/Sub moves it to the dead-letter topic.
- The error from Resend is in the logs.
- Retries never send an email twice.

### Undelivered emails

To show invites whose email bounced, was marked as spam or couldn't be sent ("Email not delivered" in the candidate list), to turn off an optional email for a user who marked it as spam, and to keep the suppression list:

1. Add a webhook at resend.com/webhooks pointing at `https://<your domain>/api/notifications/webhooks/resend`, with the events `email.bounced`, `email.complained`, `email.suppressed` and `email.failed` (an email Resend couldn't send at all, its quota used up, say: the invite shows as undelivered, and the address isn't suppressed). `email.delivery_delayed` isn't needed: a delay is temporary.
2. Put its signing secret (`whsec_...`) in `.env` as `RESEND_WEBHOOK_SECRET`.
3. Restart notifications.

Without the secret, every webhook is refused. A webhook is answered once its signature is checked and it's recorded as an `email.webhook_received` event, keyed by its delivery (`svix-id`), so Resend sending it again records it once; its work (the suppression list, telling companies and library) runs when Pub/Sub pushes that event back, retried there, and every step is safe to repeat. The event keeps only what the work reads (`to`, `tags`, `email_id`, `bounce`), for the outbox's 7 days. Locally, Resend reaches the webhook only through a tunnel, as with Paddle (see [Credits and payments](billing.md#setting-up-paddle)).

## How it's built

Notifications' routes and event handlers call services (`src/notifications/services/`), which open each transaction and pass it to the repositories; Resend, Slack, Redis and the other services are called outside it, so no email or post waits inside a transaction. A notification is stored in one save: the recipient's lock, the check that it isn't a deleted company, the mark that its key came, the new row or its group's, and the pruning of the recipient's oldest. When an account is deleted, its notifications, its sent log, its rows in bulk sends, companies' notifications about it and the Slack channels it connected are one save, and each company whose channel stopped working is told after it; a deleted company's notifications and its candidates' opt-outs are one save, then its Slack channel goes. A complaint's suppressed addresses and the complaint counted against its campaign are one save, a temporary bounce is counted with the suppression it brings, and a reminder's complaint stops the invite's reminders to all its addresses at once. A campaign is marked sent with its bulk send in one save. Claims around a send stay apart from it: a member email's claim is given back when the send fails, a Slack post's mark is freed when Slack fails, and a bulk recipient's outcome is saved after its email went.
