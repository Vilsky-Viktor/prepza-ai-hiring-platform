# Interviews

An interview is a timed multiple-choice test for one role. A company makes it from a job description or a ready-made template, then invites candidates to it (see [Candidates](candidates.md)).

## Making an interview

There are two ways to start:

- **From a template:** pick a ready-made interview, searchable by role, level and language. It is copied at once, for free (at most 30 copies a company an hour by default, `TEMPLATE_COPIES_PER_HOUR`, `429` past it). The list shows only templates that can still be copied (see [Templates and practice](templates-and-practice.md#copying-a-template)).
- **From a job description:** paste it or describe the role. The AI extracts the requirements and proposes topics.

For each topic, set how many questions it asks each candidate: 10 by default, drawn from the topic's 70 (`INTERVIEW_QUESTIONS_PER_TOPIC`, a value in the admin zone's Controls), from 0 to the whole bank. A topic at 0 is left out: new candidates never see it, and it counts in no grade. The last topic with questions can't be set to 0 ("An interview needs at least one topic with questions."), and candidates who already started keep the questions drawn at their start.

Generating an interview is free. Until its first top-up, a company can have 1 generated interview waiting without a candidate before it generates another, and generates at most 3 a day; after it, 5 waiting and 10 a day. These are the defaults, which a superadmin can change in the admin zone ([Admin zone](admin-zone.md#limits)); until midnight UTC, the unpaid users' daily AI spend cap can also stop generating for a company that never topped up ([Generation](../generation.md#rate-limits)). Interviews copied from templates don't count, and retrying a failed generation isn't a new one (see [Credits and payments](billing.md)).

### Reviewing the topics

Before anything expensive runs, the company reviews the proposed topics, for free (a company that never paid shows it's a person when it approves them: [the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)):

- uncheck the topics it doesn't need,
- rename a topic or edit its subtopics in place,
- or describe bigger changes in plain text.

A review takes at most 10 revisions in words; after that, topics are only chosen by checkbox (see [Generation](../generation.md#rate-limits)).

### Questions

- Every topic gets a bank of multiple-choice questions.
- Each question has four options. Most have one correct option and three plausible wrong ones.
- About 1 in 10 are "select all that apply" (`MULTI_ANSWER_PERCENT`, see [Generation](../generation.md#select-all-that-apply)): 2 or 3 of the 4 options are right, and the candidate ticks every right one. Each candidate's draw from a topic has the same share. The question shows a multi-choice tag and a hint to select all that apply, never how many are right.
- A single-answer question scores 0 or 1 point. A "select all that apply" question scores 0 if any wrong option is ticked; otherwise it earns the share of its right options ticked (2 of 3: 0.67 of a point).
- A grade is the percentage of points earned over every question the candidate was shown; for single-answer questions alone, that's the percentage answered correctly.
- Question lists label "select all that apply" questions; scorecards and practice reviews show the options ticked, which were right, and the question's points ("2 of 3 right options · 0.67 of 1 point").
- Owners and admins can re-generate individual questions.
- An interview's questions page always shows each question with its answer options.
- Questions improve on their own: candidates' answers, votes and reports flag weak ones, and a background verifier fixes or replaces them (see [Question quality](../generation.md#question-quality)).

How generation works step by step is in [Generation](../generation.md).

### What's next

When a generated interview is ready, the generation page opens it marked as just generated (`?ready=1`), and owners and admins see a "What's next" dialog with three steps, each a button that takes them there: set how many questions each candidate gets per topic (it closes the dialog and puts the cursor in the first topic's count), adjust the time per question (the settings tab) and invite candidates (the candidates tab). Closing it takes the mark off the address, so a reload doesn't show it again. Viewers, and interviews copied from templates, don't get it.

## The interview page

An interview's page has three tabs, in its side menu as on a company's pages ([Companies](companies.md)):

| Tab | Who sees it | What it holds |
|---|---|---|
| **topics** | Every member | What the interview adds up to for each candidate (total questions, time per question and the whole interview's minutes, as companies counts them, which follow each change), then the interview's topics and questions, each with its number of questions for each candidate |
| **candidates** | Every member | The candidate list (see [Candidates](candidates.md#the-candidate-list)) |
| **settings** | Owners and admins | Time per question, pass mark, "Mark as hired" and keeping its questions out of the shared question bank, each saved as it changes; the API (`PATCH /interviews/{id}/settings`) changes only the settings sent, so the assistant and AI apps can change one alone |

### Settings

- **Time per question:** a new test starts with its level's: 60 seconds for a basic or medium one, 75 for a hard one, by default (`QUESTION_SECONDS_BASIC`, `_MEDIUM`, `_HARD`, values in the admin zone's Controls). A template's copy gets them at once; a generated test when its questions are ready, the first time only. Adjustable per interview (see [Timing](candidates.md#timing)); a change in Controls reaches only new tests.
- **Pass mark:** 70% by default, from 1 to 100. Grades show green or red against it.
- **Mark as hired:** marks the interview as hired and stops its shareable link at once.
- **Keep these questions out of prepza's shared question bank:** off by default, as the terms (2026-11-08) say: an interview's generated questions may be reused in other companies' interviews, without anything that identifies the company or anyone else. Checking it keeps the interview's questions out from then on (`keep_private` on the interview in companies); questions already reused in other interviews stay there. A change is in the action log (`interview_settings_changed`), and Mira and AI apps can set it (`keep_questions_private`). Today the bank holds only the templates' questions ([Generation](../generation.md)), so the setting records the company's choice ahead of companies' questions joining it.

### Status

Each interview shows its status:

| Status | Meaning |
|---|---|
| new | No candidates yet |
| in process | Candidates invited |
| hired | "Mark as hired" was set on its settings tab |

## Preview

Any company member can preview an interview as a candidate, with the play button on the interview list or page.

- It shows the same timed questions.
- It is free.
- It is kept out of the candidate list.
- Its answers are kept out of the questions' statistics.
- A person starts at most 20 previews an hour, as many as practice rounds (`PREVIEWS_PER_USER_HOUR`, by default).

## Lists and text fields

- Every list loads more as you scroll and renders only what's on screen, however long it gets. A page that fails to load says so with **Try again**, and the list can still load the rest; a list whose first page fails says so too, rather than looking empty (`hooks/use-paged-list.ts`).
- Dates and times show in the visitor's own time zone: the server renders them in UTC, and the browser shows them local as soon as the page runs (`hooks/use-local-time.ts`, `components/local-date.tsx`). A calendar day (an article's update, a statement's review) is the same day everywhere (`formatDay`).
- Every text field stops at the length its service accepts, so nothing is refused on sending. The limits live in the services; `frontend/constants/limits.ts` mirrors them.

| Field | Limit (characters) |
|---|---|
| Title | 70, and at least 3 (`MIN_TITLE_LENGTH`; a test's and a template's title, spaces at either end aside, `prepza_common.titles`) |
| Company name | 45, and at least 2 (`MIN_COMPANY_NAME_LENGTH`: EY and 3M are companies) |
| Topic name | 50 |
| Job description | 10,000 |
| Email | 254 |
| A pasted or uploaded list of emails | 50,000 |
