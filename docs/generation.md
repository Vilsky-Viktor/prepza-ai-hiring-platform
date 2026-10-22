# Generation and question quality

How prepza turns a job description into an interview, how questions are reused and checked, and the settings that shape it. The `generation` service runs it; the `library` service stores the results (see [Architecture](architecture.md)).

- [Generation pipeline](#generation-pipeline)
- [Reusing proven questions](#reusing-proven-questions)
- [Question quality](#question-quality)
- [Generation settings](#generation-settings)
- [Models](#models)
- [Rate limits](#rate-limits)

## Generation pipeline

The pipeline is a LangGraph graph (`app/services/graph.py`); the diagram below is drawn from the compiled graph by `scripts/graph-diagrams.sh`, and a unit test fails when it no longer matches the code. Dotted arrows are conditional edges.

<!-- graph:generation -->
```mermaid
graph TD;
	__start__ --> extract_info;
	collect_results --> fill_topics;
	extract_info --> generate_topics;
	find_reused -.-> collect_results;
	find_reused -.-> generate_questions;
	generate_questions --> merge_questions;
	generate_topics --> human_review;
	human_review -.-> find_reused;
	human_review -.-> revise_topics;
	merge_questions --> collect_results;
	revise_topics --> human_review;
	fill_topics --> __end__;
```
<!-- /graph:generation -->

- `extract_info`: reads the job text for its title, requirements and level (cached per input).
- `generate_topics`: drafts the topics and their subtopics (cached per input).
- `human_review`: pauses (`interrupt`) until the company keeps topics, edits them inline or asks for a revision in free text; `revise_topics` rewrites the draft and sends it back to review, and approval moves on.
- `find_reused`: takes proven questions from similar public templates (pgvector).
- `generate_questions`: one parallel branch (`Send`) per call of each subtopic writes questions with their options, for what reuse left; with nothing left to write, the run goes straight to `collect_results`.
- `merge_questions`: waits for every branch and keeps, per topic, one list of distinct questions (duplicates by meaning dropped with embeddings).
- `collect_results`: each topic's questions, reused ones first.
- `fill_topics`: tops up any topic short of its size, of each kind; the questions are then saved to the library.

- The graph is run by the generation worker (`app/worker_main.py`) as Cloud Tasks jobs.
- The graph is checkpointed in Postgres, so a failed run can be retried from where it stopped.
- Companies hears how an interview's generation ends through events: `generation.completed` stores its questions and title, `generation.failed` (a failed run, or one the sweeper finds stuck) marks it as failed until a retry, and `generation.cancelled` removes it. Interview lists read only what these stored and never ask generation; an interview's own page asks once, in case an event hasn't come yet, and shows what companies knows when generation can't answer.
- The title the model gives is cut to 70 characters (`MAX_TITLE_LENGTH`), what editing a title allows, so saving the questions never fails on it.
- A generation can be cancelled at any step.
- A generation makes up to `GENERATION_CALLS_AT_ONCE` AI calls at once (24 by default); so do the other jobs' fan-outs (translations into the missing languages, the key self-checks, the sample key checks), and every LLM call of the pipeline shares one rate limit across the API and all workers (`GENERATION_CALLS_PER_SECOND`, 24 a second by default, counted in Redis). Both are values in the admin zone's Controls (see [Admin zone](features/admin-zone.md#limits)), read within 30 seconds of a change; OpenAI allows our account 5,000 requests and 1M tokens a minute, and a full template uses about 380k tokens. The help chat isn't held to the rate, so it stays responsive during big generations.
- An LLM call silent for 5 minutes has hung (`LLM_TIMEOUT_SECONDS`) and is tried again at most twice (`LLM_MAX_RETRIES`): quick failures recover, and a stuck call gives up well within a run's 25 minutes.
- Regenerating one question has 110 seconds to write it (`REGENERATE_TIMEOUT_SECONDS`), under the 120 companies waits; past that the old question stays and the company is told to try again, so a retry never makes two replacements.
- `generation.completed` carries the test's level, which gives a generated test its level's seconds a question (see [Interviews](features/interviews.md#settings)).
- The worker also translates news posts into every language, with its own model (`TRANSLATION_MODEL`), as a `translate-news` job (see [Admin zone](features/admin-zone.md#news)).

### Prompts

Every prompt that writes questions or their options (`questions.py`, `answers.py`, `regenerate.py`) starts with the same generic role, an assessment designer who writes questions for skills tests in any field (`QUESTION_WRITER_ROLE` in `app/prompts/question_rules.py`), in a system message that holds all the instructions and changes with no call, so OpenAI's prompt cache keeps it; the call's own values (counts, language, level, topic, subtopic) and the topic's existing questions, tagged as data, come after in the request message. The topic draft, its revision and the extraction have their own role (an assessment designer who plans what a test covers, or reads job postings for it); the company's posting, its requirements, the current topics and the reviewer's instructions come in the user's message, tagged and read as data. Every key check (the verifier's, the blind confirmation before a key moves, and a new multi-answer question's self-check) runs with a reviewer's role in its system message and the question and options tagged in the user's; the batched checks ask the Batch API for the same strict schema. Prompts work for any field: they name no technology, standard or field (the kinds of material are described generically, such as "a lookup over stored records" or "the standard, law, framework or version in use"), and questions are driven by the topic, subtopic and level, never the job's role. A unit test keeps a list of such names out of every generation prompt (`test_generation_prompts_name_no_technology_standard_or_field`).

### Topics

The topic draft has up to `MAX_TOPICS` main topics (set in Controls, see [Generation settings](#generation-settings)), that number included: one for each distinct subject the job's requirements cover. Distinct subjects are merged only when there are more of them than the limit.

### Question length

A capable candidate at the test's level reads a question, its example and its four options and answers within one minute, also when reading in a language that isn't their own; only the hardest (hard level, several steps of reasoning, or select all that apply) may take up to a minute and a half, never more. Every prompt that writes or rewrites a question says so (`READING_RULES` in `app/prompts/question_rules.py`):

- the question at most 40 words (50 at the hard level), in one or two short, plain sentences, with only what the answer depends on;
- an example at most 8 short lines, and only the lines the answer depends on: no setup or boilerplate that doesn't change it, short names, the fewest records or values that still make the case, and one piece (one file) unless the question is about several working together;
- a scenario or worked example with only the details the answer depends on;
- each option at most 10 words.

A question is hard because of the reasoning it needs, never because of its length.

A question that still comes back far over is dropped, and the topic's top-up writes another (`readable` in `app/helpers/questions.py`): its sentences over 400 characters (`MAX_QUESTION_CHARS`), its example over 10 lines (`MAX_EXAMPLE_LINES`), or an option over 100 characters (`MAX_OPTION_CHARS`). A rewritten question (a member's or the quality checks') is held to the same limits.

### Examples and their language

On a topic about material written in a formal notation (instructions a machine runs, a lookup over stored records, commands, settings files, text-matching patterns), about a third of the questions show an example and ask what it produces, what it does, why it fails or which change fixes it. It's held both ways (`prepza_common.examples`):

- each question call is asked for its share: exactly a third of its questions with an example when the subtopic is about such material, otherwise none (`QUESTIONS_REQUEST`);
- each topic keeps 30–40% with an example (`MIN_EXAMPLE_SHARE`, `MAX_EXAMPLE_SHARE`; 27–36 of a template's 90), and each of a template's pools its share too (9–12 of the 30 practice questions, 18–24 of the 60 company ones, `pool_share`). A topic counts as being about such material when at least 15% of its questions came with an example in a notation the site colors (`FORMAL_SHARE`; a table's rows are `text` and don't count). Other topics, such as nursing or a language for travel, are never asked for examples and only held to the 40% ceiling;
- the top-up writes each kind that's missing apart (single- or multi-answer, with an example or without), and the last round makes up anything still missing with single-answer questions without one, so a topic isn't failed for its mix. A superadmin's addition gives each pool its share the same way, and a regenerated question shows an example exactly when the one it replaces did.

The model gives a question's example apart from its sentences, with the example's notation (`example_language`: one of `CodeLanguage` in `app/constants/code.py`, shiki's names, or `text` for a table's rows or plain prose). One that shows several files gets the notation most of it is written in, never `text`. The stored question is its sentences, then the example in a fenced block tagged with it ("```python", `with_example`), so the site shows it in an editor with that language's colors (`components/code-editor.tsx`).

Questions saved before examples were tagged get their language once from a job, which asks the model in batches of 20 (`TAG_BATCH_SIZE`) and tags each question's first untagged block through library (`GET /internal/code/untagged`, `PUT /internal/code/languages`). It only picks questions whose first block has no language, so running it again is safe. With `--text` it checks the blocks tagged `text` instead (`?text=true`, page by page): one the model names a notation for gets it (an example of several files used to be `text`), and genuine plain text, such as a table's rows, stays as it is:

```bash
docker compose exec generation uv run --no-sync python -m app.jobs.tag_code_languages
docker compose exec generation uv run --no-sync python -m app.jobs.tag_code_languages --text
```

### Select all that apply

About 1 in 10 questions of every topic (`MULTI_ANSWER_PERCENT`, 10% by default, a value in the admin zone's Controls) are "select all that apply": 4 options of which 2 or 3 are right, never all 4. The rest have one right option and three wrong ones. Each topic's calls are asked for their share of them, and the top-up writes any that are missing; when a topic still lacks them after its last top-up, single-answer questions make up the rest. One run keeps the share it started its questions with (`multi_share` in its state). Each option of a multi-answer question must be clearly right or wrong by itself, under conditions the question states (`MULTI_ANSWER_RULES` in `app/prompts/question_rules.py`). Regenerating a question keeps its kind.

Every new multi-answer question is checked before it's kept (`app/services/key_self_check.py`): the verifier answers it blind (no option marked, a new order) and names any condition the question leaves unstated that decides an option. A question whose blind answer differs from its key, or that leaves a condition open, is dropped and the top-up writes another. Single-answer keys already reach the target without it. Measured key accuracy: 98.5% for multi-answer questions and 99% for single-answer ones (see [evals/README.md](../evals/README.md)). The share is to go up to 0.2 once real answers confirm the multi-answer keys.

Each candidate's draw from a topic, and each practice round's, has the same share of multi-answer questions, made up with the other kind when a topic has too few. How they're scored is in [Interviews](features/interviews.md#questions).

### Cost

Every AI call is recorded by `prepza_common.ai_usage.record`: its action (`ACTIONS` in `prepza_common.ai_constants`: `interview_generation`, `template_generation`, `question_regeneration`, `question_verify`, `embeddings`, …), model, tokens and cost in USD at the prices in `ai_constants.MODEL_PRICES` (cached input at its own price, Batch API calls at half), who it was for and whether it ended `ok`, `cut` or `failed`. In generation, a run (a generation's topic draft or its questions, one regenerated question, a quality check) records once per model when it ends, failed runs too; a call that got no answer counts with estimated tokens. A retry or a resume records its own.

Each record is one log line ("AI used: …", the `prepza_ai_spend` metric and the **prepza AI spend high** alert) and an `ai.used` event that billing stores for the admin zone's AI costs page (see [Credits and payments](features/billing.md#ai-usage-and-limit-hits)).

## Reusing proven questions

The question bank is the superadmins' templates' company questions; their pools (practice and company) are in [Templates and practice](features/templates-and-practice.md#the-question-bank). Practice questions are public, so they're never reused.

- Reused questions fill at most half of a new interview's topic.
- Only proven company questions qualify: from templates of the same level and language, answered at least 5 times, never flagged.
- Template topics keep embeddings, so proven questions on similar topics can be found (pgvector).

## Question quality

### Before an interview is ready

Before a new interview or template is ready, the verifier checks one random answer key a topic, and fixes or replaces what's wrong (`KEY_CHECKS_PER_TOPIC`, about $0.001 a check). Every new multi-answer question has also passed its own check as it was written (see [Select all that apply](#select-all-that-apply)).

A company's owners and admins can also mark a question's answer wrong in one click, which sends it to the verifier at once.

### From answers, votes and reports

Rounds publish every answer. Library keeps per-question stats (answers, correct, picks per option) next to thumbs and reports, and flags a question when they show a problem.

- An answer re-checks a question only once the question has been shown 30 times, as answer-based flags need that many.
- Votes, reports and finished topics re-check it every time.
- An answer event missing a field is logged and dropped rather than retried forever.
- A question is flagged once, however many reviews run at the same moment (an answer and its finished topic): the flag is saved only if it's still what the review read, so one notification goes out and the verifier gets one request. A member marking the answer wrong twice at once is sent once too.

| Flag | When | What the verifier does |
|---|---|---|
| `wrong_key` | 2 "wrong answer" reports, or a wrong option picked more than the marked one (for a multi-answer question, more than the right option ticked least often; after 30 answers) | Checks the key through OpenAI's Batch API (half price, every 10 minutes; a batch that expires or fails keeps the results it has, and only the rest go out again; checks a finished batch left without a result are made at once, at most 20 a run, the rest in the next batch): keeps the question, moves the key (for a multi-answer question, to another set of 2 or 3 right options), or replaces it. The check sees the question, its options and the reports' reasons, never how often each option was picked (the popular answer can be wrong). A key moves only when a second, blind check (no option marked, a new order) names the same option (or the same set); otherwise the question is replaced, so no future candidate is marked on an uncertain key |
| `rewrite` | 2 "unclear", "hard to read" or "off topic" reports, 3+ dislikes at twice the likes, or ≤ 15% correct | Writes a new question in its place, of the same kind and with an example when the old one had one, told what users reported: for "hard to read", simpler wording, a cleanly laid-out example with only the lines it needs, tagged with its notation; for "unclear", every condition stated; for "off topic", on the topic (`REPORT_GUIDANCE` in `app/prompts/regenerate.py`) |
| `weak_options` | A wrong option almost nobody picks, or ≥ 95% correct | Writes new options for the same question |

For a multi-answer question, "correct" is the share of the question's point the answers earned (2 of 3 right options ticked and no wrong one: 0.67), so "too hard", "too easy" and the strong/weak separation read its average points as a single-answer question's share right. Each ticked option counts as a pick.

### Fixes

- Fixes happen in place, so a topic's size never changes.
- The replaced version is archived with its stats and feedback; the new one starts its own, and an answer still arriving for the old text isn't counted for it.
- A fix (the verifier's, a member's "wrong answer" mark sent to it, or a superadmin's "Fix now") applies to candidates who start after it. Each session keeps its own copy of the questions, so candidates who already answered keep their answers, scorecard and grade as they were; nothing marks past answers again.
- A fixed template question fixes its copies in companies' interviews too, the same way: every copy that still holds the original's content, so not one a company changed or one fixed on its own. Each company gets the "question fixed" notification. A template question rewritten without a flag leaves its copies as they are.
- A replacement question must differ in meaning from every question already in the topic, checked by embeddings like the pipeline's duplicate step.

Superadmins see flagged and replaced questions on the admin zone's Questions tab, under Flagged and Replaced (see [Admin zone](features/admin-zone.md#questions)).

### Patterns from bad questions

Once a week (Mondays, 05:00 UTC, `/internal/schedules/patterns` on the worker) generation turns the past week's flagged and replaced questions into general rules for a superadmin to review, without one company's questions ever reaching another's prompts.

- It reads them through library's `/internal/questions/signals`, which answers generation's service token only (any other service gets 403): each question's text, options, answer stats, the number of reports per reason and the thumbs, and what replaced it. No question id, set, company or report comment leaves library. A replaced question comes with the flag it had; revisions kept before flags were kept with them get the flag their stats and feedback give, and an owner's edit of a question nothing was wrong with is left out.
- Questions are grouped by flag; a flag with fewer than 2 is skipped, and the model reads at most 60 a flag, newest first. One call a flag, with a domain-neutral prompt (`app/prompts/patterns.py`) that also lists the flag's known patterns, so a known mistake is counted again rather than reworded.
- A new rule is kept only when at least 2 of the questions show it, it's at most 300 characters, it names no technology, field or role (`DENIED_TERMS`) and has no capitalized word other than at the start of a sentence (a name), and it shares no 6 words in a row with any question, option or replacement it was given. A rejected rule is logged by its reason, never its text.
- Stored: the rule's text, the flag, how many questions showed it (a count only), when it was first and last seen, its status (proposed, approved, dismissed, in use) and who reviewed it when. No question ids or text. A known rule found again adds to its count and last seen; a dismissed one stays dismissed and is never proposed again.
- Each flag is read once a week (a Redis key per flag, kept 6 days), so a retried or repeated run counts no question twice; one run at a time (a lock), and none during the emergency pause. Its AI cost is recorded under its own line, "Question quality patterns".
- Superadmins approve or dismiss the proposed rules on the admin zone's Questions tab, under Patterns (see [Admin zone](features/admin-zone.md#questions)). An approved rule is only a candidate: it's used in generation once an eval shows it helps.
- In production the job is created paused (`infra/terraform/jobs.tf`) until the terms and privacy version that allows it, 2026-11-08, is in force.

## Generation settings

Four values shape every generation. They aren't settings: each starts at its default in `prepza_common.limit_list` and a superadmin changes it in the admin zone's Controls tab ([Admin zone](features/admin-zone.md#limits)), in effect within 30 seconds. A run takes its questions per topic when it starts and keeps them to its end, also through a retry or a resume; a change applies to generations started after it. The topic caps are read when the topics are drafted or revised, and when a review is sent.

| Value | Default | Range | What it sets |
|---|---|---|---|
| `MAX_TOPICS` | 10 | 1–20 | Main topics an interview or template has. The review page follows it; approving more without instructions is refused ("Choose at most {count} topics") |
| `MAX_SUBTOPICS` | 5 | 1–20 | Subtopics per topic; every subtopic is at least one model call. The review page follows it; a topic edited with more is refused ("A topic can have at most {count} subtopics") |
| `INTERVIEW_QUESTIONS_PER_TOPIC` | 70 | 10–500 | Questions per topic of a company's interview, from which each candidate gets a random subset. Public at `GET /api/generate/sizes` (`questions_per_topic`, no sign-in) for the home page's facts |
| `TEMPLATE_QUESTIONS_PER_TOPIC` | 90 | 10–500 | Questions per topic of a template: 30 for free practice and 60 for companies' interviews (library's `PRACTICE_QUESTIONS` and `COMPANY_QUESTIONS`) |

These settings in `.env` trace generation to Langfuse. Terraform doesn't pass them to Google Cloud yet (see [infra/README.md](../infra/README.md#notes)).

| Setting | Default | What it sets |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Off; `https://cloud.langfuse.com` (EU) | Trace generation's AI calls to Langfuse, marked with the environment they come from (`ENVIRONMENT`, as Sentry's reports are), on only with both keys (`prepza_common.tracing`). Each AI run (a generation's pipeline run through LangGraph, a regenerated question, a key check, a translation, ...) is one trace with every call it makes: named by its action and tagged with it and its subject's id (the generation's id for a generation), with no company names, job text or emails in its name or tags; the calls' inputs and outputs are traced. A generation's runs before and after its review share one trace. The assistant and the help chat use the same keys ([Votes in Langfuse](features/assistant.md#votes-in-langfuse)). Nothing goes to LangSmith |

## Models

Each AI task has its own model and reasoning effort. The effort is `none`, `minimal`, `low`, `medium` or `high`; only reasoning models take an effort.

| Task | Model | Effort |
|---|---|---|
| Generation of an interview or template, at any level | `INTERVIEW_MODEL` (`gpt-6.1-sol`) | `INTERVIEW_REASONING_EFFORT` (`low`) |
| Verifier: answer-key checks, at once and in batches | `VERIFY_MODEL` (`gpt-6.1-sol`) | `VERIFY_REASONING_EFFORT` (`medium`) |
| Translating news posts and campaign emails | `TRANSLATION_MODEL` (`gpt-6.1-sol`) | `TRANSLATION_REASONING_EFFORT` (`low`) |
| The weekly quality patterns | `PATTERNS_MODEL` (`gpt-6.1-sol`) | `PATTERNS_REASONING_EFFORT` (`medium`) |
| Tagging the notation of questions' examples (`tag_code_languages`) | `CODE_TAGS_MODEL` (`gpt-6.1-sol`) | `CODE_TAGS_REASONING_EFFORT` (`low`) |
| Help chat (the signed-out assistant) | `HELP_MODEL` (`gpt-6-luna`) | `HELP_REASONING_EFFORT` (`none`, which also lets it take a temperature) |
| In-app assistant | `ASSISTANT_MODEL` (`gpt-6-luna`) | `ASSISTANT_REASONING_EFFORT` (`low`) |
| Assistant's conversation titles | `TITLE_MODEL` (`gpt-6-luna`) | `TITLE_REASONING_EFFORT` (`none`) |
| Assistant's voice messages to text | `TRANSCRIBE_MODEL` (`gpt-4o-mini-transcribe`) | None |

Every service builds its chat models with `prepza_common.llm.chat_model`, which leaves the temperature out at any effort but `none`.

Every generation runs on `gpt-6.1-sol` at low. In testing ([evals/README.md](../evals/README.md)):

- `gpt-6-luna` at high wrote basic and medium questions as accurately, at a fraction of the price but more slowly.
- Its hard questions came out too easy.
- So generation stays on Sol, for one quality everywhere.
- The verifier did as well at low as at medium, and stays at medium.

## Rate limits

Each limit is one of `prepza_common.limit_list.LIMITS`, with its default; a superadmin changes its number in the admin zone's Controls tab (see [Admin zone](features/admin-zone.md#limits)), and generation reads the current one (`limits.limit`). Its window stays as it is.

| Limit | Name | Default |
|---|---|---|
| Generations per account a day | `GENERATION_LIMIT` | 20 |
| Re-generated questions per account a day | `REGENERATION_LIMIT` | 100 |
| New generations and regenerated questions a day for companies that never topped up, together, a ceiling on AI spending; a company that paid isn't held to it, so free sign-ups can't use it up for paying ones | `DAILY_GENERATION_LIMIT` | 100 |
| Revisions in words per topic review; after that, topics are only chosen by checkbox | `MAX_TOPIC_REVISIONS` | 10 |
| Verifier jobs a day for everyone together; a superadmin's "Fix now" isn't counted | `DAILY_VERIFY_LIMIT` | 300 |
| Question reports per user a day (library) | `REPORTS_PER_DAY` | 30 |
| Thumbs (ratings) per user a day (library) | `RATINGS_PER_DAY` | 200 |

Above them all, the daily AI spend cap for unpaid companies and people without a company (`AI_SPEND_UNPAID_DAY`, $15 a UTC day by default): once their AI calls of the day (generations, regenerations, the assistant and the help chat) have cost that much, generating for an unpaid company answers 503 ("AI features are paused for today…") until midnight UTC. Paid companies and prepza's own work (templates, quality checks, news) aren't counted or held to it. Billing adds each call's cost to the day's Redis counter (`spend:ai:unpaid:<date>`) as it stores it; with Redis down, nothing is refused.

A company's new interview passes generation's refusals on to the person as generation gave them (its status, message and `Retry-After`: the account's generations a day, the day's budget, the AI spend cap), and an attempt generation refused or failed doesn't count towards the company's interviews a day.

Email limits are in [Candidates](features/candidates.md#email-limits).
