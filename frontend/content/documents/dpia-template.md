# Data protection impact assessment (DPIA): template for companies using prepza

Version: 2026-10-23\
Operator: Arcolabs OÜ (registry code 17587452), Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia; hello@prepza.ai

For companies that invite candidates through prepza. Your company is the **controller** of
candidates' interview data; Arcolabs OÜ (prepza) is your **processor**. Parts marked
**[COMPANY]** are yours to complete. Parts already filled describe prepza as of the version date,
matching the data processing agreement (prepza.ai/dpa) and privacy policy (prepza.ai/privacy) of
the same date; if either changes, the current version applies, and prepza emails your owners and
admins about a significant change to the agreement at least 14 days before it applies.

Whether you need a DPIA is your decision. Many EU supervisory authorities list systematic
evaluation of candidates, new technologies and AI in recruitment among the cases that require one;
check your authority's list.

## 1. Overview

| Item | Answer |
|---|---|
| Controller | **[COMPANY]** name, address, DPO or privacy contact |
| Processor | Arcolabs OÜ, registry code 17587452, Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia; hello@prepza.ai (no DPO is required; this address handles data protection) |
| Roles / vacancies covered | **[COMPANY]** |
| Countries of candidates | **[COMPANY]** |
| Assessment owner and date | **[COMPANY]** |

## 2. Description of the processing

**Purpose.** Assessing job knowledge of candidates for **[COMPANY: role]** with a timed
multiple-choice test, as one input to a hiring decision made by **[COMPANY: who]**.

**How it works.**

1. You paste a job description; AI (OpenAI models) proposes topics; you review and edit them.
2. AI writes a bank of multiple-choice questions per topic; you can try the interview as a
   candidate and report any question whose answer looks wrong.
3. You invite candidates by email (or share a link); if you connect them, your applicant tracking
   system (Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR) or your own systems (through
   prepza's API) invite them too. Each invited candidate signs in (Google, LinkedIn or GitHub) with
   the invited email address, and gets a random subset of questions with a timer on each.
4. prepza marks each answer against the question's answer key (a question is worth one point; a
   "select all that apply" question, about 1 in 10, earns part of it for each right option ticked
   and nothing with a wrong one) and shows you a grade, the percentage of points earned, green or red against the passing grade you set, ranked best first, with
   integrity signals.
5. You review results and decide. prepza sends candidates no decision. If you connect them, prepza
   also sends results to your applicant tracking system (as a note), your Slack channel (the
   notifications you choose) and your own systems (through the API and web hooks).
6. Your team can ask prepza's assistant about interviews, candidates and results, in the app or
   through an AI app a member connects to their own prepza account (such as Claude or ChatGPT).
   It reads with that member's access and role, can summarise and compare candidates, and can
   act for them (inviting, changing a pass mark, revoking): in the app each action waits for their
   confirmation; through an AI app, whether to ask first is up to that app.

**Data categories.**

| Category | Details |
|---|---|
| Identity and contact | Invited email address; name (from you, your applicant tracking system or the sign-in) and account id from sign-in; the candidate's id in your applicant tracking system, if it sent them |
| Assessment | Questions shown, answers (every option ticked), right/wrong or points, time per answer, timeouts, topic and overall grades, pass/fail against your passing grade, rank |
| Accommodations | Extra time you give a candidate (the amount only, never a reason) |
| Integrity signals | Times the candidate left the page, copy attempts, answers under 3 seconds, each with the question on screen |
| Pledge | When the candidate confirmed, before starting, that they'd answer on their own, without AI tools or other people |
| Feedback | Candidate's ratings and reports of questions (reports may include a free-text comment) |
| Reports | PDFs made in your browser; if emailed through prepza, kept at most 7 days to send |
| Email opt-outs | A one-way hash of the email address of a candidate who stops your emails (or one interview's reminders) through the link in prepza's invites and reminders |
| Special categories | None requested. **[COMPANY]** confirm you do not add any (e.g. in job descriptions or notes) |

**Data subjects.** Job candidates **[COMPANY: approx. number per year]**; your staff using prepza.

**Recipients and sub-processors** (per prepza's privacy policy and DPA at prepza.ai/dpa):

- Google Cloud (hosting, database, events; EU, Belgium, region europe-west1) and Google Firebase
  (sign-in; Google LLC, United States, under the EU-US Data Privacy Framework).
- OpenAI (writing and checking questions; receives job descriptions, questions, how many people
  picked each option, and the reasons questions were reported, never reporters' comments. The
  assistant's answers: the member's questions and the data its tools read with their access,
  which can include candidates' emails, names, grades and integrity signals; voice messages
  turned into text. prepza tells OpenAI not to store it; under OpenAI's API terms it keeps the
  data for at most 30 days, only to check for abuse, and uses none of it for training. OpenAI
  Ireland Ltd, which transfers it to OpenAI in the United States under the European Commission's
  standard contractual clauses).
- Resend (emails; EU, Ireland).
- Google Workspace (prepza's email inbox: messages from companies and candidates, and requests passed on to the company; Google Ireland Ltd, mail may be stored outside the EU under the EU-US Data Privacy Framework and standard contractual clauses).
- Sentry (error reports, without email addresses; EU).
- Langfuse (records of AI calls, to monitor and improve the quality of answers: what is sent to the AI and its answers, which can include candidates' data the AI handles, such as the results the assistant reads to answer a member, and votes on the assistant's answers; kept 30 days; Langfuse GmbH, Germany, its EU cloud).
- Cloudflare (the "I'm not a robot" check, Turnstile, when a candidate starts through a job ad's link: their browser's signals and address, from which prepza keeps only whether it passed; Cloudflare, Inc., United States, under the EU-US Data Privacy Framework).
- Upstash (short-lived counters for limits and live updates; EU, Belgium).
- Paddle (payments; receives no candidate data).

**Tools you connect** (your own recipients, not prepza's sub-processors; delete the ones you don't
use): **[COMPANY: your applicant tracking system (Workable, Greenhouse, Teamtailor, Recruitee or
Breezy HR), your Slack workspace, your own systems through prepza's API and web hooks]**. They
receive candidates' emails, grades, whether the grade reached the passing grade, integrity signals
and a link to the results; your applicant tracking system also sends prepza the email and id of
each candidate you move to a linked stage, kept 12 months.

**AI apps your members connect** (the member's own recipients, not prepza's sub-processors):
an app such as Claude (Anthropic) or ChatGPT (OpenAI) that a member connects to their prepza
account receives what that member asks it to read, within their role, including candidates'
data, under the app provider's own terms. AI apps never see the in-app notifications, and can't
delete an account or a company. Your owners and admins decide whether members may use your
company's data from AI apps: **Allow AI apps** on your company's AI apps page (Integrations), on
unless they turn it off, each change recorded in your action log. **[COMPANY]** record your
decision, and the terms you require (for example, only your organisation's business plans of
those apps).

**International transfers.** Three sub-processors handle data in the United States: Google
Firebase (sign-in) and Cloudflare (the "I'm not a robot" check), under the EU-US Data Privacy
Framework, and OpenAI, through OpenAI Ireland Ltd under the European Commission's standard
contractual clauses. prepza gives a copy of the
safeguards on request. Transfers to tools you connect are yours to cover.

**Retention.** Candidate results, timings and signals: deleted automatically 12 months after the
invite was last sent. Unstarted invites expire after 30 days. Candidates your applicant tracking
system sends: their email, name and id there, 12 months after they arrive. Job description text in
generation records: 90 days. Your company's action log: 12 months. Assistant conversations: 90 days after the last message, and at once when your
company is deleted. AI app connections: until the member disconnects one or deletes their
account, and 90 days after its last use. Candidates' requests to stop your emails: until your
company is deleted.
Records of AI calls at Langfuse: 30 days.
Database backups: 14 days, then overwritten. **[COMPANY]**: your own retention of
downloaded PDFs and notes, and of what reached your applicant tracking system, Slack and own
systems.

**Automated decision-making.** prepza computes a grade and ranking but makes no decision. Whether
your process is "solely automated" under GDPR Art. 22 depends on how you use it. **[COMPANY]**
describe who reviews results and how (see section 5).

## 3. Necessity and proportionality

| Question | Answer |
|---|---|
| Lawful basis | **[COMPANY]** usually legitimate interest (Art. 6(1)(f)) or steps before a contract (Art. 6(1)(b)); record your balancing test |
| Is the knowledge tested a genuine requirement of the role? | **[COMPANY]** you approved the topics; keep that record |
| Could a less intrusive method work? | **[COMPANY]** |
| Data minimisation | Only sign-in details and test data; no CV, video, voice or demographics are collected by prepza |
| Information to candidates | Invite page tells candidates what to expect, whether prepza has verified your company, that leaving the page and copying are recorded, that questions are AI-written, that people at your company decide and can review their result, and to ask you for more time if needed. Invites and reminders have links to stop your emails or that interview's reminders. **[COMPANY]** add your notice (see prepza's candidate notice templates) |
| Rights | Access: candidate's scorecard page and PDF report give you everything to answer; erasure: "Delete candidate" on the candidate's page (also deletes prepza's copy of what your applicant tracking system sent; delete it in your own tools yourself); a candidate who deletes their prepza account erases their answers and results too; objection: **[COMPANY]** process; stopping your emails: the link in prepza's invites and reminders, after which an invite to them shows as undelivered; candidates can also write to prepza, who passes requests on |
| Human review on request | **[COMPANY]** who handles it and how fast |
| Accommodations | Extra time per candidate (+25%, +50% or +100%), set before they start, no reason stored; **[COMPANY]** alternative process |

## 4. Risks to candidates

Likelihood and severity: **[COMPANY]** to rate. Starting points from prepza:

| Risk | Typical source | prepza controls | Your controls **[COMPANY]** |
|---|---|---|---|
| Unfair rejection from a wrong or ambiguous question | AI-written content | Your topic review and trial run; a sample of answer keys per topic checked before release; statistics and reports flag questions for a fix, and a fix applies to candidates who start after it (past results don't change) | |
| Discrimination (age, disability, language, origin) | Time pressure, language, content | Knowledge questions only; questions flagged when too slow or not discriminating; extra time | |
| Over-reliance on the grade or signals | Ranked list, green/red | All answers visible; signals as counts; no automatic decisions | |
| Wrongful cheating suspicion | Page-leave and fast-answer signals | Shown as hints with the question on screen | |
| Over-reliance on the assistant's summaries or comparisons | AI-written answers about candidates | It answers only from the data its tools read, says the AI can be wrong, makes no decision, and asks before every action in the app; action log marks results read through it | |
| Candidates' data in an AI app outside your control | A member connecting Claude, ChatGPT or another app | Only the member's own access; your owners and admins can turn AI apps off for your company; no access to the in-app notifications; deleting an account or a company is impossible through an app; connections end when disconnected or unused for 90 days; your action log marks what came through an app | |
| Lack of transparency | Candidates don't see their grade | Privacy policy; invite page notice | |
| Results reaching the wrong place through your tools | Applicant tracking system, Slack, API keys and web hooks | Only owners and admins connect them; keys, tokens, Slack web hooks and web hook secrets stored encrypted, API keys only as a hash; each stops working when whoever made it is no longer an owner or admin; web hooks only to public HTTPS addresses, signed; events from an applicant tracking system accepted only with its signature | |
| Data breach | Hosting, sub-processors | Access controls, encryption by Google Cloud, error reports without emails, retention limits; prepza tells you within 48 hours where possible | |
| Excessive retention | | Automatic deletion after 12 months | |

## 5. Measures to reduce risk **[COMPANY]**

- [ ] Topics reviewed against the job's real requirements and the review recorded
- [ ] Interview tried by someone who knows the role before inviting
- [ ] Passing grade chosen and justified (not just the default 70%)
- [ ] A named person reviews every candidate's scorecard before a rejection
- [ ] Integrity signals never the sole reason to reject
- [ ] Candidate notice sent before the invite; accommodation route offered
- [ ] Human review offered on request, with a response time
- [ ] Adverse impact checked on your own hiring outcomes where lawful
- [ ] Downloaded PDFs kept no longer than your retention period
- [ ] Decided whether members may use the assistant and AI apps ("Allow AI apps"), and under which terms
- [ ] New York City roles: bias audit summary published and notice given 10 business days before
  use (see prepza's instructions for companies)

## 6. Sign-off **[COMPANY]**

| | Name | Date | Notes |
|---|---|---|---|
| Measures approved by | | | |
| Residual risks accepted by | | | |
| DPO advice | | | |
| Review date | | | |
