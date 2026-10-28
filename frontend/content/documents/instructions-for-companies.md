# Using prepza responsibly: instructions for companies

Version of 2026-10-17. Arcolabs OÜ (registry code 17587452), Sepapaja tn 6, 15551 Tallinn, Estonia; hello@prepza.ai.

For owners and admins of a company on prepza. These are prepza's instructions for use under the
EU AI Act (Art. 13). Your own duties as an employer, under the employment and data protection law
that applies to you, stay yours.

## 1. What prepza is and is for

- **Provider:** Arcolabs OÜ, above. **You** (the company that tests candidates) are the deployer.
- **Intended purpose:** testing job candidates' knowledge for one role with a timed
  multiple-choice interview, to help the people at your company decide whom to take further. AI
  writes the questions from your job description (up to half of a topic may be proven questions
  from prepza's own templates, never ones shown publicly for practice); you review the topics; each
  candidate's answers are marked against a fixed answer key.
- **High-risk AI system.** Under the EU AI Act, a system used to evaluate candidates is high-risk
  (Annex III point 4(a)), and prepza is treated as one. Its obligations apply from 2027-12-02;
  before then prepza signs its EU declaration of conformity and is registered in the EU database,
  and from 2027-11-02 the CE marking is shown in the site footer, linked to the declaration.
- **Not for:** see section 11.

## 2. What a prepza grade is

- The **percentage of points earned**, over every question the candidate was shown. Each question
  is worth one point:
  - most questions have one right option of four: 1 point when it's picked, 0 otherwise;
  - about 1 in 10 are **"select all that apply"** (shown as such to the candidate): 2 or 3 of the
    4 options are right and the candidate ticks every option they think is right. Any wrong option
    ticked scores 0; otherwise the question earns the share of its right options ticked (2 of 3:
    0.67 of a point). Each candidate gets the same share of these questions.

  With single-answer questions alone, the grade is the percentage answered correctly. A question
  with nothing picked when its timer ran out counts as wrong. Candidates can change their pick
  until they move on; only the final one is kept.
- Each answer is marked against the question's **answer key**. No AI marks answers,
  and nothing else (speed, page leaves, copy attempts) changes the grade. If a question's key is
  found to be wrong and corrected, the fix applies to candidates who start after it; answers
  already given, and their grades, don't change.
- **Green or red** only compares the grade with the passing grade you set. **The ranking** sorts by
  grade, best first.
- **Explaining a grade:** the candidate's scorecard shows every question, the options picked, right
  or wrong, the points of a "select all that apply" question ("2 of 3 right options · 0.67 of 1
  point"), the time taken, and the integrity signals. That is everything the grade comes from.

## 3. Accuracy and its limits

- **Declared accuracy:** a correct answer key for **at least 98% of questions**, single-answer and
  "select all that apply" alike (for the latter, every option correctly marked right or wrong).
  Measured in prepza's offline evaluations, checked by an AI judge: 99% for single-answer
  questions (240 questions in 8 fields, 2026-10-04; 98% had exactly one defensible answer) and
  98.5% for "select all that apply" questions (268 of them on 48 subtopics, 2026-10-17). The key
  checker caught 60 of 60 single-answer and 263 of 263 "select all that apply" wrong keys planted
  on purpose. Every new "select all that apply" question is also answered again blind, and dropped
  if that answer differs from its key or it leaves a deciding condition unstated. A change of
  model or prompt that misses the target isn't released without a reason.
- **What that means for a grade:** the grade counts points against the key. A key found wrong is fixed for candidates who start afterwards; grades already given are never marked again,
  so a candidate may have answered a question whose key was later corrected (section 5).
- **In use:** before an interview is ready, one answer key per topic is checked again. After 30
  answers, a question is flagged and fixed or replaced when it is answered right by 15% or fewer, by
  95% or more (for a "select all that apply" question, by its average points), when a wrong
  option is picked more often than the key (than its least-picked right option), when strong and weak
  candidates get it right about equally often, or when time runs out on a quarter of its showings;
  also after 2 reports of the same problem.
- **What a grade is not:** a measure of overall ability, experience, potential, personality or
  fit; a qualification or certificate.
- **Not exactly comparable between candidates:** each one gets a different random set of questions
  from the same bank, so small differences (a few points) can come from the draw.
- **Not free of error:** a question can still be wrong or unclear, especially in a new interview
  before about 30 people have answered it.
- **Language and reading speed:** when the interview is timed and not in the candidate's first
  language, it also tests those. Choose the interview's language with your candidates in mind.
- **Groups of candidates:** prepza collects no data about candidates' sex, age, origin or
  disability, so it can't measure results by group for you. An independent bias audit of prepza
  is done before 2027-12-02 and every year after, and its summary published at prepza.ai/documents.
- **Job performance:** prepza doesn't learn how hired candidates do in the job, so it doesn't
  show that a grade predicts job performance.

## 4. What prepza needs from you (input)

- A job description, or a description of the role, that names what the job actually needs. Only
  what is in it becomes topics.
- Your review of the topics before questions are written: uncheck what the job doesn't need,
  rename or edit, then approve. The approval is recorded.
- A passing grade and time per question that fit the role (section 6).

## 5. Human review: your duty

People at your company make the hiring decision. prepza never tells a candidate they were rejected.

- **Give the review to people who understand prepza:** these instructions, especially sections 2,
  3 and 7, are what they need to know.
- **Before rejecting anyone on a prepza result, a person must open their scorecard** and look at the
  answers, not just the grade, colour or rank.
- Use the grade **alongside** other information (CV, work samples, interviews), not as the only
  gate.
- If a question looks wrong, report it with **Wrong answer**: prepza checks its answer key again,
  usually within a day, and tells you when it's fixed. Take that into account for candidates who
  already answered it.
- **Candidates can ask you for a human review** of their result (prepza tells them so on the invite
  page, and reminds you on the results page and in PDF reports). Name who handles these requests,
  reply within a reasonable time, and be ready to explain what was tested and how the result was
  used.
- In the EU, a decision based solely on automated processing that significantly affects a candidate
  is restricted (GDPR Art. 22). Rejecting automatically everyone below the passing grade can be
  one.
- The same applies to results prepza sends to the tools you connect: your applicant tracking
  system, Slack, or your own systems through the API and web hooks receive the grade and whether
  it reached the passing grade. **Don't set them up to reject candidates automatically** on those
  results; the human review above applies there too.
- **The assistant and AI apps.** prepza's in-app assistant acts only after the member confirms
  each change. AI apps (Claude, ChatGPT and others) a member connects act with that member's
  access, and the data they read goes to that app's provider. Owners and admins can turn AI apps
  off for the company (Integrations → AI apps → **Allow AI apps**). The same human review applies
  to results read through them. Both answer with AI and can misstate or leave out part of a
  result: before acting on what they say about a candidate, check the candidate's scorecard, and
  don't let them decide about a candidate. They don't change grades; they read what prepza
  recorded.

## 6. Choosing a passing grade

- The default 70% is a starting point, not a recommendation for your role.
- Try the interview yourself first (**Try as a candidate**, free). Ask one or two people who do the
  job well to try it too: their grades show what "good" looks like.
- Set the passing grade from what the role needs, and write down why. Don't raise it to cut volume.
- Treat grades near the passing grade (for example within 5–10 points) as a band that deserves a
  closer look, not a hard cut.
- Keep the same passing grade for every candidate of the same interview.

## 7. Integrity signals

Page leaves, copy attempts and answers under 3 seconds are **hints, not proof**. A notification, an
accessibility tool, a slow connection or a fast expert can all trigger them. They're reported by the
candidate's browser, and a page leave counts only when it lasts 2 seconds or more (a shorter one,
such as a notification or a permission prompt taking focus, is kept but not counted). Never reject
on signals alone; follow up in a conversation, and let the candidate explain.

## 8. Accommodations and extra time

- Tell candidates, before they start, how to ask for an accommodation (the candidate notice
  templates include this).
- prepza's invite page tells candidates to ask you for more time before they start.
- For a candidate who asks, set **extra time: +25%, +50% or +100%** on every question's timer, on
  the candidate's page. It can be set or changed only **before the candidate starts**, so agree it
  first. prepza stores only the amount, never the reason. Their grade is compared with the same
  passing grade.
- Candidates who come through your shareable link can't get extra time there: the page tells them
  to ask you for a personal invite first. Invite them by email instead.
- If timed multiple choice doesn't suit the candidate's needs at all (for example some screen-reader
  or motor impairments), offer an **alternative assessment** outside prepza. Don't ask for medical
  details beyond what you need.
- You can also raise the time per question for everyone in the interview's settings.
- prepza's candidate pages are built to WCAG 2.2 AA.

## 9. Telling candidates

Before you invite, tell candidates that they will take a timed AI-generated knowledge test, what it
covers, how the result is used, that page leaves and copies are recorded, that they confirm answering
on their own before they start, how long data is kept, and
how to ask for an accommodation, an alternative or a human review. prepza's candidate notice
templates (at prepza.ai/documents) are a starting point. prepza's invite page also tells candidates
what to expect and links prepza's privacy policy, but the notice about **your** use of the results
is yours to give.

- Until prepza has verified your company, your invite pages and emails say so in a small line.
  Use **Verify company**: your website, and a sign-in with an email on its domain.
- prepza's invite and reminder emails let candidates stop your company's emails, or that
  interview's reminders, with a link at the bottom. Once a candidate stops your company's emails,
  prepza doesn't email them for your company again: an invite to them shows as undelivered in the
  candidate list, so reach them another way if you still need to.
- **Candidates from your own platform.** Through the API your platform can invite a candidate with
  `sign_in` false: prepza then sends them no emails, and they take the interview from their invite
  link without signing in to prepza, so the notice and the link are yours to send, to that
  candidate only (anyone with the link can use it). The invite can also set a `return_url`, a
  **Back to** your company button on the finished page, and a `theme` (light, dark, or the
  candidate's own). prepza's SDK (prepza.ai/embed/v1.js) shows the interview inside your own page.
  The return button and the embedded interview work only on the domains your company allows on its
  API page (localhost only when you allow it, to try it on your own computer); verification isn't
  needed for them, nor for the API or AI apps: it only adds the verified badge. The candidate still sees prepza's invite page, in your company's logo and
  colors if you set them, before they start. Leaving the embedded interview, also for the rest of your page, counts
  as a page leave. The developer docs (prepza.ai/api-docs) give the details.

## 10. Records, retention and data requests

**Records (logs).** For each candidate prepza records every question shown and when, the picks,
right or wrong (or the points of a "select all that apply" question), the time taken, timeouts, page leaves and copy attempts, start and finish: the
scorecard and its PDF report show them, and the API returns the results. It also records when the
candidate confirmed, before starting, that they'd answer on their own, which the scorecard shows. Your company's action
log records every action your members take: on interviews (created, renamed, settings, shareable
link, topics approved, passing grade), on candidates (invited, revoked, deleted, renamed, extra
time, results viewed, reports emailed), on the team, the company, billing and integrations (ATS,
Slack, API keys and web hooks), with who acted, when, and whether they acted in the app, through
the assistant, an AI app, the API or an ATS. The owner reads it on the company's **Action log**
tab, filtered by member, kind of action and days, or through the API
(`GET /companies/{id}/audit`). Keep what your law requires: the EU AI Act asks you to keep
these records at least six months, and prepza keeps them for you as below. Download PDF reports to
keep them longer.

**Retention.**

- Candidate results, timings and signals are **deleted automatically 12 months after the invite**
  was last sent.
- Invites never started expire after 30 days.
- Candidates your applicant tracking system sends (their email and ATS ids) are kept 12 months.
- The action log is kept 12 months.
- Job description text is kept 90 days in generation records; the interview stays until you delete
  it.
- A candidate's request to stop your company's emails is kept, as a one-way hash of their email
  address, until you delete the company, also after you delete the candidate.
- Backups hold deleted data for at most 14 more days.
- PDFs you download, and results sent to your applicant tracking system, Slack or your own systems,
  are yours to keep and delete under your own retention policy.

**Data requests.** You are the controller of candidates' interview data; prepza is your processor
under the data processing agreement at prepza.ai/dpa, which is part of the terms.

- **Access:** open the candidate's **scorecard page** and download their **PDF report**. Together
  they hold everything prepza keeps about the interview: each question, their answer (every option ticked), right or
  wrong or the points it earned, time taken, page leaves and copy attempts, and the grade. Send the PDF, with your own explanation of
  how it was used.
- **Erasure or objection:** on the candidate's page, revoke an unused invite, or use **Delete
  candidate** for one who started or finished: their answers and results are deleted for good, also
  from the bell and from prepza's record of them for your applicant tracking system, and credits
  still held come back (a finished candidate stays charged). Copies already sent to your applicant
  tracking system, Slack or your own systems are yours to delete there.
- If a candidate writes to prepza instead, prepza passes the request on to you.
- Candidates can also download what is linked to their own prepza account with **Download my data**
  in Settings.

## 11. Where not to use prepza

- As the **only** basis for a rejection without human review.
- For skills a multiple-choice knowledge test can't measure (manual, interpersonal, creative work)
  or knowledge the job doesn't actually need.
- For promotion, termination, performance monitoring or task allocation of employees.
- For candidates under 16.
- For **New York City** roles, before you have done what Local Law 144 asks of you as the employer:
  a bias audit by an independent auditor within the year before use, its summary published, and a
  notice to candidates at least 10 business days before they are assessed. prepza gives you the
  candidates' results (API, PDF reports) for the audit, the summary of its own bias audit, and a
  notice template.
- Where your local law requires a works council agreement, a regulator approval or a bias audit you
  haven't done.

## 12. Your duties as a deployer under the EU AI Act

From 2027-12-02, when you use prepza in the EU:

- use it as these instructions say, and give human review to people with the competence and
  authority for it (section 5);
- make sure the job description and topics are relevant to the role (section 4);
- watch how it works for you, and tell prepza at once of a serious problem (below);
- keep the records for at least six months (section 10);
- tell your employees' representatives before you use it for hiring, where your law requires;
- tell candidates that a high-risk AI system is used to assess them (section 9), and explain, on
  request, the role it played in a decision about them;
- use these instructions for your data protection impact assessment (prepza's DPIA template at
  prepza.ai/documents).

## 13. Availability, changes and support

- **What it needs:** a current web browser; candidates are best on a computer. Nothing to install.
- **Maintenance:** prepza runs and updates it. During a maintenance break the site is closed and
  candidates' timers stop, so no one loses time. In an emergency prepza can pause new interviews;
  candidates already in one can finish.
- **Lifetime and updates:** prepza is a hosted service with no set end of life: prepza maintains
  it for as long as it offers it, and updates it continuously, with nothing for you to install or
  do. A new AI model or prompt is released only after it meets the accuracy target in section 3.
  If prepza ever stops offering the service, you are emailed in advance, with time to download
  your results.
- **Changes:** questions are improved continuously (section 3); a fix applies only to candidates
  who start after it. A change to how grades are worked out or to these instructions is published
  here with a new version date. A significant change to the terms or the data processing agreement
  is emailed to you at least 14 days before it applies.
- **Security:** sign-in with Google, LinkedIn or GitHub and a verified email; only the invited
  email can start an invite, except an invite your platform sent through the API without sign-in,
  which anyone with its link can use; roles limit what admins and viewers can do; API keys are kept only as
  hashes.

## Reporting serious problems

Tell prepza at once at hello@prepza.ai if a result may have harmed a candidate (for example a
wrong answer key behind a rejection), you see signs of unfair results for a group of
candidates, or anything looks like a security problem. prepza investigates, and reports serious
incidents to the authorities when the law requires it.

Questions: hello@prepza.ai.
