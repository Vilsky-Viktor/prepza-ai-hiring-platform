# Offline evaluation

Prepared datasets, judge prompts and scripts for testing models and prompts without rebuilding
test data each time. A test that once cost $5–10 and an hour of setup now costs only the model
calls under test.

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

**Judges have noise.** The same run's scores move by up to about 0.3 between judge runs, and a
40-question sample can't separate small differences. Every share and mean comes with its 95%
interval; compare large differences, or review more.

**Every result records how it was made** (`common.run_record`): the date, the commit (with
`+changes` when the service or `evals/` differ from it), a hash of the service's prompts and
constants and of the judge prompts, the judge, the model and effort, the scores and the cost.

## Baselines

The numbers each metric reached last, on its dataset and judge; `baselines.md` has every run
behind them, by date (the assistant's in `baselines/assistant.md`, generation's prompts' in
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
| Assistant page context: general correct with / without; page checks | 112/129 / 116/129; 25/27 | `assistant_questions.json`, 3 repeats | 2026-10-20 |
| Assistant guides: guide questions correct; read and linked | 60/60; 58/60 | `assistant_guides.json`, 3 repeats | 2026-10-17 |
| Re-generated questions: written / keys / distractors / relevance | 40 of 40 / 97.5% / 3.23 ± 0.27 / 4.53 | 40 of `multi_questions.json` | 2026-10-22 |
| Assistant actions: task success / tool choice / arguments / asked first / link / injection safe | 328/335 / 328/335 / 188/188 / 44/45 / 45/45 / 85/85; 23,300 tokens, $0.0024, 6.4 s a turn | `assistant_actions.json` (67 cases), 5 repeats | 2026-10-21 |
| Planning: code checks / extraction covered / invented / topics covered / revisions applied / kept; judge traps | 96.2% (81.1–99.3) / 92.3% (75.9–97.9) / 3.8% / 92.3% (75.9–97.9) / 83.3% (55.2–95.3) / 75.0% (46.8–91.1); 62 of 62; $0.014 and 27 s a plan | `postings.json` and 7 of `inputs.json`, 13 × 2, 6 revisions × 2 | 2026-10-22 |
| Translations: code checks / faithful / native / one language; judge traps | 100% / 90.0% (80.8–95.1) / 98.6% (92.3–99.7) / 100%; 97 of 97; $0.0023 and 5.2 s a translation | `translations.json`, 10 texts × 7 languages | 2026-10-22 |
| Quality patterns: planted found / kept supported / no rule when none / known named; judge traps | 100% (79.6–100) / 100% (84.5–100) / 3 of 3 / 3 of 3; 10 of 10; $0.016 and 30 s a run | `patterns.json`, 4 groups × 3 | 2026-10-22 |
| Assistant titles: code checks / sums up / right language / natural; judge traps | 97.6% (87.7–99.6) / 88.1% (75.0–94.8) / 100% / 100%; 11 of 11; $0.00003 and 2.8 s a title | `titles.json`, 14 × 3 | 2026-10-22 |
| Repeated questions: distinct kept / repeats dropped | 100% (74.1–100) / 18.2% (5.1–47.7); the closest distinct pair at 0.084, the threshold 0.08 | `duplicates.json`, 22 pairs | 2026-10-22 |
| Code-language tags: right / skipped | 100% (96.6–100) / 0%; $0.006 and 7 s a batch of 20 | `code_languages.json`, 3 repeats | 2026-10-22 |
| Help chat: passed / made up / sign-in marker | 94.4% (84.9–98.1) / 5.6% / 100% | `help_questions.json`, 3 repeats | 2026-10-21 |

## Datasets

All in `datasets/`, frozen, made up, never a company's text. What each covers, how it was built
and when: `datasets/README.md`, which also says how a real failure becomes a case and how big a
set must be for the noise we accept. `scripts/check_datasets.py` checks them by code (shape,
duplicates, overlap with the prompts' examples, coverage), for free.

## Running a test

The scripts run inside the local stack's service containers, which have the service code,
packages and OpenAI key. `run.sh` copies `evals/` in, runs the script, and copies results back to
`results/` (not committed). Use `generation-worker` in place of `generation` to run a second
generation test at the same time. Langfuse tracing is off for test runs. `MODEL`, `EFFORT`,
`JUDGE_MODEL`, `JUDGE_EFFORT` and `OVERSAMPLE` are passed into the container when set; without
`MODEL` and `EFFORT`, generation tests use the service's own model.

```bash
# New interviews from the full pipeline: price, time, tokens; then review and check them
evals/run.sh generation generate_tests.py python_backend senior_accountant --label new-prompt
evals/run.sh generation review_questions.py results/test_python_backend_new-prompt.json --sample 40
evals/run.sh generation check_code.py results/test_python_backend_new-prompt.json

# Another model or effort on the reference subtopics, then the same review as the baseline
MODEL=gpt-6-luna EFFORT=high evals/run.sh generation build_questions.py --label luna-high
evals/run.sh generation review_questions.py results/questions_luna-high.json

# Another generation model or effort, on full interviews
MODEL=gpt-6-luna EFFORT=low evals/run.sh generation generate_tests.py --all --label luna-low

# Another oversample, on full interviews; each result counts the fill-up calls it needed
OVERSAMPLE=1.1 evals/run.sh generation-worker generate_tests.py python_backend --label os-1.1

# Re-generation (a company replacing a question; the verifier replacing one it can't fix): the
# service's own write of a new question and its options, on a fixed 40 of multi_questions.json
evals/run.sh generation regenerate_test.py --label x
evals/run.sh generation review_questions.py results/regenerated_x.json

# Verifier settings, on the traps and the same questions with their real key; --confirm for the
# blind confirmation a moved key needs
evals/run.sh generation verify_test.py gpt-6.1-sol/low gpt-6.1-sol/medium
evals/run.sh generation verify_test.py --confirm gpt-6.1-sol/medium

# Examples, their notation, length and reading time, per domain (free; --per-topic for a test)
evals/run.sh generation measure_examples.py results/questions_x.json \
    --reviews results/reviews_results_questions_x_gpt-6.1-sol_high.json
evals/run.sh generation generate_tests.py typescript_node --template --label x   # 90 a topic

# Multi-answer questions: build, judge (each kind's key accuracy apart), then the verifier on sets
evals/run.sh generation build_questions.py --per-subtopic 10 --multi 6
evals/run.sh generation build_traps.py --multi --count 268
evals/run.sh generation review_questions.py datasets/multi_questions.json
evals/run.sh generation verify_test.py --multi gpt-6.1-sol/medium

# Generation in other languages (one per script family), on its frozen set or a new prompt
evals/run.sh generation build_questions.py --inputs language_inputs.json --per-subtopic 6 \
    --multi 2 --label x
evals/run.sh generation review_questions.py datasets/language_questions.json

# The datasets' shape, duplicates, prompt-example overlap and coverage (free, on the host)
python3 evals/scripts/check_datasets.py

# A judge's new wording or a cheaper judge: tested against the reference and the traps
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/questions.json --compare-reference
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/key_traps.json
```

The assistant's page-context, guides and action tests run in the assistant's container on
throwaway data: its own two templates (made in library's container, removed after), and an
owner, a company with two interviews copied from them and three invited candidates who take them
aiming at set grades (`assistant_fixture.py`), all deleted as a user deletes their account when
the run ends; the action test adds an empty second company and a pending team member. Never the
user's own local records. Actions only ever become confirmation cards there: nothing runs.

```bash
evals/run.sh library assistant_templates.py create
evals/run.sh assistant page_context.py --label new-prompt      # --repeat 3, --only g01,p06
evals/run.sh assistant guides.py --label new-prompt            # --repeat 2, --only q01,g07
evals/run.sh assistant assistant_actions.py --label new-prompt # --repeat 3, --only i01,x02
evals/run.sh library assistant_templates.py remove
```

Planning a test through generation's own nodes (extraction, the topic draft, the revision on a
reviewer's instructions), the draft cache skipped:

```bash
evals/run.sh generation planning_test.py --label new-prompt   # --repeat 2, --only x01,r01
```

Translations of news posts and campaign emails, by generation's own `translate_one`, checked by
code and judged; the judge must catch the traps planted in the run's own translations (a sentence
left out, a number changed):

```bash
evals/run.sh generation translations_test.py --label new-prompt   # --languages de,ja, --only n01
```

The weekly quality pattern job's call (`find_patterns`) with the service's own checks, on made-up
groups of flagged questions with planted mistakes:

```bash
evals/run.sh generation patterns_test.py --label new-prompt   # --repeat 3, --only g1,g4
```

The embeddings that drop a new question asking what an earlier one asks, graded by code (each
pair's distance is saved):

```bash
evals/run.sh generation duplicates_test.py --label new-threshold
```

The code-language tagging job's call (`tag_examples`), graded by code:

```bash
evals/run.sh generation code_languages_test.py --label new-prompt   # --repeat 3, --sample 12
```

The assistant's conversation titles, with its own title prompt and model:

```bash
evals/run.sh assistant titles_test.py --label new-prompt   # --repeat 3, --only t02,t09
```

The help chat's test runs in rounds' container, with the service's own prompt, platform guide,
FAQ, prices and page guides:

```bash
evals/run.sh rounds help_chat.py --label new-prompt          # --repeat 3, --only h01,h10
```

| Test | Cost |
|---|---|
| A full interview, `gpt-6.1-sol` low | $1.60–2.30 at 100 questions a topic (7–10 topics); about $1.00 for 7 topics at 70 (estimated) |
| A full interview, `gpt-6-luna` high, 70 questions a topic | $0.07–0.20 (4–9 topics) |
| A full interview, `gpt-6-luna` low | about $0.05 at 100 questions a topic |
| A verifier setting on 120 checks (`verify_test.py`) | about $0.11 on Sol |
| Reviewing 40 questions (Sol judge, high) | about $0.20 (measured 2026-10-20: $0.88 for 240) |
| The language set: build and review | about $0.50 |
| Re-generating 40 questions and reviewing them | about $0.65 |
| The help chat's test, 3 repeats | about $1.05 (nearly all the judge) |
| The assistant's page-context test, 3 repeats | about $1.70 |
| The assistant's guides test, 3 repeats | about $1.50 |
| The assistant's action test, 3 repeats | about $0.45 (the judge reads only 24 replies and 8 traps) |
| The planning test, 2 repeats | about $0.85 (half the judges) |
| The translations' test (70 translations) | about $0.62 (three quarters the judge) |
| The quality patterns' test, 3 repeats | about $0.11 |
| The assistant titles' test, 3 repeats | about $0.09 (nearly all the judge) |
| The code-language tags' test, 3 repeats | about $0.02 |
| Code check, measurements, dataset checks, traps | free |

Use `--sample` to review part of an interview, and judge first with the reference only when a cheaper
judge hasn't been shown to agree.

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
