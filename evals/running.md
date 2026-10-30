# Running the offline tests

How to run each test of [README.md](README.md), what it needs and what it costs.

Contents: [Generation and the verifier](#generation-and-the-verifier) ·
[The assistant](#the-assistant) · [Planning a test](#planning-a-test) ·
[Small utility prompts](#small-utility-prompts) · [The help chat](#the-help-chat) · [Thumbs-down answers](#thumbs-down-answers) ·
[What each costs](#what-each-costs) · [Lessons](README.md#lessons-so-far)

The scripts run inside the local stack's service containers, which have the service code,
packages and OpenAI key. `run.sh` copies `evals/` in, runs the script, and copies results back to
`results/` (not committed). Use `generation-worker` in place of `generation` to run a second
generation test at the same time. Langfuse tracing is off for test runs. `MODEL`, `EFFORT`,
`JUDGE_MODEL`, `JUDGE_EFFORT` and `OVERSAMPLE` are passed into the container when set; without
`MODEL` and `EFFORT`, generation tests use the service's own model.

## Generation and the verifier

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
# service's own write of a new question and its options, on a fixed 40 of multi_questions.json;
# --mode rewrite or new-options for the verifier's work as its batch requests ask for it
evals/run.sh generation regenerate_test.py --label x
evals/run.sh generation regenerate_test.py --label x --mode new-options
evals/run.sh generation review_questions.py results/regenerated_x.json

# Flagged templates' questions as traps (datasets/flagged_traps.json, free, in library's container);
# the verifier and the judge read them with the planted traps
evals/run.sh library export_flagged.py
evals/run.sh generation review_questions.py datasets/flagged_traps.json

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

# Fitted question times: rounds' estimate against the judge's seconds (free, code only); the
# dataset rebuilt from review files (dataset=reviews pairs; a dataset given twice is the retest)
evals/run.sh rounds question_times.py
evals/run.sh rounds question_times.py --build datasets/questions.json=results/reviews_x.json ...

# The datasets' shape, duplicates, prompt-example overlap and coverage (free, on the host)
python3 evals/scripts/check_datasets.py

# A judge's new wording or a cheaper judge: tested against the reference and the traps
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/questions.json --compare-reference
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/key_traps.json
```

## The assistant

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

## Planning a test

Planning a test through generation's own nodes (extraction, the topic draft, the revision on a
reviewer's instructions), the draft cache skipped:

```bash
evals/run.sh generation planning_test.py --label new-prompt   # --repeat 2, --only x01,r01, --sample 4
```

## Small utility prompts

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

The eval gate before an approved pattern becomes a rule in use: a fresh set without and with the
rule on the same subtopics, judged on every dimension and on the pattern's own mistake; `--record`
puts a pattern that ships in use with its run (then add its text to generation's `QUALITY_RULES`
and the run to `baselines/generation.md`):

```bash
evals/run.sh generation pattern_gate.py --pattern <id> --record   # --subtopics 16 for a quick look
evals/run.sh generation pattern_gate.py --rule "..." --subtopics 16 --label dry   # never recorded
```

The embeddings that drop a new question asking what an earlier one asks, graded by code (each
pair's distance is saved):

```bash
evals/run.sh generation duplicates_test.py --label new-threshold
```

The check that refuses a pasted text naming nothing to test, graded by code (a false refusal
fails):

```bash
evals/run.sh generation screen_test.py --label new-prompt   # --repeat 3
```

The shared question bank's filter (`is_general`), graded by code (a private question kept is a
leak); `--local FILE` counts what it keeps of questions saved in `results/` (never committed):

```bash
evals/run.sh generation bank_filter_test.py --label new-prompt   # --repeat 3
```

The code-language tagging job's call (`tag_examples`), graded by code:

```bash
evals/run.sh generation code_languages_test.py --label new-prompt   # --repeat 3, --sample 12
```

The assistant's conversation titles, with its own title prompt and model:

```bash
evals/run.sh assistant titles_test.py --label new-prompt   # --repeat 3, --only t02,t09, --sample 6
```

The assistant's speech to text, on recordings made once by text-to-speech (`build_audio.py`):

```bash
evals/run.sh assistant transcription_test.py --label new-model   # --repeat 2
```

## The help chat

The help chat's test runs in the assistant's container, with the service's own prompt and model,
reading the platform guide, FAQ, prices and page guides from site as the service does:

```bash
evals/run.sh assistant help_chat.py --label new-prompt       # --repeat 3, --only h01,h10
```

## Thumbs-down answers

The answers people voted down, to turn into made-up feedback cases (`datasets/README.md`,
Feedback cases), free; `READ_LANGFUSE=1` keeps Langfuse's keys, which `run.sh` otherwise empties.
The cases run apart from the hand-written ones:

```bash
READ_LANGFUSE=1 evals/run.sh assistant disliked_answers.py   # results/disliked_answers.json
evals/run.sh assistant help_chat.py --dataset help_feedback.json --label feedback
evals/run.sh assistant page_context.py --dataset assistant_feedback.json --label feedback
```

## What each costs

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
| The eval gate | about $0.09 a subtopic ($1.48 for 16), about $5 on all 53 |
| The assistant titles' test, 3 repeats | about $0.09 (nearly all the judge) |
| The code-language tags' test, 3 repeats | about $0.02 |
| Code check, measurements, dataset checks, traps | free |

Use `--sample` to review part of an interview, and judge first with the reference only when a cheaper
judge hasn't been shown to agree.

