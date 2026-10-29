# What the help chat knows about prepza besides the FAQ, prices, terms and privacy policy that
# come with it. Limits come from the services that enforce them.
PLATFORM_GUIDE = """\
prepza helps companies find out which candidates really know the job: a short, timed \
multiple-choice test made from a job description, for any role, used as a screen before \
interviews or as an interview step itself.

Menus: the header has "hiring" (companies) and "pricing" (on wide screens). The account menu has \
the user's name and email with a small "copy id" button, then Settings and Top up. The site follows the device's light or dark setting until the visitor picks a theme: three buttons \
(system, light, dark) in the header for visitors on wide screens, in the account menu once signed \
in; "system" follows the device's light or dark setting. The footer has three columns. The product: skills tests by role, \
pre-employment testing, AI interviews, free practice and comparisons. Resources: guides, the FAQ, \
the legal docs (documents for companies), the developer docs (the API, web hooks, the SDK, MCP and \
objects) and a news page with prepza's latest updates. The company: an about page (the company \
and its solo founder, Viktor Vilskyi), a contact page with a form (name, email, message) that \
reaches the prepza team, the privacy policy, terms, and an accessibility statement (what works \
for people with disabilities, what falls short, and where to report a problem: \
hello@prepza.ai). Signing in is with Google, LinkedIn or GitHub; taking an interview and \
creating a company need a verified email, so a GitHub sign-in that hasn't verified it gets a \
link to verify it first; if the link never came, signing out and in again sends a new one.

Page guides and the assistant: the app's pages have an info button (a question mark under the \
back arrow) with a short guide to the page: what it's for, what you can do there and tips; \
it ends with a "contact us" button to the contact page, to report a problem, suggest an idea or \
ask for a missing feature. \
"ask Mira" in the header opens Mira, prepza's AI assistant (an AI, not a person), which \
knows the page it's asked on: "What can I \
do on this page?" answers from that page's guide, and "Who's best here?" on an interview's \
candidates means that interview.

Companies:
- The home page starts with the box for a job description; submitting it signs you in if \
needed and asks which company the test is for, or its name for a first company. Companies are \
also under "hiring" (one person can own up to {max_companies}). A company has an owner and \
members: on its Team tab the owner invites each one as an admin or a viewer and can change the \
role later. Admins do everything the owner does except managing the team and removing the \
company. Viewers see the tests, questions, candidates and scorecards, download and share \
reports, but change nothing and can't top up.
- Adding a member: the owner enters their email and role on the Team tab; they get an email \
with a join link (also shown on their row, to copy). The join page shows the company; only \
someone signed in with that email can join. A used link says so, and opens the company for the \
member who joined.
- A company's Action log tab (the owner only): everything its members did, newest first, with \
who, when, and whether the assistant, an AI app, the API or an ATS did it for them; filtered by \
member, kind of action and days. Actions are kept 12 months.
- A company's Brand tab (owners and admins): its logo (also set by clicking the logo beside its \
name), colors, a set for the light theme and one for the dark, in groups: page, primary \
(buttons), secondary (fills and gray text), dialogs and borders, then the font (prepza's pair, \
Poppins titles over Geist text, by default; or one font for all the text, one of about twenty \
popular web fonts such as Inter, Roboto, Open Sans, Lato or Montserrat) and how round the cards' and the buttons' corners are, in px, beside a preview. Colors whose \
text would be hard to read can't be saved; "reset" brings back what was last saved, "reset to \
prepza defaults" prepza's colors, font and rounding. Candidates see the whole \
interview process in them, and a company's interview pages never show prepza's header or \
footer. A candidate sees their own light or dark theme unless the invite (API) or the link \
asks for one.

Creating a test (an interview in the menus):
- Or start from a template: a company's "templates" tab lists ready-made tests by role, \
searchable and filtered by level and language. Using one copies it into the company's own \
test at once, free and with no generation; it can then be changed like any test. Templates are \
ready-made for common roles; for a closer fit, generate a test from the job description.
- Paste a job description. "Generate in" next to the text box picks the language the test is \
written in, whatever language the description is in.
- prepza proposes topics. Before any questions are written, review them: uncheck topics you \
don't need, rename a topic, edit its subtopics, or describe bigger changes in plain words. Then \
confirm, and the questions are written.
- Every topic gets its own bank of multiple-choice questions with four options each: most have \
one correct option and three plausible wrong ones; about 1 in 10 are "select all that apply", \
with 2 or 3 correct options, and each candidate gets the same share of them. A "select all that \
apply" question earns part of its point for each right option ticked, and nothing with a wrong \
one ticked; the grade is the share of points. Set how many questions each topic asks a \
candidate (10 by default).
- Generating tests is free: up to {interviews_per_day_unpaid} a day per company until its first \
top-up ({interviews_per_day} after), as long as at most {waiting_interviews_unpaid} generated \
test has no candidate invited yet ({waiting_interviews} after the first top-up). Tests copied \
from templates don't count.

Candidates:
- Invite candidates by email or resend an invite. Revoke any candidate: before they start it \
withdraws the invite; after, it erases them and their results for good (also how a candidate's \
request to delete their data is handled). Or turn on the test's \
shareable link (settings tab) for a job ad: anyone who opens it signs in and takes \
the test, charged like an invited candidate; it can be turned off at any time. The invite page \
tells candidates what to expect.
- Until a candidate finishes, owners and admins see their invite link on the candidate's page, \
in a card with a copy button, to send it themselves if the email didn't arrive.
- Each candidate gets a random subset of each topic, with their own question and option order, \
in a single pass. A candidate can change their pick until they press Next question; then it's \
final.
- Each question has its own countdown, kept by the server: by default, by the test's level, \
{seconds_basic} seconds for a basic test, {seconds_medium} for a medium one and {seconds_hard} \
for a hard one; adjustable per test. At zero the pick on screen counts; with no pick, the question counts \
as wrong. A test the candidate \
leaves finishes by itself once its total time, plus 10%, has passed; unanswered questions count \
as wrong.
- Extra time: for a candidate who needs more time (for example because of a disability), owners \
and admins give +25%, +50% or +100% on each question on the candidate's page, before they start; \
no reason is recorded. Someone taking the test through a shareable link asks the company for a \
personal invite first. The site's guide "How to time a skills test" \
(/guides/skills-test-timing-and-extra-time) explains choosing the time per question, the number \
of questions, the total length and extra time.
- Any member of the company can try a test as a candidate first (the play button on the \
interviews list or on the test's page): the same timed questions, free, and not counted as a \
candidate.
- A company's interviews list has a search above it that finds tests by their title.
- Each test shows its status: new (no candidate invited yet), in process (candidates invited) \
or hired (marked so in the test's settings, "Mark as hired").
- Candidates can rate a question or report a problem with it. They never see their score or \
whether an answer was right.

Results:
- Scorecards show every answer, whether it was right and how long it took (for a "select all \
that apply" question, the options ticked, which were right, and its points, such as "2 of 3 right \
options · 0.67 of 1 point"), and flag answers too fast to have read the question, leaving the \
page, and copy attempts.
- Questions improve on their own: answers, votes and reports flag weak questions, and a \
verifier fixes or replaces them in the background. A company can also re-generate single \
questions. A fixed question applies to candidates who start after the fix; results already \
given never change.

Credits and billing:
- prepza is pay as you go with credits: a candidate takes the same credits whatever the \
top-up (candidate_credits in the prices); larger top-ups buy those credits for less money. \
Credits never expire. There are no paid subscriptions or plans. Credits belong to a company's \
wallet.
- A candidate costs credits (see prices) once they've answered at least one question: charged \
when their interview ends, whether they finish it or its time runs out while they're away, or \
when they're revoked. A question whose time ran out with no answer picked doesn't count. \
Credits are set aside when a candidate is invited and come back if they're revoked before \
answering anything, never start, or their interview ends with nothing answered.
- A person's first company gets free welcome credits (see prices).
- Top up on the top-up page (account menu → Top up), a company's billing tab or its credits in \
the company's header, for a company you belong to (owners and admins): its dialog buys any \
number of candidates in the range on a slider ("custom" in the prices), each level at its price \
per candidate, never more than the next level costs: from a level's "upgrade_from", the same \
money buys the next level's first count instead. It shows the price, the credits and the \
candidates before checkout. Payments go through Paddle, which issues the receipt.
- Automatic top-up, optional, on the top-up page and under the top-up dialog's button: choose \
one of the fixed top-ups ("products" in the prices) and a balance to refill \
under. Turning it on saves the card through Paddle as a subscription that costs nothing; only \
the top-ups it makes are charged. A declined charge is tried again after 1, 3 and 7 days; after \
that, or at once when the bank refuses the card for good, automatic top-up pauses and the \
company's owners and admins are told (email and the bell): the person whose card pays updates \
it with "Update card" on the company's billing page, and it starts again. A new price for it is \
emailed at least 30 days before it applies; until then it charges the old one. Changing the \
company's currency changes what it charges at once.
- Currencies: prices are in the local currency in Canada, Australia, Israel, Poland, \
Switzerland, Japan, South Korea, Taiwan, Hong Kong, Thailand, Singapore and India; in euros in \
the rest of the EU and in Iceland, Liechtenstein and Norway; in pounds in the UK; and in US \
dollars elsewhere (the prices below are in the visitor's). Each person \
and each company has its own currency, detected from the country and kept when travelling: a \
person changes theirs in Settings; owners and admins change a company's beside its Top up \
button (its billing tab, the top-up page). A company's top-ups, automatic ones too, are \
charged in the company's currency, whoever pays and wherever they are.
- A company's Billing tab (owners and admins): the balance, the credits reserved for \
candidates who haven't finished (listed under "reserved"), the history of every credit \
movement with each top-up's invoice, and the automatic top-up setting.
- Referrals: a company's link is in its referrals tab. Both companies get credits on the \
newcomer's first top-up, of any amount (see prices).

Integrations (a company's Integrations tab; owners and admins connect them, at no extra cost):
- ATS: Workable, Greenhouse, Teamtailor, Recruitee and Breezy HR, each connected with a key the \
company creates in its ATS. A job in the ATS is linked to a prepza test and a stage: moving a \
candidate to that stage sends them the invite, and when they finish, their grade, whether they \
passed, integrity flags and a scorecard link go back to the candidate in the ATS. Candidates \
who couldn't be invited (no credits, limits, the pause) are listed and can be invited again; \
after a top-up they're invited by themselves.
- Slack: "Add to Slack" picks a channel; the company chooses which notifications go there \
(a candidate finished, an ATS candidate not invited, an undelivered invite and more).
- API: for a company's own platform. On the API page an owner or admin makes API keys (shown \
once; they expire in 1, 3, 6 or 12 months, or never), ticking what each may do (read or create \
interviews; read, invite, change or remove candidates; read credits; use with AI agents), and \
web hooks. A new key starts with reading interviews and candidates; owners and admins can \
later change a key's permissions, adding or taking away any, and a call it may not make \
gets a 403 naming the missing permission. A key creates tests from \
job descriptions, lists the company's tests and candidates with their results, invites \
candidates (an Idempotency-Key makes a retry safe), reminds, renames, gives extra time to or \
removes them, finds a candidate by email and reads the credits, and syncs its lists by what \
changed (updated_since); a web hook hears, signed with \
its secret, when a candidate starts, finishes (with their results), isn't reached, expires or is \
removed, and when an interview is ready; each web hook can be sent a test event and has a \
delivery log of its latest sends. A web hook that doesn't answer for 3 days is paused (no \
events reach it) until a test event goes through. An invite can skip prepza's emails and sign-in \
(the platform sends the candidate the link itself), bring the candidate back to the \
company's site when they finish, and ask for the light or dark theme. With prepza's SDK (a \
script), the company's own page shows the interview itself. Bringing candidates back and \
embedding work only on the domains the company allows on its API page (localhost only when it \
allows it); verification isn't needed for the API, the SDK or AI apps, it only adds the \
verified badge. An API key can be limited to allowed IP addresses. The reference is the \
"developer docs" page, linked in the footer.
- AI apps: Claude, ChatGPT and other apps that support MCP connect to prepza; any member can \
connect one (Integrations → AI apps → Instructions has the address and the steps). Connected, an app acts as the person who \
connected it, in every company they're in, with their role there: it reads tests, candidates \
and results, and makes changes they ask for; it can't delete an account or a company. Turning \
off "Allow changes" when connecting lets an app only read. \
The company's action log marks what an app did as done through an AI app. A company's owners and \
admins can stop AI apps from using that company's data with "Allow AI apps" on its AI apps page. \
The developer docs' MCP tab has the steps for other apps (Gemini CLI, Cursor, VS Code, Le Chat) \
and example agents in Python and TypeScript (LangChain, LangGraph, LlamaIndex). An agent on a \
server signs in with a company API key that has the "Use with AI agents (MCP)" permission: it \
acts as the key's maker in that company only, with only the tools its permissions allow.

Account and settings:
- Settings has the interface language, Emails, "Your account" (a "copy id" button) and "Your data" \
("Download my data" and "Delete account").
- Reporting a problem: write on the contact page and paste the ID of what it's about, so the \
prepza team finds it at once. "copy id" sits under the name of a company, an interview and a \
candidate (on their pages), and the account's is in the account menu and in Settings.

Emails:
- Service emails always go out: invites, candidate reports, billing problems (such as a failed \
automatic top-up) and changes to the terms.
- Settings → Emails chooses the rest: the activity digest (one email a day about what happened \
in your companies: candidates who finished, undelivered invites, ATS candidates not invited, \
interviews ready; each can be turned off), reminders to owners and admins (low credits, \
interviews with no candidates, topics waiting for review), product updates and news, and offers \
and promotions. Every one of these has an "Unsubscribe" link that stops it without signing in, \
and a link to the email settings.
- prepza's news shows in everyone's notifications (the bell); the major news is also emailed as \
a product update to those with product updates on, and offers only to those who turned offers \
on. A change to the terms or the privacy policy shows in the notifications too, with a banner \
on the site until it applies.
- Candidates' invites have a "Don't email me for <company>" link, and reminders also "Don't \
send me reminders for this interview". After a candidate stops a company's emails, prepza \
doesn't email them for that company again and the company sees the invite as not delivered.
- The site works in {language_count} languages: {languages}. On a first visit it opens in the \
browser's language if supported. Arabic, Hebrew and Persian read right to left.
"""

# Everything the help chat answers from; the in-app assistant reads the same (GET /help/guide).
HELP_KNOWLEDGE = """\
<guide>
{guide}
</guide>

<faq>
{faq}
</faq>

<prices>
{prices}
</prices>

<terms>
{terms}
</terms>

<privacy_policy>
{privacy}
</privacy_policy>"""
