# Templates and free practice

Templates are ready-made interviews by role, made by prepza's superadmins (see [Admin zone](admin-zone.md#templates)). They are the question bank: companies copy them into interviews, and people preparing for a role practise free on their practice questions.

## The question bank

Each template question belongs to one pool, fixed when it's made and never changed (`questions.pool`):

| Pool | Used by | A new template's topic |
|---|---|---|
| **practice** | Free practice and the role pages' sample questions only; public, shown with its answer | 30 (`PRACTICE_QUESTIONS`) |
| **company** | Company interviews copied from the template, and the bank new generations reuse from; never shown publicly | 60 (`COMPANY_QUESTIONS`) |

- A new template's topic (`helpers/sets.py` `new_template`, `helpers/pools.py`): questions reused from the bank are company questions; of the fresh ones, 30 go to practice and the rest to companies. With 90 a topic and at most half reused, there are always enough fresh ones for 30 practice.
- No question moves between pools. A wrong answer key or a flagged question is still fixed or replaced, and the fix reaches the copies.
- Company interviews' own questions have no pool: they're never shared and never in the bank.
- Templates made before the pools got them from their old stages (library migration 0027): revealed questions are practice, private and retiring ones company. Their counts vary, so a topic may be short of either; the admin zone's template page shows each topic's counts and tops them up (below).
- A new topic's 30 practice questions hold its share of "select all that apply" questions (`MULTI_ANSWER_PERCENT`, see [Generation](../generation.md#select-all-that-apply)), and on a topic about material in a formal notation (code, queries, commands, settings files) its share of questions with an example: 30–40% of the topic, 9–12 of the practice questions and 18–24 of the company ones (see [Generation](../generation.md#examples-and-their-language)).
- An interview's copy of a question remembers its original, so its answers count there too, and a fix to the original reaches the copy (see [Fixes](../generation.md#fixes)).
- An interview's copy of a practice question (only copies made before the pools can be one) is no longer given to candidates.

Template topics keep embeddings, so proven questions on similar topics can be found and reused by new interviews (see [Generation](../generation.md#reusing-proven-questions)). Template topics without an embedding get one from:

```bash
docker compose exec generation uv run --no-sync python -m app.jobs.embed_templates
```

## Adding questions

A superadmin adds questions to a template from its page in the admin zone (see [Admin zone](admin-zone.md#templates)). Both are a background run of generation's (`POST /generate/superadmin/templates/{id}/top-up` and `…/additions`, progress at `…/additions/latest`), one at a time per template, written like a template's questions (the topic's title, subtopics, level and language; the same answer-key checks and de-duplication, also against the topic's own questions) and counted toward generation's daily limit:

- **Top up**, offered while a topic is short of 30 practice or 60 company questions: writes exactly what each side lacks ("Every topic already has its practice and company questions." otherwise).
- **Add questions**, any time: a number for every topic, 30 by default, in steps of 3, at most 90 a run (generation checks it), a third to practice and the rest to companies.

Each side of a top-up or an addition gets its share of "select all that apply" questions and, on a topic about material in a formal notation, of questions with an example, as a new topic's pools do.

The practice side is always freshly written; the company side may take proven bank questions, at most half of what it adds. Added questions go after the topic's last (library's `POST /internal/templates/{id}/questions`); interviews already copied from the template keep theirs, and new copies get them. A run that fails leaves the template as it was.

## Copying a template

- Copying a template into a company's interview takes only its company questions.
- A topic with fewer than 10 company questions is left out (`MIN_COPY_QUESTIONS`).
- A template with no such topic can't be copied, and companies' template list leaves it out (`GET /templates/copyable`).
- Practice and the admin zone list every template.

## Slugs

Each template has a readable slug made from its title when it's saved: `backend-developer`, then `backend-developer-2`, and so on.

- The slug never changes on rename, so its practice page's URL stays the same.
- `GET /templates/{id or slug}` finds a template by either.
- The public `GET /templates/{id or slug}/sample` gives up to 5 of its practice questions with answers, spread across its topics. It never gives company ones.

## Free practice

Free practice (`/practice`) gives people preparing for a role practice interviews on the templates' practice questions, timed unless they choose otherwise.

- 10 questions a topic, about 1 in 10 of them "select all that apply" (scored as in [Interviews](interviews.md#questions)), each with the seconds a company's new test of the template's level starts with (60 for basic and medium, 75 for hard, by default).
- Before a round, beside its start button, the person picks the time per question: the standard seconds, double, or no time limit (WCAG 2.2.1: practice measures nothing, so whoever needs it gets more time or none). Rounds decides the options (`PRACTICE_TIMINGS` in `services/rounds/src/rounds/constants/practice.py`), sends them with the round's size (`GET /rounds/practice/{template_id}/size`, worked out from the level's current seconds) and takes the choice when the round starts (`POST /rounds/practice/{template_id}` with `{"timing": "standard" | "double" | "untimed"}`; anything else is a 422). A round with double time or none doesn't count in the questions' statistics, as repeat rounds don't.
- At the end: the grade and every right answer; for a "select all that apply" question, also the options ticked, which were right, and its points ("2 of 3 right options · 0.67 of 1 point").
- Each template keeps the person's rounds and progress. Their rounds (`/practice/history/<template id>`) are listed newest first, 20 at a time, and more load as the list scrolls (`GET /rounds/practice/{template_id}/rounds?offset=&limit=`).
- Signed in, the practice list marks each test after its title, from the person's latest round on it: a blue check while in progress, the results' green double check once every topic's questions are all answered, nothing before the first answer. Its tooltip says how many topics are answered to the end of all ("In progress: 2/7 topics"). Rounds decides the status, by the same count as the test page's per-topic progress (`GET /rounds/practice/statuses`, one entry per practiced test); a round that ended with questions left unanswered stays in progress.
- At most 20 rounds an hour per person (`PRACTICE_ROUNDS_PER_HOUR`, by default).

A practice page is in English and in its template's language only (see [Public site](site.md#skills-tests-by-role)).

### "Hiring for this role?"

A practice test's page and its result both offer the template for hiring. The button opens `/companies/templates/<template id>`, which:

- goes straight to the test in the user's only company,
- or lists their companies, or lets them create one, to choose where it's copied.

## How it's built

Library's routes and event handlers call services (`src/library/services/`), which open each transaction and pass it to the repositories; generation, the other services, Firebase and Redis are called outside it. A question's replacement (its old content kept as a revision, the new content, its owner's notification and the `question.fixed` event for its copies) is one save, and so is each batch of copies fixed after it, with their companies' notifications. A new news post is saved with its notification for everyone, and an edit with its translations dropped. When an account is deleted, library's own rows and the note that replays the deletion after a restore (`erasures`) are one save, made once every other service has deleted the account; a failure keeps both and the sign-in, so the user's retry does it all again.

## Related pages

- [Public site](site.md#skills-tests-by-role): the skills test page each template gets.
- [Generation](../generation.md#generation-settings): `TEMPLATE_QUESTIONS_PER_TOPIC` and the other values that shape a generation, set in the admin zone's Controls.
