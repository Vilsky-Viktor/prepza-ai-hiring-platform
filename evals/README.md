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
| **Judge reliability** | Planted wrong keys it catches (`key_traps.json`) | `review_questions.py` | 100% |
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

## Baselines (2026-10-04)

**Generation**, `gpt-6.1-sol` at low reasoning, current prompts, on `questions.json` (240 questions,
8 domains), judged by `gpt-6.1-sol` at high reasoning; price and time per topic measured at 100
questions a topic, before interviews went to 70:

| Clarity | Relevance | One answer | Key correct | Code answers | Distractors | Correct is longest | Per topic |
|---|---|---|---|---|---|---|---|
| 4.95 | 4.23 | 98% | 99% | 13 of 13 | 3.03 | 11% | $0.21–0.25, 49–61 s |

At 70 questions a topic and oversample 1.0 that comes to about $0.13–0.16 a topic, and about $1.00
for a 7-topic interview (estimated from these runs, not measured).

For comparison, `gpt-6-luna` at low reasoning: about $0.006 and 17 s a topic, but more
miscalculations on hard topics, questions judged too easy for the level, and the correct option
the longest 26–46% of the time.

`gpt-6-luna` at **high** reasoning (2026-10-04, 236 questions on the same subtopics, same judge;
price and time from full Python backend and senior accountant interviews):

| Clarity | Relevance | One answer | Key correct | Code answers | Distractors | Correct is longest | Per topic |
|---|---|---|---|---|---|---|---|
| 4.91 | 3.97 (hard level 2.40, Sol 3.10) | 97% | 99% | 8 of 8 | 2.87 | 25% | $0.030–0.035, 87–92 s |

As accurate as Sol and 7–8 times cheaper, but about 1.6 times slower, and its hard-level
questions are too easy: relevance on hard topics is the gap, and it misses the relevance,
distractor and time targets, so every interview and template is generated on Sol at low. At 70 questions a topic
(the oversampling runs below, Python backend and Spanish for travel): $0.015–0.024 and 51–66 s a
topic; a 7-topic interview $0.16 in under 8 minutes.

**Verifier** (`verify_test.py`, the service's key-check prompt on the 60 traps and the same 60
questions with their real key): `gpt-6.1-sol` at low and at medium both fixed 60 of 60 traps and
kept 60 of 60 real keys, at $0.0009 a check and 1.8 s; medium is in use.

**Judge**, `gpt-6.1-sol` at high reasoning: caught 60 of 60 planted wrong keys.
Its wording of 2026-10-20 (a role, "skills test" and "candidate" for "prep kit" and "learner",
tagged data, anchored clarity and relevance) caught 60 of 60 single-answer traps and a fixed 60
of the multi-answer ones, and agreed with the reference on 239 of 240 keys (right kept 236 of
237, wrong found 3 of 3, kappa 0.86); clarity 4.95, relevance 4.20, distractors 2.82 ± 0.12
against the reference run's 4.95, 4.23, 3.03, within the judge's noise.

**Multi-answer questions** (2026-10-16, the gate before they ship: keys must reach 98%; the same
prompt's single-answer questions are the control), judged by `gpt-6.1-sol` at high, on fresh
`multi_questions.json` (48 subtopics, 3 of each 5 multi-answer):

| Prompt | Multi-answer keys correct | Single-answer keys correct | Multi-answer distractors |
|---|---|---|---|
| First version (`results/questions_multi-v1.json`) | 97.2% (140 of 144) | 99.0% | — (judged before multi-answer had its own measure) |
| Stated conditions, each option right or wrong alone, plus the self-check (`results/questions_multi-v5-final.json`) | 98.6% (139 of 141) | 99.0% (95 of 96) | 2.53 (2 right 2.74, 3 right 2.72, all 4 right 2.13); single-answer 3.21 |
| 2 or 3 right only (no all-4), four recipes for tempting wrong options, blind self-check (`results/questions_multi-r2-final.json`) | **96.5%** (137 of 142) | **99.0%** (95 of 96) | **2.70** (2 right 2.73, 3 right 2.66); single-answer 3.26 |

| The same, the self-check also asking for any unstated condition that decides an option (in use, 2026-10-17; 460 questions) | **98.5%** (264 of 268) | **99.0%** (190 of 192) | **2.68** (2 right 2.75, 3 right 2.60); single-answer 3.11 |

The last row's self-check (one call per new multi-answer question, `services/key_self_check.py`)
dropped 20 of 288 (6.9%) for a condition left open and none for a key it answered otherwise. Its
4 misses: a premise false on the platform named, a deduplication rule left unstated, a right
option outside the question's own scope, an option serving a neighbouring goal. 136 questions had
2 right options and 132 had 3. The verifier fixed 263 of 263 multi-answer traps and kept 263 of
263 real keys, and 60 of 60 and 60 of 60 single-answer.

The second row's tuning run (`results/questions_multi-v6.json`, one sentence less about the lone wrong
option of a 3-right question) scored 100% keys and 2.70 distractors: between runs of 140 questions
key accuracy moves by 2–3 points. The 5 misses of the fresh run left a condition unstated (which
`as` target, which titles, which is the titrant), the cost of tougher wrong options. The model writes
about twice as many 2-right as 3-right questions (95 and 47) though asked for as many of each.

The prompt was tuned on separate runs (`results/questions_multi-v2…v5.json`: multi-answer 98.6%,
94.4%, 98.6%, 99.3%); the final numbers come from a fresh run. Pushing for harder multi-answer
distractors ("right options a half-knowing person would doubt") cost accuracy (94.4%), so the
distractor score stays under 3.0: the next thing to raise. A select-all-that-apply question with
every option right scores lowest. The self-check (generation `services/key_self_check.py`: a blind
check of each new multi-answer key, dropping it when the check names other options) dropped 1–4
of about 140 a run. The right option is the longest 57% of the time against 75% by chance. The
verifier (`verify_test.py --multi`, `gpt-6.1-sol` at medium) fixed 139 of 139 multi-answer traps
and kept 139 of 139 real keys ($0.0012 a check, 3.3 s); on the single-answer traps, 60 of 60 and
60 of 60. On the 2-or-3 dataset: 137 of 137 multi-answer traps and real keys, 60 of 60 single-answer.

**Examples, length and reading time** (2026-10-17: the share of questions with an example,
their notation tags, how long they are, and domain-neutral prompts). Fresh sets on the 53
subtopics of `inputs.json`, 8 a subtopic, 2 of them multi-answer (`build_questions.py
--per-subtopic 8 --multi 2`), all judged by `gpt-6.1-sol` at high; counted by
`measure_examples.py`. Before: the prompt asked "at least a third" to come with an example, with
no upper bound. After: "about a third" on a subtopic about a notation a computer runs or reads
(each call is told exactly how many), concise artefacts (a few rows of data, figures, a schedule)
allowed elsewhere up to a third, never a notation the field doesn't use; examples only as long
as the question needs, one piece, the scenario with every detail the answer depends on and
nothing else; one minute to read and answer, a minute and a half only for the hardest; no
technology, standard or field named in any prompt.

| Domain (level) | With an example, before → after | Example lines (mean) / chars | Judge seconds, median / p90 / max | Single keys | Multi keys |
|---|---|---|---|---|---|
| python_backend (medium) | 65% → 40% (single 78% → 50%) | 5.9 / 136 → 5.5 / 133 | 30/35/60 → 25/35/40 | 34/36 → 35/36 | 10/10 → 9/9 |
| typescript_node (hard) | 78% → 38% (single 83% → 47%) | 5.7 / 158 → 6.0 / 162 | 30/40/60 → 30/35/40 | 29/29 → 30/30 | 8/8 → 10/10 |
| marketing_manager (hard) | 27% → 30%, all `text` (no SQL) | 4.3 / 153 → 4.0 / 158 | 28/40/60 → 30/35/45 | 35/36 → 36/36 | 12/12 → 11/11 |
| senior_accountant (hard) | 0% → 38%, `text` | — → 4.5 / 165 | 35/50/60 → 30/45/60 | 36/36 → 36/36 | 12/12 → 11/12 |
| project_manager (medium) | 6% → 31% | 2.0 / 69 → 3.7 / 112 | 25/40/60 → 25/35/60 | 36/36 → 36/36 | 12/12 → 12/12 |
| high_school_chemistry (medium) | 15% → 26% | 1.0 / 25 → 2.5 / 69 | 35/45/60 → 30/40/60 | 35/36 → 35/36 | 12/12 → 11/11 |
| registered_nurse (medium) | 2% → 19% | 6.0 / 154 → 2.8 / 95 | 25/40/60 → 25/30/60 | 35/36 → 36/36 | 11/11 → 12/12 |
| electrician_apprentice (basic) | 0% → 15% | — → 2.7 / 70 | 20/25/35 → 20/25/35 | 35/36 → 34/36 | 12/12 → 12/12 |
| spanish_travel (basic) | 0% → 9% | — → 3.8 / 62 | 20/20/30 → 20/22/30 | 36/36 → 35/36 | 10/10 → 11/11 |
| **All** | **20% → 27%**; code tagged `text`: 2 → 1 (a raw HTTP message, genuinely text) | 5.0 / 135 → 4.2 / 126; over 8 lines: 1 → 1 | 25/40/60 → 25/35/60; over 60 s: 0 → 0 | **98.1% → 98.4%** (311/317 → 313/318) | **100% → 99%** (99/99 → 99/100) |

Clarity 4.95 → 4.96, relevance (level fit) 4.21 → 4.15, distractors 3.00 → 2.88 (code-output
questions have the most tempting wrong options, and there are fewer of them; python 3.67 → 3.36,
TypeScript 3.49 → 3.33), all within the judge's noise. The judge's read-and-answer time by level
and kind after (median / p90 / max, seconds; none over 60, so none over 75 or 90): basic single
20/25/30, basic multi 25/25/35, medium single 25/35/60, medium multi 30/35/45, hard single
30/40/60, hard multi 30/40/60. Neither set reaches 99% single-answer keys; re-judged, the misses
held (mostly a condition the scenario left unstated), so the scenario rule now asks for every
detail the answer depends on.

Two tries on the way (`results/questions_ex-after1.json`, `…_ex-after2.json`): describing the
material neutrally as "a formal notation with exact rules … a calculation rule" brought examples
into every field (chemistry 38%, accounting 39%, SQL in marketing); "a notation a computer runs
or reads" with no examples elsewhere left the other fields at 0% (single keys 97.5%, multi 99%).
Files: `results/questions_ex-base.json`, `…_ex-after3.json` (in use) and their reviews.

**Hard-level prompt** (2026-10-04: "a scenario alone doesn't make a question hard: two or more
steps, or factors that pull in different directions"), 60 hard reference subtopics' questions, Sol
judge: `gpt-6.1-sol` low relevance 3.10 → 3.67, distractors 3.15 → 3.53, key correct 100%, but
questions about 75% longer, so a hard Sol interview costs roughly 50–70% more; `gpt-6-luna` high 2.40 →
2.68, still too easy for hard interviews. Basic and medium on Luna unchanged within judge noise
(medium relevance 4.29 → 4.17, basic distractors 2.80 → 2.60).

**Oversampling** (`generate_tests.py` with `OVERSAMPLE`, Luna high, 70 questions a topic, Python
backend and Spanish for travel): no topic came up short at 1.1 (13 topics) or at 1.0 (12), so no
fill-up call was made; 1.0 saves about 9% of question generation and is in use.

**Assistant: page context** (2026-10-17, `page_context.py`, the service's model `gpt-6-luna` at
low, each question 3 times in each variant, judged by `gpt-6.1-sol` at high). "Without" is the
assistant as before the page context: the page's path alone, no page instructions, no
`get_page_guide`, earlier messages without their page.

| Version | General: correct (with / without) | Right scope | Right tools | With wins / ties / losses | Page checks passed | Guide called |
|---|---|---|---|---|---|---|
| First instructions ("here" means the page; its ids used at once), one run each (`results/assistant_page_context_v1.json`) | 34/40 / 33/40 | 36 / 35 | 35 / 33 | 13 / 16 / 11 | 7/9 / 5/9 | 5/5 / 0/5 |
| The page's ids only when the user points at it, in the instructions (`…_v3.json`) | 103/120 / 109/120 | 115 / 114 | 109 / 106 | 32 / 49 / 39 | 24/27 / 10/27 | 15/15 / 0/15 |
| The same on the context line too (`…_v4.json`) | 110/120 / 103/120 | 115 / 109 | 108 / 99 | 41 / 50 / 29 | 25/27 / 12/27 | 15/15 / 0/15 |
| A named interview or candidate found with the list and search tools (`…_v5.json`) | 108/120 / 108/120 | 117 / 114 | 108 / 106 | 38 / 50 / 32 | 25/27 / 13/27 | 15/15 / 0/15 |
| A name wins over the page: found by the name without reading the page's one first, and searched for when what was read is about another (in use, 43 questions with 3 more named-vs-page ones, `…_v8.json`) | **121/129 / 108/129** | **129 / 116** | **120 / 107** | **46 / 57 / 26** | **25/27 / 11/27** | **15/15 / 0/15** |

The first instructions narrowed questions that don't point at the page to the ids on screen
("Who is my best candidate overall?" and "Which candidates passed?" answered for this interview
only; "Show me the Backend Developer candidates" on another interview's page showed that one).
Saying when the ids count, and on the context line beside them, fixed it. A name asked about on
another candidate's report ("How did Cara Diaz do?" on Ben's) still got Ben's result: the model
read the page's scorecard first and stopped there. Telling it to find a named one by the name,
and to search when what it read is about someone else, fixed it: on the 6 named-vs-page
questions (a named interview or candidate on another one's page) 18 of 18 answers were right
with the page context, 10 of 18 without (`…_v7-scope.json`, the scope-sensitive subset alone:
37/42 against 29/42). Without the page context, "What can I do on this page?"
answers about the whole interview or adds what the page doesn't offer, and "and here?" after
moving pages answers about the earlier page. The judge doesn't see the platform guide, so
how-to answers from it are judged with more noise (they move both ways between runs). Each run
costs about $1.70: the assistant about $0.75 for both variants, the judge about $0.95.

**Assistant: guides** (2026-10-17, `guides.py`, `gpt-6-luna` at low, each question 3 times in each
variant, judged by `gpt-6.1-sol` at high): 20 hiring-advice questions the site's guide articles
answer and 15 general ones of `assistant_questions.json` (data and how-to). "Without" is the
assistant before the guide tools: no `list_guides` or `get_guide`, no guide instruction.

| Version | Guide: correct (with / without) | Complete | Read a right guide / linked it | Guide wins / ties / losses | General: correct | Right scope | Right tools | General wins / ties / losses |
|---|---|---|---|---|---|---|---|---|
| Tools and a hiring-advice instruction (`results/assistant_guides_v1.json`) | 55/60 / 32/60 | 35 / 5 | 45/60 / 45/60 | 53 / 0 / 7 | 44/45 / 44/45 | 45 / 45 | 41 / 39 | 15 / 20 / 10 |
| Also for questions about prepza's own ATS integrations, MCP and API (in use, `…_v2.json`) | **60/60 / 28/60** | **43 / 5** | **58/60 / 58/60** | **58 / 0 / 2** | **44/45 / 44/45** | **45 / 43** | **44 / 40** | **13 / 25 / 7** |

In v1, "Which ATSs does prepza connect to?" and "Can I use prepza from Claude or ChatGPT?" read
the platform guide only, which has the facts but not the guide's checklist; saying that questions
about prepza's own integrations, MCP and API read the guide too fixed it. Two questions are
answered by two guides each (structured interviews, a knowledge screen's length), and either
counts. No general question called the guide tools; their differences are judge noise. A run
costs about $1.50: the assistant about $0.63 for both variants, the judge about $0.90.

## Datasets

All in `datasets/`, frozen: rebuild one only on purpose (a new domain, a new prompt generation),
note the date, and re-run the baselines on it.

| File | What | Built by | Cost to rebuild |
|---|---|---|---|
| `inputs.json` | 9 domains (Python backend, TypeScript/Node.js (hard, added 2026-10-17 so examples in several files are measured), marketing, nursing, accounting, Spanish for travel, school chemistry, electrician apprentice, project management): a job description or role for the full pipeline, plus fixed topics and subtopics for question-only tests | By hand | — |
| `questions.json` | 240 reference questions, 5 per subtopic, written by `gpt-6.1-sol` at low with the generation prompt of the date inside (a rebuild uses the service's model, `INTERVIEW_MODEL`) | `build_questions.py` | about $0.50 |
| `reviews.json` | The reference judge's verdict on each of those questions | `review_questions.py --save-reference` | about $3 |
| `key_traps.json` | 60 of those questions with the key moved to a wrong option on purpose | `build_traps.py` | free |
| `multi_questions.json` | 460 questions on the same subtopics, 6 of each subtopic's 10 multi-answer ("select all that apply": 2 or 3 right options of 4; 136 and 132), written by `gpt-6.1-sol` at low with the prompt of 2026-10-17 and its self-check; ids `m0000`… | `build_questions.py --per-subtopic 10 --multi 6` | about $1.60 |
| `multi_key_traps.json` | Its 268 multi-answer questions with one option's mark flipped (with 2 right a wrong one marked, with 3 a right one unmarked), so 2 or 3 stay marked | `build_traps.py --multi --count 142` | free |

| `assistant_guides.json` | The assistant's guides test: 20 hiring-advice questions, each with the page it's asked on, the guide articles that answer it and what a right answer does, and the ids of 15 general questions of `assistant_questions.json` asked as a guard | By hand | — |
| `assistant_questions.json` | The assistant's page-context test: 8 pages (key, path, the ids the panel sends), 43 general questions asked on 6 of them (6 name an interview or candidate other than the page's), each with what a right answer does, and 9 page checks ("What can I do on this page?" on 5 pages, "Who's best here?", "How did this candidate do?", and "and here?" after moving between interviews) | By hand | — |

`reviews.json` flags 4 questions as flawed (q0008, q0072, q0094, q0232). They're kept on purpose:
real generations have such slips, and a verifier test should see some.

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

# Verifier settings, on the traps and the same questions with their real key
evals/run.sh generation verify_test.py gpt-6.1-sol/low gpt-6.1-sol/medium

# Examples, their notation, length and reading time, per domain (free; --per-topic for a test)
evals/run.sh generation measure_examples.py results/questions_x.json \
    --reviews results/reviews_results_questions_x_gpt-6.1-sol_high.json
evals/run.sh generation generate_tests.py typescript_node --template --label x   # 90 a topic

# Multi-answer questions: build, judge (each kind's key accuracy apart), then the verifier on sets
evals/run.sh generation build_questions.py --per-subtopic 10 --multi 6
evals/run.sh generation build_traps.py --multi --count 268
evals/run.sh generation review_questions.py datasets/multi_questions.json
evals/run.sh generation verify_test.py --multi gpt-6.1-sol/medium

# A cheaper judge, tested against the reference and the traps
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/questions.json --compare-reference
JUDGE_MODEL=gpt-6-luna JUDGE_EFFORT=medium evals/run.sh generation review_questions.py datasets/key_traps.json
```

The assistant's page-context and guides tests run in the assistant's container on throwaway data: its own two
templates (made in library's container, removed after), and an owner, a company with two
interviews copied from them and three invited candidates who take them aiming at set grades
(`assistant_fixture.py`), all deleted as a user deletes their account when the run ends. Never
the user's own local records.

```bash
evals/run.sh library assistant_templates.py create
evals/run.sh assistant page_context.py --label new-prompt      # --repeat 3, --only g01,p06
evals/run.sh assistant guides.py --label new-prompt            # --repeat 2, --only q01,g07
evals/run.sh library assistant_templates.py remove
```

| Test | Cost |
|---|---|
| A full interview, `gpt-6.1-sol` low | $1.60–2.30 at 100 questions a topic (7–10 topics); about $1.00 for 7 topics at 70 (estimated) |
| A full interview, `gpt-6-luna` high, 70 questions a topic | $0.07–0.20 (4–9 topics) |
| A full interview, `gpt-6-luna` low | about $0.05 at 100 questions a topic |
| A verifier setting on 120 checks (`verify_test.py`) | about $0.11 on Sol |
| Reviewing 40 questions (Sol judge, high) | about $0.20 (measured 2026-10-20: $0.88 for 240) |
| The assistant's page-context test, 3 repeats | about $1.70 |
| The assistant's guides test, 3 repeats | about $1.50 |
| Code check, measurements, traps | free |

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
