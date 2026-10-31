# Data protection impact assessment (DPIA): template for companies using testee

Version: 2026-10-23\
Operator: Arcolabs OÜ (registry code 17587452), Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia; hello@testee.ai

For companies that invite candidates through testee. Your company is the **controller** of
candidates' interview data; Arcolabs OÜ (testee) is your **processor**. Parts marked
**[COMPANY]** are yours to complete. Parts already filled describe testee as of the version date,
matching the data processing agreement (testee.ai/dpa) and privacy policy (testee.ai/privacy) of
the same date; if either changes, the current version applies, and testee emails your owners and
admins about a significant change to the agreement at least 14 days before it applies.

Whether you need a DPIA is your decision. Many EU supervisory authorities list systematic
evaluation of candidates, new technologies and AI in recruitment among the cases that require one;
check your authority's list.

## 1. Overview

| Item | Answer |
|---|---|
| Controller | **[COMPANY]** name, address, DPO or privacy contact |
| Processor | Arcolabs OÜ, registry code 17587452, Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia; hello@testee.ai (no DPO is required; this address handles data protection) |
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
   testee's API) invite them too. Each invited candidate signs in (Google, LinkedIn or GitHub) with
   the invited email address, and gets a random subset of questions with a timer on each.
4. testee marks each answer against the question's answer key (a question is worth one point; a
   "select all that apply" question, about 1 in 10, earns part of it for each right option ticked
   and nothing with a wrong one) and shows you a grade, the percentage of points earned, green or red against the passing grade you set, ranked best first, with
   integrity signals.
   If you set an interview to **voice mode** (English, Spanish, German, French, Portuguese or
   Italian), testee reads each question and its options aloud and the candidate answers aloud:
   what the microphone picks up while they answer is turned into text by AI and matched to the
   options; a clear choice of one option is recorded at once as a tapped answer is, with the
   interviewer saying which ("B, saved."), and a choice of several options is confirmed first. The audio
   and its text are never stored, voices are never analysed (no tone, emotion or confidence), and
   the candidate can always tap an option instead. Marking is the same in both modes.
5. You review results and decide. testee sends candidates no decision. If you connect them, testee
   also sends results to your applicant tracking system (as a note), your Slack channel (the
   notifications you choose) and your own systems (through the API and web hooks).
6. Your team can ask testee's assistant about interviews, candidates and results, in the app or
   through an AI app a member connects to their own testee account (such as Claude or ChatGPT).
   It reads with that member's access and role, can summarise and compare candidates, and can
   act for them (inviting, changing a pass mark, revoking): in the app each action waits for their
   confirmation; through an AI app, whether to ask first is up to that app.
7. Your team can write notes on an interview (its Notes tab, the assistant, AI apps or the API's
   keys); candidates never see them.
8. If you have topped up at least once, an interview's **Discover** tab lists people who chose to
   be open to offers and practised its subjects at its level: their name, LinkedIn profile and
   latest timed practice results. testee shows them with their consent, as their controller; what
   you do with what you see, and anyone you invite from there, is yours as controller (see
   section 3, Information to candidates).

**Data categories.**

| Category | Details |
|---|---|
| Identity and contact | Invited email address; name (from you, your applicant tracking system or the sign-in) and account id from sign-in; the candidate's id in your applicant tracking system, if it sent them |
| Assessment | Questions shown, answers (every option ticked), right/wrong or points, time per answer, timeouts, topic and overall grades, pass/fail against your passing grade, rank |
| Accommodations | Extra time you give a candidate (the amount only, never a reason) |
| Integrity signals | Times the candidate left the page (with how long they were away), copy attempts, answers under 3 seconds, each with the question on screen; answer patterns worked out when you read the results and never stored (answer times about the same on every question whatever its length, or hard questions right while easy ones were wrong, against all candidates' answers), with up to 3 follow-up questions to ask in a live interview |
| Voice mode | Only for an interview you set to it: what the microphone picks up while the candidate answers (their spoken answer, and any other voice in the room), turned into text and matched to the options in memory, never stored; the options they choose are stored as answers |
| Team notes | Notes your members and API keys write on an interview, which may name candidates; kept with the interview |
| Open to offers | For people on your Discover tab: name, LinkedIn profile address, latest timed practice results on your interview's subjects; never their email until you invite them |
| Pledge | When the candidate confirmed, before starting, that they'd answer on their own, without AI tools or other people |
| Feedback | Candidate's ratings and reports of questions (reports may include a free-text comment) |
| Reports | PDFs made in your browser; if emailed through testee, kept at most 7 days to send |
| Email opt-outs | A one-way hash of the email address of a candidate who stops your emails (or one interview's reminders) through the link in testee's invites and reminders |
| Special categories | None requested. **[COMPANY]** confirm you do not add any (e.g. in job descriptions or notes) |

**Data subjects.** Job candidates **[COMPANY: approx. number per year]**; your staff using testee.

**Recipients and sub-processors** (per testee's privacy policy and DPA at testee.ai/dpa):

- Google Cloud (hosting, database, events; EU, Belgium, region europe-west1) and Google Firebase
  (sign-in; Google LLC, United States, under the EU-US Data Privacy Framework).
- OpenAI (writing and checking questions; receives job descriptions, questions, how many people
  picked each option, and the reasons questions were reported, never reporters' comments. The
  assistant's answers: the member's questions and the data its tools read with their access,
  which can include candidates' emails, names, grades and integrity signals; voice messages
  turned into text. In voice mode: questions read aloud (no personal data), and a candidate's
  spoken answer turned into text and matched to the options, from the recording and then its
  text with the question and options, never the answer key. testee tells OpenAI not to store it; under OpenAI's API terms it keeps the
  data for at most 30 days, only to check for abuse, and uses none of it for training. OpenAI
  Ireland Ltd, which transfers it to OpenAI in the United States under the European Commission's
  standard contractual clauses).
- Resend (emails; EU, Ireland).
- Google Workspace (testee's email inbox: messages from companies and candidates, and requests passed on to the company; Google Ireland Ltd, mail may be stored outside the EU under the EU-US Data Privacy Framework and standard contractual clauses).
- Sentry (error reports, without email addresses; EU).
- Langfuse (records of AI calls, to monitor and improve the quality of answers: what is sent to the AI and its answers, which can include candidates' data the AI handles, such as the results the assistant reads to answer a member, and votes on the assistant's answers; in voice mode only which options a spoken answer matched, never its words; kept 30 days; Langfuse GmbH, Germany, its EU cloud).
- Cloudflare (the "I'm not a robot" check, Turnstile, when a candidate starts through a job ad's link: their browser's signals and address, from which testee keeps only whether it passed; Cloudflare, Inc., United States, under the EU-US Data Privacy Framework).
- Upstash (short-lived counters for limits and live updates; EU, Belgium).
- Paddle (payments; receives no candidate data).

**Tools you connect** (your own recipients, not testee's sub-processors; delete the ones you don't
use): **[COMPANY: your applicant tracking system (Workable, Greenhouse, Teamtailor, Recruitee or
Breezy HR), your Slack workspace, your own systems through testee's API and web hooks]**. They
receive candidates' emails, grades, whether the grade reached the passing grade, integrity signals
and a link to the results; your applicant tracking system also sends testee the email and id of
each candidate you move to a linked stage, kept 12 months.

**AI apps your members connect** (the member's own recipients, not testee's sub-processors):
an app such as Claude (Anthropic) or ChatGPT (OpenAI) that a member connects to their testee
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
contractual clauses. testee gives a copy of the
safeguards on request. Transfers to tools you connect are yours to cover. For candidates under
UK data protection law, transfers from the UK to testee in the EU need no safeguard (UK adequacy
regulations), and the onward transfers rely on the UK Extension to the EU-US Data Privacy
Framework (Google Firebase, Cloudflare) and the standard contractual clauses with the UK
International Data Transfer Addendum (OpenAI).

**Retention.** Candidate results, timings and signals: deleted automatically 12 months after the
invite was last sent. Unstarted invites expire after 30 days. Candidates your applicant tracking
system sends: their email, name and id there, 12 months after they arrive. Job description text in
generation records: 90 days. Your company's action log: 12 months. Assistant conversations: 90 days after the last message, and at once when your
company is deleted. AI app connections: until the member disconnects one or deletes their
account, and 90 days after its last use. Candidates' requests to stop your emails: until your
company is deleted.
Records of AI calls at Langfuse: 30 days. Team notes: with their interview. Voice mode's spoken
answers: never stored.
Database backups: 14 days, then overwritten. **[COMPANY]**: your own retention of
downloaded PDFs and notes, and of what reached your applicant tracking system, Slack and own
systems.

**Automated decision-making.** testee computes a grade and ranking but makes no decision. Whether
your process is "solely automated" under GDPR Art. 22 depends on how you use it. **[COMPANY]**
describe who reviews results and how (see section 5).

## 3. Necessity and proportionality

| Question | Answer |
|---|---|
| Lawful basis | **[COMPANY]** usually legitimate interest (Art. 6(1)(f)) or steps before a contract (Art. 6(1)(b)); record your balancing test |
| Is the knowledge tested a genuine requirement of the role? | **[COMPANY]** you approved the topics; keep that record |
| Could a less intrusive method work? | **[COMPANY]** |
| Data minimisation | Only sign-in details and test data; no CV, video, voice recordings or demographics are kept by testee; in voice mode, speech is turned into text and options in memory and never stored or analysed for anything else |
| Information to candidates | For people you invite from the Discover tab, you got their data from testee, not from them: tell them, at the latest in your first message (the invite), who you are, why you contacted them, what you saw (name, LinkedIn profile, practice results) and their rights (GDPR and UK GDPR Art. 14). Invite page tells candidates what to expect, whether testee has verified your company, that leaving the page and copying are recorded, that questions are AI-written, that people at your company decide and can review their result, and to ask you for more time if needed. Invites and reminders have links to stop your emails or that interview's reminders. **[COMPANY]** add your notice (see testee's candidate notice templates) |
| Rights | Access: candidate's scorecard page and PDF report give you everything to answer; erasure: "Delete candidate" on the candidate's page (also deletes testee's copy of what your applicant tracking system sent; delete it in your own tools yourself); a candidate who deletes their testee account erases their answers and results too; objection: **[COMPANY]** process; stopping your emails: the link in testee's invites and reminders, after which an invite to them shows as undelivered; candidates can also write to testee, who passes requests on |
| Human review on request | **[COMPANY]** who handles it and how fast |
| Accommodations | Extra time per candidate (+25%, +50% or +100%), set before they start, no reason stored; **[COMPANY]** alternative process |

## 4. Risks to candidates

Likelihood and severity: **[COMPANY]** to rate. Starting points from testee:

| Risk | Typical source | testee controls | Your controls **[COMPANY]** |
|---|---|---|---|
| Unfair rejection from a wrong or ambiguous question | AI-written content | Your topic review and trial run; a sample of answer keys per topic checked before release; statistics and reports flag questions for a fix, and a fix applies to candidates who start after it (past results don't change) | |
| Discrimination (age, disability, language, origin) | Time pressure, language, content | Knowledge questions only; questions flagged when too slow or not discriminating; extra time | |
| Over-reliance on the grade or signals | Ranked list, green/red | All answers visible; signals as counts; no automatic decisions | |
| Wrongful cheating suspicion | Page-leave and fast-answer signals; answer patterns | Shown as hints with the question on screen; each answer pattern set on an offline test to flag at most 1% of honest candidates, not counted as "flagged", and shown with follow-up questions to ask rather than a verdict | |
| A spoken answer misheard (accent, speech impairment, noise) | Voice mode's speech-to-text and matching | The interviewer says and shows the option it heard: a single clear option is saved as it says so ("B, saved."), anything unclear is asked again and a choice of several options is confirmed before it counts; matching is told to answer unclear when in doubt, measured at 0 wrong matches in its eval; tapping an option is always possible; voice mode only in languages where speech recognition is reliable | |
| Other people's voices sent for transcription | A room with others talking while the candidate answers | Speech is sent only while the interview listens for an answer, turned into text in memory and never stored | |
| Candidates found through Discover treated as applicants without being told | Open to offers | Listed only with their own consent, which they can withdraw at once; no ranking or recommendation; no email until you invite | |
| Over-reliance on the assistant's summaries or comparisons | AI-written answers about candidates | It answers only from the data its tools read, says the AI can be wrong, makes no decision, and asks before every action in the app; action log marks results read through it | |
| Candidates' data in an AI app outside your control | A member connecting Claude, ChatGPT or another app | Only the member's own access; your owners and admins can turn AI apps off for your company; no access to the in-app notifications; deleting an account or a company is impossible through an app; connections end when disconnected or unused for 90 days; your action log marks what came through an app | |
| Lack of transparency | Candidates don't see their grade | Privacy policy; invite page notice | |
| Results reaching the wrong place through your tools | Applicant tracking system, Slack, API keys and web hooks | Only owners and admins connect them; keys, tokens, Slack web hooks and web hook secrets stored encrypted, API keys only as a hash; an applicant tracking system or Slack connection stops working when whoever made it is no longer an owner or admin, while API keys and web hooks belong to the company, act as themselves (every action named by its key in the action log) and work until deleted, keys also until they expire; web hooks only to public HTTPS addresses, signed; events from an applicant tracking system accepted only with its signature | |
| Data breach | Hosting, sub-processors | Access controls, encryption by Google Cloud, error reports without emails, retention limits; testee tells you within 48 hours where possible | |
| Excessive retention | | Automatic deletion after 12 months | |

## 5. Measures to reduce risk **[COMPANY]**

- [ ] Topics reviewed against the job's real requirements and the review recorded
- [ ] Interview tried by someone who knows the role before inviting
- [ ] Passing grade chosen and justified (not just the default 70%)
- [ ] A named person reviews every candidate's scorecard before a rejection
- [ ] Integrity signals never the sole reason to reject
- [ ] Candidate notice sent before the invite; accommodation route offered
- [ ] Voice mode: candidates told before they start that their answers are turned into text by
  AI, and that they can tap instead; click mode offered to anyone who asks
- [ ] Discover: people invited from it told, in the invite, where you found them and their rights
- [ ] Human review offered on request, with a response time
- [ ] Adverse impact checked on your own hiring outcomes where lawful
- [ ] Downloaded PDFs kept no longer than your retention period
- [ ] Decided whether members may use the assistant and AI apps ("Allow AI apps"), and under which terms
- [ ] New York City roles: bias audit summary published and notice given 10 business days before
  use (see testee's instructions for companies)

## 6. Sign-off **[COMPANY]**

| | Name | Date | Notes |
|---|---|---|---|
| Measures approved by | | | |
| Residual risks accepted by | | | |
| DPO advice | | | |
| Review date | | | |
