# Baselines and their history

What each metric of `../README.md` measured, by date, with the runs behind it. The newest numbers
per metric are summed up in `../README.md`; a shipped change adds its row here, for the assistant
in `assistant.md` (its actions in `assistant-actions.md`), for the help chat in `help-chat.md`, for
generation's prompts in `generation.md`, and for the small utility prompts (translations, code-language tags, quality patterns, conversation titles)
in `utility.md` (CLAUDE.md rule 20).

Contents: [Baselines (2026-10-04)](#baselines-2026-10-04) ·
[Eval changes (2026-10-20)](#eval-changes-2026-10-20) ·
[Fitted question times (2026-10-29)](#fitted-question-times-2026-10-29) ·
[Integrity signals (2026-10-29)](#integrity-signals-2026-10-29)

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

**Assistant**: page context and guides in `assistant.md`; actions and tools per turn
in `assistant-actions.md`.

## Eval changes (2026-10-20)

Results now record their run (commit, prompts hash, judge, model, scores with 95% intervals,
cost). `judges/question_review.md` got a role, "skills test" and "candidate" for the old "prep
kit" and "learner", tagged data and anchored clarity and relevance scales. Its checks
(`gpt-6.1-sol` high): planted single-answer traps caught 60 of 60, multi-answer traps 60 of 60
(a fixed sample of 60 of 268), and on `questions.json` agreement with the reference 239 of 240
(right keys kept 236 of 237, wrong keys found 3 of 3, kappa 0.86). Its scores there: keys 98.3%
(95.8–99.4), one defensible answer 97.9%, clarity 4.95 ± 0.05, relevance 4.20 ± 0.12,
distractors 2.82 ± 0.12 (the reference run of the old wording: 4.95, 4.23, 3.03; within the
judge's run-to-run noise). The three runs cost $1.42.

**Other languages** (`language_questions.json`, new: German medium, Japanese basic, Arabic
medium, Thai basic, Hindi medium, Russian hard; 72 questions, 24 multi-answer, `gpt-6.1-sol` low,
$0.24): keys 100% (94.9–100), one defensible answer 100%, clarity 4.99, relevance 3.89 ± 0.23,
distractors **2.28 ± 0.24**. The wrong options are less tempting than in English (2.8–3.0): the
gap to work on in other languages. (A first build with only German, Japanese and Arabic, 35
questions, scored 1.83.)

**Help chat** (`help_chat.py`, new; `gpt-6-luna` at none, 18 messages × 3, judged by
`gpt-6.1-sol` high): passed 49 of 54, 90.7% (80.1–96.0); made up 5.6%; sign-in markers 54 of
54. By kind: typical 24/24, sign-in 6/6, off-topic 3/3, injection 6/6, page 3/3, unknown 4/6
(a price question answered with a hedge instead of pointing to the contact page), language 3/6
(asked in Japanese how many attempts a candidate has, it invented "one"). $1.06 a run. The first
run (63%) judged against expectations that listed optional details as required, and without the
page's guide; both fixed before this baseline.

**Re-generation** (`regenerate_test.py`, new: the service's `write` on a fixed 40 of
`multi_questions.json`, 25 multi-answer, each told the other questions of its subtopic;
`gpt-6.1-sol` low, judged at high): 40 of 40 written, all of their kind; keys 100% (91.2–100),
clarity 5.00, relevance 4.58 ± 0.20, distractors 3.38 ± 0.27; $0.49 for 40 (a new question, its
options, and a retry when one came out ambiguous), 121 s.

## Fitted question times (2026-10-29)

`question_times.py` (new, free) on `question_times.json` (452 questions, judged by `gpt-6.1-sol`
high; the new judge runs cost $0.79): rounds' estimate of each question's time (reading at 200
words a minute, an example at 120, plus 30 s to answer) against the judge's seconds. Over 3,000
draws of 10 questions of one level and language at an average of 60 s, each question's distance
from the time the judge's estimates would give it, as a share of the average:

| Kind | Questions | Spearman | Fitted | Equal |
|---|---|---|---|---|
| All | 452 | 0.49 (English) | 0.158 ± 0.002 | 0.167 ± 0.002 |
| English basic, single | 68 | 0.65 | 0.116 ± 0.003 | 0.147 ± 0.004 |
| English basic, multi | 13 | 0.70 | 0.222 ± 0.018 | 0.217 ± 0.019 |
| English medium, single, example | 29 | 0.65 | 0.181 ± 0.010 | 0.209 ± 0.011 |
| English medium, single, text | 111 | 0.25 | 0.193 ± 0.007 | 0.186 ± 0.006 |
| English medium, multi, text | 33 | 0.16 | 0.189 ± 0.014 | 0.186 ± 0.013 |
| English hard, single | 69 | 0.33 | 0.251 ± 0.007 | 0.256 ± 0.008 |
| English hard, multi | 14 | -0.13 | 0.212 ± 0.015 | 0.244 ± 0.014 |
| German / Hindi | 12 / 12 | 0.47 / 0.57 | 0.147 / 0.133 | 0.156 / 0.173 |
| Arabic / Russian (weight 1) | 12 / 12 | 0.16 / 0.10 | 0.183 / 0.261 | 0.183 / 0.261 |
| Japanese / Thai (weight 1) | 12 / 12 | -0.17 / 0.28 | 0.086 / 0.041 | 0.086 / 0.041 |

The judge is consistent with itself (40 questions twice: Spearman 0.95, 2.1 ± 0.8 s apart), so
its estimates carry a question's working time, which length alone doesn't: within medium and hard
text-only questions the estimate follows it only weakly (0.25–0.33). Fitted times still come
closer overall, most for basic questions and those with an example. Tried: 15, 30 and 45 s to
answer, with 0, 5 and 10 s more for a multi-answer question; 30 and none came closest (15 with 5:
0.168, no better than equal). Arabic and Russian came out further than equal (0.199 and 0.277)
and Japanese and Thai can't be counted in words, so those scripts get weight 1; each rests on 12
questions only.

## Integrity signals (2026-10-29)

The anti-cheating plan's signals (`internal_docs/plans/anti-cheating.md`), measured before any was
built. No real candidate's answers exist or may be used (rule 20), so candidates are made up
(`integrity_population.py`): honest ones answer by the Rasch model with van der Linden's lognormal
times (reading plus thinking that grows with difficulty, a speed per person, noise per answer);
relaying ones give the AI's real answer to each question (`ai_picks.json`) in a flat 20–40 s of
their own (±25% an answer, plus 15% of the reading). Four honest populations: typical, noisy (much
more noise, thinking that barely follows difficulty, more skimming), weak and strong. Questions are
the eval's real ones, drawn as interviews with rounds' fitted times; each question's difficulty is
the share right of 30 simulated answers. 4,000 candidates a population; free.

**AI-trap questions** (`ai_picks.py`, $1.07): of 772 questions, `gpt-6-luna` (no reasoning) and
`gpt-6.1-sol` (low) never gave the same wrong answer (0.0%, 0.0–0.5): Sol answers 99.6% of the
generator's own questions right, so the planned traps don't exist. The only traps there are, the
cheap model's mistakes that Sol gets right (14.5% of questions; 2 of 112 had a key the judge
found wrong), are given again by the cheap model in another order 44.6% of the time, by Luna at
medium reasoning 3.6%, by Sol 0%. As a signal (at least 2 traps answered with the AI's answer,
P ≤ 0.001 for an honest candidate with a generous pull to that option): 0.1% of honest candidates,
6.6% of relays to the cheap model at 30 questions, 0% of relays to any reasoning model (on the
simulation's first version, which held the trap's statistics). Dropped (the user, 2026-10-29): the
planned traps don't exist, and the only ones there are catch no relay to a reasoning model, for an
AI call a question at generation. `ai_picks.py` stays to rerun the measurement on a new model.

**Timing** (rounds' `flat_timing`): answer times' spread (standard deviation of their logs) and
their Spearman rho against each question's fitted time (longer by 1 + (1 − share right) when
known). Rho alone can't separate them (honest times are noisy and fitted times vary little within
an interview: rho ≤ 0 for 10–22% of honest candidates and 24–41% of relays); spread and rho
together can:

| Spread ≤ / rho ≤ | Honest, worst population (30 questions) | Relays, all questions | Half | Hard-only |
|---|---|---|---|---|
| 0.25 / 0.0 (chosen) | 0.7% | 33% | 3% | 11% |
| 0.25 / 0.2 | 1.4% | 62% | 6% | 17% |
| 0.30 / 0.0 | 1.1% | 39% | 7% | 13% |
| 0.30 / 0.4 | 4.5% | 93% | 19% | 35% |

The weak population sets the limit: candidates who run up against every question's time look
flat too. At 10 and 20 questions the chosen one flags 0.6–0.7% of honest candidates and catches
33–34% of full relays.

**Person-fit** (rounds' `unusual_pattern`, lz over questions of known difficulty, at least 8):

| lz ≤ | Honest, worst (30 / 10 questions) | Relays, all (Luna / Sol) | Half | Hard-only |
|---|---|---|---|---|
| −3.0 | 2.6% / 1.1% | 12% / 0.3% | 16% | 26% |
| −3.5 | 1.6% / 0.8% | 5% / 0.1% | 10% | 16% |
| −4.0 (chosen) | 0.7% / 0.3% | 3% / 0% | 7% | 10% |

A relay to a strong model gets nearly everything right, which leaves no pattern; the signal is
for partial use (and fires only once questions have 30 answers each, library's `MIN_ANSWERS`).

**Either shipped signal** at the chosen thresholds: honest 0.2–0.7% in every population at 10, 20
and 30 questions; full relays 33–35%; half 7–9%; hard-only 15–19%. What these rest on: the
relays' flat timing (a real relay's spread is unknown: at ±35% instead of ±25%, full relays
caught drop to 8–11%), and honest times as the model draws them. Rerun on real traffic once companies confirm
cases in follow-up interviews.

