# Candidates

How candidates get to an interview, how they take it, and what the company sees afterwards.

- [Invites](#invites)
- [Revoking a candidate](#revoking-a-candidate)
- [Candidate names](#candidate-names)
- [Shareable link](#shareable-link)
- [Taking an interview](#taking-an-interview)
- [Timing](#timing)
- [Scorecards](#scorecards)
- [The candidate list](#the-candidate-list)
- [Reports](#reports)
- [Email limits](#email-limits)
- [Retention](#retention)

## Invites

Owners and admins invite candidates by email, in the "New candidate(s)" dialog's three tabs (the last one used is remembered in the browser):

- **one:** an email and an optional name,
- **many:** a pasted list, one candidate per line (or several separated by commas or semicolons), with or without names (`Name <email>` or `email, Name`),
- **upload:** a CSV or TXT file (at most 50 KB; another type, or a file that isn't text, is refused); the tab has buttons that download example files (`frontend/public/examples/prepza-candidates-example.csv` and `prepza-candidates-example.txt`).

Each line nobody can be invited from is named under the list with its one reason: no email found, an email that isn't valid, or a name not written as `Name <email>` (the first 10, then how many more). After inviting, the list keeps only those lines and the emails that weren't invited. The service reads the list and decides (`helpers/candidate_lists.py`, `helpers/list_files.py` in companies).

A list or file takes up to `MAX_BULK_INVITES` emails at once (100 by default; the tab's hint reads the current value from companies' `GET /companies/limits`), and only the emails in it count, with the names written with them (see [Candidate names](#candidate-names)). A list skips candidates who already started, so they aren't emailed again.

An invite can be resent until the candidate finishes, or revoked (see [Revoking a candidate](#revoking-a-candidate)). Inviting an address whose invite is still open sends it again and answers `200` (nothing new is made, as in the API); a new invite, or an expired one brought back, answers `201`. Inviting a candidate who finished again is refused (409), so they aren't emailed for nothing; through an ATS or the API they are returned as they are, with no email. The service tells the page what each candidate allows (`can_resend`, `revokable`), and the page only shows it. The invite page tells candidates what to expect before they start: the company's logo above who invited them, the interview's title, the time per question (with any extra time they were given) and the whole interview's time in minutes, rounded up (the questions a candidate gets from each topic, times their seconds a question; companies works it out as `total_minutes` and leaves it out until the questions are known), and the start button, under the candidate's pledge to answer on their own, without AI tools or other people: a checkbox that enables the start (see [The pledge](#the-pledge)). Beside them, on a computer, the rules run the screen's full height in a square-cornered card that scrolls inside when they don't fit; on a phone they come first, out to the screen's edges, with the start button after them. The shareable link's page and a member's preview look the same. A visitor who isn't signed in sees the invitation (the company, the interview and its rules, but not the invited email) with a **Sign in to start** button. Signed in with another email, the page explains in a warning that only the invited email can start; once the interview is finished, it says so in an info card. A candidate a company's own platform sent through the API without a sign-in starts straight away: the link signs them in as that invite's guest ([API](api.md)). A small gray line says when prepza hasn't verified the company, and a suspended company's invites are invalid until a candidate has started (see [Suspension](companies.md#suspension)).

Until the candidate finishes, owners and admins see the invite link on the candidate's page, in a card with a copy button, to send it themselves if the email didn't arrive or got lost. An expired invite has none (sending it again revives it), and viewers don't see it.

A candidate's credits are set aside on invite and given back if they never answer (see [Credits and payments](billing.md)).

### Reminders and expiry

| When | What happens |
|---|---|
| Not started after 3 days | One reminder email. A daily job runs it (`/internal/schedules/invite-reminders`) |
| Not started within 30 days | The invite expires and its credits come back; its link says it expired and to ask the company to send it again (`410`, `INVITE_EXPIRED`). Sending it again, or the candidate starting through the shareable link, sets them aside again |

Candidates can also arrive from an ATS (see [ATS integrations](ats.md)).

## Revoking a candidate

Owners and admins can revoke any candidate in the list (`DELETE /interviews/{id}/candidates/{invite_id}` in companies):

- **Not started yet:** the invite is withdrawn; its link stops working and the credits set aside come back. The candidate can be invited again later.
- **Started or finished:** the candidate is erased for good, with their answers, timings and results in rounds, for example when they ask to have their data deleted. Results that arrive after the erasure (a section finishing at that moment) are dropped, with no notification or event. A candidate who picked an answer to at least one question (one whose time ran out doesn't count) is charged (a finished one stays charged); other credits still held come back.

Either way the company's [action log](companies.md#action-log) records it, and companies publishes `candidate.removed`: the company's bell notifications about the candidate go, and so does the ATS's record of them for that interview.

## Candidate names

Each candidate may have a name (`name`, null while unknown; the app shows "No name yet"). It's untrusted text: trimmed, cut to 200 characters (`MAX_CANDIDATE_NAME_LENGTH` in prepza_common) and shown only as text.

Where it comes from, first one wins (each fills only a name not known yet):

- **The inviter:** the invite dialog's optional name field (for one email), a list's `Name <email>` or `email, Name` lines, or a CSV file whose header has a name column (`name`, `full name`, or a first and a last name, in English or the 23 languages: `constants/name_headers.py` in companies). The list is read on the backend (`helpers/candidate_lists.py`). The public API's invite takes an optional `name`.
- **The ATS:** the name the ATS sends with the candidate (Workable's and Recruitee's and Breezy HR's `name`, Greenhouse's `first_name` and `last_name`, Teamtailor's `first-name` and `last-name`), kept on the ATS candidate and passed with the invite.
- **The sign-in:** when a candidate starts, through an invite or the shareable link, the name claim of their verified sign-in (Google, LinkedIn or GitHub). A name sent in the request is never used.

Inviting the same address again (a list pasted again, an ATS event delivered twice) keeps a known name. Owners and admins correct it on the candidate's page, under the email, like a title (`PATCH /interviews/{id}/candidates/{invite_id}/name` in companies), for example when the sign-in gave a nickname; a blank name makes it unknown again. Viewers see it read-only.

**Where it shows:** under the email in the candidate list and on the candidate's page; in the candidate's and the test's PDF reports, the shared summaries, a report's email ("Name (email)"), and the bell's and Slack's notifications about the candidate; as `name` in the candidate APIs and the public API. Searching candidates matches part of the email or the name, in any case.

**Personal data:** it is kept and deleted with the invite (revoking or deleting the candidate, retention, the interview or the company going), with the ATS's record of the candidate, and with the notifications about them. A deleted interview's or company's invites go a batch at a time, each batch its own transaction (with the company: its action log and interviews too, then the company), so a deletion cut off midway goes on when it's run again. When the candidate deletes their account, every invite they were sent or started is deleted, as if each company had deleted the candidate (`candidate.removed` tells the other services; a row kept without the email would still point to them by its times and grade, so none is kept), and their data export lists them until then. Rows an earlier version left blanked go with the daily `candidate-removals` job. Invites are matched to an account by its email only when that email is verified (`app/helpers/accounts.py` in library), so a sign-in that merely claims an address can't erase or download them.

## Shareable link

The shareable link (`/apply/{token}`) is one link per interview, for a job ad. Owners and admins turn it on, once the interview has its questions (as for an invite, and not during the emergency pause); a link turned on earlier holds no credits until they're made.

- Anyone who opens it signs in and takes the interview.
- Each verified email can take it once.
- It is charged like an invited candidate.
- On their first start, they're emailed their own invite link (`/invite/{token}`), to continue if they leave: companies saves `candidate.joined` with the new invite, once, and notifications sends it (not to an address that stopped the company's emails). The page says so.
- Turning it off, or marking the interview as hired, stops it at once for new candidates; those who started continue from their own link.
- Extra time can't be given to them, as their invite is made when they start: the page tells them to ask the company for a personal invite before they start.
- A new candidate shows they're a person first ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)).
- It takes at most 30 new candidates an hour, and one address starts at most 10 an hour across all links (`LINK_STARTS_PER_HOUR`, `LINK_STARTS_PER_IP_HOUR`, their defaults), so a script with many accounts can't use up a company's credits; over either, a 429. A candidate already invited is never held back by them.

## Taking an interview

- Only the invited email, verified, can start; for a shareable link, any verified email. A sign-in that doesn't verify the email (GitHub) is told to confirm it first, with the link sent when they signed in, not that the invite was for another address. When Firebase couldn't send that link, the sign-in says so, and signing in again sends a new one. Starting reads the account again, so an email confirmed meanwhile (in another tab) counts without signing in again.
- Each candidate gets a random subset of each topic, with their own question order and option order.
- The interview is a single pass.
- A candidate can change their pick until they press Next question, finish the interview, or the question's time runs out. The pick is sent then, and it's final. On a "select all that apply" question they tick every option they think is right, and the ticks are sent the same way (see [Interviews](interviews.md#questions) for how it's scored).
- Unanswered questions count as wrong.
- Candidates never see their scores or whether an answer was right.

The backend decides which section and question come next, and when the interview is done: `POST /sessions/{id}/step` and `/finish-interview` in rounds (`app/routers/interview_flow.py`).

Questions and options carry the interview's language (`lang`), so screen readers read them in it whatever the interface language.

### The pledge

Before a first start, a candidate ticks that they'll answer on their own, without AI tools or other people; the start button works once it's ticked. The start request carries it (`pledged: true` on `POST /invites/{token}/start`, `POST /links/{token}/start` and a member's `POST /interviews/{id}/preview`), and companies refuses a first start without it (422, `NO_PLEDGE`), so no other client can skip it; a candidate already in the interview continues without it. Companies stores when it was given on the invite (`pledged_at`, from the first start; candidates from before migration 0051 have none), and the candidate's page shows it as a small line under the grade (the scorecard's `pledged_at`). It goes with the invite: retention, erasure and the candidate's data export (`pledged_at` in `interview_invites`). A candidate sent from a company's own platform ticks it inside the embedded page; the API asks nothing of the company. Practice rounds don't ask for it: no one assesses them.

## Timing

Every interview is timed. Each question has its own countdown.

- By the test's level: 60 seconds for a basic or medium test, 75 for a hard one, by default (values in the admin zone's Controls); adjustable per interview on its settings tab.
- The countdown turns red for the last 10 seconds, or for the last third of a shorter question.
- At zero, the pick on screen counts. If nothing is picked, the question counts as wrong.
- An answer can't be changed. The same pick sent again (its reply lost on the way) is answered as before, even after it finished the section, so the candidate isn't told it failed.

While the questions run, the page shows only them: no header, footer or "ask agent", nothing to leave the page through by accident (a page leave is recorded, and the clock keeps running). The same goes for practice rounds and a company's preview. A company's interview keeps them away for good: its invitation, its shared test link and its finished page show the company only, never prepza's header or footer. A practice round's results have them again.

### Extra time

For a candidate who needs more time, for example because of a disability, owners and admins can give extra time on each question: +25%, +50% or +100% (`PUT /interviews/{id}/candidates/{invite_id}/extra-time` in companies). It is set per candidate, on their page, and only before they start: their questions' time is fixed then. No reason is recorded, and the company's [action log](companies.md#action-log) records the change. The invite page tells candidates to ask the company before they start; the shareable link's page, to ask for a personal invite.

The server enforces the clock:

- Closing the tab doesn't stop it.
- It accepts an answer up to 5 seconds after the deadline (`TIME_GRACE_SECONDS`), for a pick sent as the clock reaches zero. Only the interview's own steps (the next question, an answer, finishing) record a question as timed out; requests on the side (rating or reporting a question, a page leave) never do, so they can't beat a last-second answer to it.
- An interview the candidate leaves finishes by itself once its total time, plus 10%, has passed. Unanswered questions count as wrong.

## Scorecards

A scorecard shows every answer, whether it was right and how long it took; for a "select all that apply" question, the options ticked, which were right, and its points ("2 of 3 right options · 0.67 of 1 point"). It flags:

- answers too fast to have read the question,
- times the candidate left the page,
- copy attempts.

Only a company's interview records page leaves and copies: a talent's practice round and a member's preview record none, as no one assesses them. One session's browser may report a page leave or a copy 60 times a minute (`SIGNALS_PER_MINUTE`; a 429 past that), and a question keeps at most 50 (`MAX_SIGNALS_PER_QUESTION`), by default: one already flags the candidate, so a script can't flood the scorecard.

A page leave is reported when the page loses focus, and how long it lasted when it gets focus back (`tab_return`, stored as the leave's `away_seconds`). Rounds counts a leave only when it lasted at least 2 seconds (`MIN_TAB_LEAVE_SECONDS`), so a notification or a permission prompt taking focus for a moment is kept but not counted; a leave the candidate never came back from counts. Any counted signal flags the candidate, so a company trying an interview itself sees exactly what a candidate's would show. Signals are what the candidate's browser reports: the scorecard and the PDF report say so when there are any (a reason to look closer, not proof), and so does the result comment in the ATS.

## The candidate list

- Sorted by invite date by default: newest first.
- Can be sorted by grade instead: best first, candidates without a grade yet last.
- Can be searched by email or name.
- Can be filtered by status: invited, in process, finished, passed, flagged, not delivered, expired.

Any member, viewers too, can also search a company's candidates across all its interviews by email or name, newest first, a page at a time (`GET /companies/{id}/candidates?q=&offset=&limit=` in companies). Each row is a list row with its interview's id and title; candidates of a deleted interview are gone with it. The app has no page for it.

"Not delivered" means the invite email bounced or was marked as spam (see [Notifications and emails](notifications.md#undelivered-emails)).

Each candidate's grade and integrity flag are stored on their invite when they finish, so the list is sorted, filtered and paged in the database. A finished candidate's results never change: a question fixed later applies only to candidates who start after the fix (see [Question quality](../generation.md#fixes)).

## Reports

A report is a PDF, made in the browser, for one candidate or for all of an interview's candidates. A report can be:

- downloaded,
- emailed from prepza, with the PDF attached (it counts towards the member's email limits); owners and admins send it to any address, viewers only to one of the company's joined members (another address is refused with a 403 that says so),
- shared as a short summary on WhatsApp, Telegram, Viber or LINE (Viber's button opens only where its app is installed).

The home page offers both reports as samples (`frontend/public/samples/prepza-report-samples.zip`, cached for a day), made by the same reports and download buttons from made-up data (`frontend/constants/report-samples-fixture.ts`, company "Acme Hiring (example)"). When the reports' design changes, make them again with the stack running: `./scripts/report-samples.sh` opens the development-only page `/report-samples` (404 in production) in Playwright's Docker image, downloads both PDFs and zips them.

## Email limits

Candidate invites, emailed reports and [team invites](companies.md) count towards the limits of the member who sends them, per user and per recipient; emailed reports also towards their company's. A superadmin can change each in the admin zone's Controls tab ([Admin zone](admin-zone.md#limits)):

| Limit | Name | Default |
|---|---|---|
| Per user, an hour | `EMAIL_HOURLY_LIMIT` | 100 |
| Per user, a day | `EMAIL_DAILY_LIMIT` | 200 |
| Per recipient address, a day (counted per inbox: lowercased and without a `+tag`, so `name+1@` and `name+2@` share one count; the email still goes to the address as typed) | `EMAIL_RECIPIENT_DAILY_LIMIT` | 3 |
| Reports a company emails a day | `REPORT_EMAILS_PER_COMPANY_DAY` | 20 |

An invite counts towards these limits only once the company's credits are set aside for it: an invite refused for lack of credits (an ATS's too) uses up none of them, and one refused over a limit gives back the credits it just set aside.

A company emails a candidate's report only once that candidate has finished the interview.

## Retention

| Data | Kept | Deleted by |
|---|---|---|
| A candidate's invite (email and name), answers, timings, integrity signals and results | 365 days after the invite was last sent | The daily retention job in companies (`/internal/schedules/retention`), with the sessions in rounds and any credits still held |
| A candidate an ATS sent (email and ATS ids), with any results waiting to go back | 365 days | The ats `recover` job (every 10 minutes); see [ATS integrations](ats.md) |

Both go earlier with their interview, their company, or when the company revokes the candidate.

Companies' daily candidate jobs (retention, invite expiry and `candidate-removals`) go a batch at a time and start no batch 100 seconds into a run (`JOB_RUN_SECONDS`), so each ends within the service's 150-second timeout; whatever is left goes in the next run.
