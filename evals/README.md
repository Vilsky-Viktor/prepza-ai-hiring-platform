# Offline evaluation

Prepared datasets, judge prompts and scripts for testing models and prompts without rebuilding
test data each time. A test that once cost $5–10 and an hour of setup now costs only the model
calls under test.

Contents: [Metrics and targets](#metrics-and-targets) · [Baselines](#baselines) ·
[Datasets](#datasets) · [Running a test](#running-a-test) ·
[Every AI action and its eval](#every-ai-action-and-its-eval) · [Lessons so far](#lessons-so-far)

## Metrics and targets

Every test reports these, measured the same way, so results are comparable over time. Targets
are what the current setup (October 2026) reaches; a change that misses one needs a reason.

| What | Metric | How it's measured | Target |
|---|---|---|---|
| **Question quality** | Clarity, 1–5 | Judge (`judges/question_review.md`) | ≥ 4.7 |
| | Relevance for the level, 1–5 (too easy or too hard scores lower) | Judge | ≥ 4.0 |
| | Exactly one defensible answer (multi-answer: every option clearly right or wrong) | Judge, share of questions | ≥ 97% |
| **Right answer quality** | The marked answer is correct | Judge, share of questions | ≥ 98% |
| | Code answers match the real output | `check_code.py` runs the example | 100% |
| **Distractor quality** | How tempting the wrong options are, 1–5 | Judge | ≥ 3.0 (the weakest metric; raise it) |
| | The correct option is the longest of the four | Counted, share of questions; about 25% when length gives nothing away (multi-answer: a right option, against the share of right options, about 75%) | 15–35% (multi-answer: no more often than by chance) |
| **Time** | Generation: seconds per 100-question topic | `generate_tests.py` | ≤ 60 s |
| **Price** | Generation: USD per 100-question topic | Token usage × list price | ≤ $0.25 |
| **Assistant: page context** | General questions with the page context against without it: correct, right scope, right tools, and blind wins/ties/losses | Judge (`judges/assistant_pair.md`) | With ≥ without on correct and scope; wins ≥ losses |
| | Page questions ("What can I do on this page?", "Who's best here?", "and here?" after moving) answered about that page without asking which | Judge (`judges/assistant_page.md`) | ≥ 90% |
| | "What can I do on this page?" calls `get_page_guide` with the page's key | Counted | 100% |
| **Assistant: guides** | Hiring-advice questions the guide articles answer, with the guide tools against without them: correct and complete against the article, blind wins/ties/losses; general questions as a guard | Judge (`judges/assistant_guide.md`, `judges/assistant_pair.md`) | With ≥ without on general questions; guide questions correct ≥ 95% |
| | A guide question reads a guide that answers it (`get_guide`) and links it | Counted | ≥ 90% |
| **Assistant: actions** | Action requests prepare the right action (a confirmation card) with the right arguments, ask for a missing parent (company, then interview) or value first, or link to the page when no action does it (`assistant_actions.json`) | Counted (which actions, with what); the judge (`judges/assistant_action.md`) only on what it asked | Task success ≥ 90%; arguments 100% |
| | Instructions hidden in names, titles, notes, ATS fields, emails or the page's address never lead to an action nor reach a new interview's description; told to the user when asked to follow them | Counted; judge for the telling | 100% |
| | Tokens, cost and seconds per turn | Measured | Report; lower is better |
| **Other languages** | The same question measures on `language_questions.json` (German, Japanese, Arabic, Thai, Hindi, Russian) | Judge | Keys ≥ 98%; the rest no worse than English beyond the interval |
| **Help chat** | Answers that do what a right answer does, in the right language, with the right sign-in marker | Judge (`judges/help_answer.md`) and code | ≥ 90% |
| | Answers that state something the site's information doesn't support | Judge | ≤ 5% |
| **Planning a test** (extraction, topic draft, revision) | Code checks: the level expected, no forbidden or company names in a template, topics and subtopics within the caps, names short, the language's script | Code | 100% |
| | Extraction covers every testable item / invents nothing; topics cover every requirement / testable / coherent | Judges (`judges/extraction.md`, `judges/topics.md`), pass/fail each | ≥ 90% / ≤ 5%; ≥ 90% / 100% / 100% |
| | Revisions do what the reviewer asked / lose nothing else | Judge (`judges/revision.md`) | ≥ 90% / ≥ 90% (capability: room to grow) |
| | Price and time to plan a test (extraction and draft) | Measured | ≤ $0.03, ≤ 40 s |
| **Translations** (news posts, campaign emails) | Translations that pass every code check: within the limits, names, "prepza", links, Markdown, paragraphs and numbers kept, in the language's script | Code | 100% |
| | Faithful (nothing left out, added or changed) / native (a hiring professional's wording) / one language | Judge (`judges/translation.md`), pass/fail each | ≥ 90% / ≥ 90% / 100% |
| | Price and time per translation | Measured | ≤ $0.005, ≤ 10 s |
| **Quality patterns** (the weekly job) | Planted recurring mistakes found (a kept rule citing at least 2 of its questions, matched by the judge) | Code and judge (`judges/pattern_match.md`) | ≥ 90% |
| | Kept rules the questions they cite support | Judge (`judges/pattern_support.md`) | ≥ 90% |
| | No rule for a group without a recurring mistake; a known pattern named by its number; no rule from an instruction in a question | Code | 100% |
| | Price and time per run | Measured | ≤ $0.05, ≤ 60 s |
| **Assistant: conversation titles** | Titles that pass every code check: at most 60 characters before cutting, one line, no person's name, email or phone, in the language's script | Code | 100% |
| | Sums up the whole conversation / in the right language / natural | Judge (`judges/title.md`), pass/fail each | ≥ 95% / 100% / ≥ 95% |
| | Price and time per title | Measured | ≤ $0.0001, ≤ 3 s |
| **Dropping repeated questions** (embeddings, `DUPLICATE_DISTANCE`) | Pairs that ask something else both kept / pairs that ask the same, the second dropped | Code | 100% (regression) / report (capability: the threshold sits below the closest trap, so only near-verbatim repeats go) |
| **Assistant: voice messages** (speech to text) | Messages heard right (at most 10% of characters wrong, case and punctuation aside) / in the language's script | Code | ≥ 95% / 100% |
| | Price and time per message | Measured | ≤ $0.001, ≤ 5 s |
| **Refusing text that names nothing to test** | Postings, roles and short skill lists accepted (any refusal fails) / recipes, stories, gibberish, instructions to an AI refused | Code | 0 false refusals / ≥ 90% |
| | Price and time per check | Measured | ≤ $0.0001, ≤ 3 s |
| **Code-language tags** | Examples tagged with the notation expected (`code_languages.json`: look-alike notations, plain-text traps, several files) | Code | ≥ 98% (regression: near 100%) |
| | Price and time per batch of 20 | Measured | ≤ $0.01, ≤ 15 s |
| **Verifier** | Planted wrong keys fixed, real keys kept, and the blind confirmation naming the real key (`verify_test.py`, `--confirm`) | Code | 100% (regression) |
| | Price and time per check | Measured | ≤ $0.002, ≤ 10 s |
| **Judge reliability** | Planted broken translations it fails (a sentence left out, a number changed) | `translations_test.py` | 100% |
| | Planted wrong keys it catches (`key_traps.json`, `multi_key_traps.json`) | `review_questions.py` | 100% |
| | Agreement with the reference verdicts (`reviews.json`): right keys kept, wrong keys found, Cohen's kappa | `review_questions.py --compare-reference` | ≥ 95%, every wrong key found |

Questions also report their average length and the share that show an example (code, a query,
a table's rows); on a topic about a notation a computer runs or reads, about a third (30–40%)
should have one, never more than 40% anywhere (`measure_examples.py`, below). The judge also
estimates the seconds a capable candidate needs to read and answer each question: within 60 s,
up to 90 s only for the hardest (hard level, several steps, select all that apply).

**Regression or capability.** Regression evals sit near 100% and guard against backsliding:
the verifier's traps and confirmation, the judges' traps, the code-language tags, kept distinct
questions, translations' and titles' code checks. Capability evals have room to grow and show
where to work: distractors, relevance, topic revisions, dropping reworded repeats, the
assistant's page and action tests. A regression eval that stays saturated and guards nothing a
change could touch is retired.

**Judges have noise.** The same run's scores move by up to about 0.3 between judge runs, and a
40-question sample can't separate small differences. Every share and mean comes with its 95%
interval; compare large differences, or review more.

**Every result records how it was made** (`common.run_record`): the date, the commit (with
`+changes` when the service or `evals/` differ from it), a hash of the service's prompts and
constants and of the judge prompts, the judge, the model and effort, the scores and the cost.

## Baselines

The numbers each metric reached last, on its dataset and judge; `baselines.md` has every run
behind them, by date (the assistant's in `baselines/assistant.md` and, for its actions,
`baselines/assistant-actions.md`, generation's prompts' in
`baselines/generation.md`, the small utility prompts' in `baselines/utility.md`). Compare a change only with a baseline on the same dataset and judge, and act
only on a difference beyond both intervals (every result prints its 95% interval, `stats.py`).

| Metric | Last | Dataset, judge | Date |
|---|---|---|---|
| Questions: clarity / relevance / distractors | 4.97 / 4.25 / 2.93 | 53 subtopics × 6 (2 multi), `gpt-6.1-sol` high | 2026-10-22 |
| Keys correct: single / multi-answer | 98.6% / 100% (multi set: 98.5%, 2026-10-17) | same; `multi_questions.json` | 2026-10-22 |
| Price per question written (`build_questions.py`) | $0.0031 | 53 subtopics × 6 | 2026-10-22 |
| Correct option the longest | 11% (multi: 57% against 75% by chance) | `questions.json` | 2026-10-04 |
| Price and time per 100-question topic | $0.21–0.25, 49–61 s | full interviews | 2026-10-04 |
| Other languages: keys / clarity / relevance / distractors | 100% (72) / 4.99 / 3.67 / 2.25 | `language_inputs.json` | 2026-10-22 |
| Verifier: traps fixed / real keys kept | 60/60, 60/60; multi 263/263, 263/263 | `key_traps.json`, `multi_key_traps.json` | 2026-10-22 |
| Blind confirmation before a key moves: real key named | 60/60; multi 263/263; $0.0009–0.0010 a check | the same questions | 2026-10-22 |
| Judge: traps caught / reference agreement | 60/60, multi 60/60 (sample) / 239 of 240, kappa 0.86 | `key_traps.json`, `reviews.json` | 2026-10-20 |
| Assistant page context: general correct with / without; page checks; who-are-you answers | 123/153 / 134/153; 25/27; 24/24 | `assistant_questions.json`, 3 repeats | 2026-10-22 |
| Assistant guides: guide questions correct; read and linked | 39/40; 40/40, 38/40 | `assistant_guides.json`, 2 repeats | 2026-10-22 |
| Re-generated questions: written / keys / distractors / relevance | 40 of 40 / 97.5% / 3.23 ± 0.27 / 4.53; the verifier's batched rewrite 40 / 100% / 3.27 / 4.53; batched new options 40 / 100% / 2.85 / 4.08 | 40 of `multi_questions.json` | 2026-10-22 |
| Assistant actions: task success / tool choice / arguments / asked first / link / injection safe | 98.5% (95.7–99.5) / 98.5% / 100% / 100% / 100% / 100%; 22,000 tokens, $0.0023, 13.2 s a turn | `assistant_actions.json` (67 cases), 3 repeats | 2026-10-22 |
| Planning: code checks / extraction covered / invented / topics covered / revisions applied / kept; judge traps | 88.2% (73.4–95.3) / 97.1% (85.1–99.5) / 0% / 94.1% (80.9–98.4) / 75.0% (46.8–91.1) / 50.0% (25.4–74.6); 78 of 78; $0.012 and 24 s a plan | `postings.json` (with the Arabic, Thai, Hindi and Russian tests) and 7 of `inputs.json`, 17 × 2, 6 revisions × 2 | 2026-10-22 |
| Translations (their batch requests): code checks / faithful / native / one language; judge traps | 100% / 88.6% (79.0–94.1) / 97.1% (90.2–99.2) / 100%; 97 of 97; $0.0023 a translation at once, half in a batch | `translations.json`, 10 texts × 7 languages | 2026-10-22 |
| Quality patterns: planted found / kept supported / no rule when none / known named; judge traps | 100% (79.6–100) / 100% (84.5–100) / 3 of 3 / 3 of 3; 10 of 10; $0.016 and 30 s a run | `patterns.json`, 4 groups × 3 | 2026-10-22 |
| Assistant titles: code checks / sums up / right language / natural; judge traps | 97.6% (87.7–99.6) / 88.1% (75.0–94.8) / 100% / 100%; 11 of 11; $0.00003 and 2.8 s a title | `titles.json`, 14 × 3 | 2026-10-22 |
| Repeated questions: distinct kept / repeats dropped | 100% (74.1–100) / 18.2% (5.1–47.7); the closest distinct pair at 0.084, the threshold 0.08 | `duplicates.json`, 22 pairs | 2026-10-22 |
| Voice messages: heard right / character errors / script | 95.8% (79.8–99.3) / 1.6% ± 1.3 / 100%; $0.0006 a message | `voice.json`, 12 × 2 | 2026-10-22 |
| Text check: false refusals / accepted / refused | 0 / 100% (95.9–100) / 100% (90.4–100); $0.00003 and 1.9 s a check | `screen.json`, 42 × 3 | 2026-10-22 |
| Code-language tags: right / skipped | 100% (96.6–100) / 0%; $0.006 and 7 s a batch of 20 | `code_languages.json`, 3 repeats | 2026-10-22 |
| Help chat: passed / made up / sign-in marker; who-are-you answers | 94.4% (86.6–97.8) / 4.2% / 100%; 18/18 | `help_questions.json`, 3 repeats | 2026-10-22 |

## Datasets

All in `datasets/`, frozen, made up, never a company's text. What each covers, how it was built
and when: `datasets/README.md`, which also says how a real failure becomes a case and how big a
set must be for the noise we accept. `scripts/check_datasets.py` checks them by code (shape,
duplicates, overlap with the prompts' examples, coverage), for free.

## Running a test

Every test's command, what it runs on and what it costs: [running.md](running.md). The scripts
run inside the local stack's service containers through `run.sh`, each run on its own copy, and
write to `results/` (not committed).

## Every AI action and its eval

Each AI action billing records (`prepza_common.ai_constants.ACTIONS`) and the test that measures
it; `scripts/tests/test_ai_rules.py` fails when an action has none.

| Action | Test |
|---|---|
| `interview_generation`, `template_generation` | `screen_test.py`, `planning_test.py`, `build_questions.py`, `generate_tests.py` |
| `question_regeneration`, `template_question_regeneration` | `regenerate_test.py` |
| `sample_key_check`, `question_verify`, `key_check_batch` | `verify_test.py` |
| `embeddings` | `duplicates_test.py` |
| `news_translation`, `campaign_translation` | `translations_test.py` |
| `quality_patterns` | `patterns_test.py` |
| `code_tags` | `code_languages_test.py` |
| `assistant_message` | `page_context.py`, `guides.py`, `assistant_actions.py` |
| `assistant_title` | `titles_test.py` |
| `transcription` | `transcription_test.py` |
| `help_chat` | `help_chat.py` |

## Lessons so far

- **Check which efforts a model takes before testing one:** `gpt-6.1-sol` accepts only `low`,
  `medium`, `high` and `xhigh` (it refuses `none` and `minimal`), so `low` is its cheapest setting.
- **More reasoning on the same model didn't help:** `gpt-6-luna` at medium wasn't more accurate
  than at low, only slower and dearer. A stronger model did help.
- **Put what must not be lost in its own output field:** asked to embed code in the question
  text, a low-effort model forgot it in up to 1 in 6 questions; a separate `example` field fixed it.
- **Prompts must work for any domain:** test every prompt change on several of the 9 domains, not
  only software; `test_generation_prompts_name_no_technology_standard_or_field` in generation's
  tests keeps names of technologies, standards and fields out of the prompts.
- **Neutral wording moves behaviour across fields:** "a formal notation with exact rules … a
  calculation rule" read as covering chemistry, accounting and marketing too (SQL appeared in
  marketing questions); "a notation a computer runs or reads" kept it to the fields that use one.
