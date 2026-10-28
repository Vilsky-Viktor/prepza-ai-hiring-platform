# Baselines and their history

What each metric of `../README.md` measured, by date, with the runs behind it. The newest numbers
per metric are summed up in `../README.md`; a shipped change adds its row here, for the assistant
in `assistant.md` (its actions in `assistant-actions.md`), for generation's prompts in `generation.md`, and for the
small utility prompts (translations, code-language tags, quality patterns, conversation titles)
in `utility.md` (CLAUDE.md rule 20).

Contents: [Baselines (2026-10-04)](#baselines-2026-10-04) ·
[Eval changes (2026-10-20)](#eval-changes-2026-10-20) ·
[Help chat: a tighter rule, reverted](#help-chat-a-tighter-rule-for-what-the-information-doesnt-say-2026-10-20-reverted) ·
[Help chat: currencies](#help-chat-currencies-in-its-guide-2026-10-21-kept) ·
[Help chat: four more currencies](#help-chat-four-more-currencies-2026-10-21-kept) ·
[Help chat: automatic top-up](#help-chat-automatic-top-ups-pause-and-price-notice-2026-10-21-kept) ·
[Help chat: Mira](#help-chat-mira-an-ai-assistant-that-says-so-2026-10-22-kept) ·
[The scope rule's language](#the-scope-rule-names-no-language-of-its-own-2026-10-22-kept) ·
[Help chat: the shareable link's tab](#help-chat-the-shareable-link-on-the-settings-tab-2026-10-23-kept) ·
[Help chat: moved to the assistant](#help-chat-moved-from-rounds-to-the-assistant-2026-10-29-kept)

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

## Help chat: a tighter rule for what the information doesn't say (2026-10-20, reverted)

Tried: "never work out a rule, a limit or a number it doesn't state from nearby facts; if the
answer isn't there, say so plainly and suggest {email} or the contact page". Passed 49 → 47 of
54 (87.0%, 75.6–93.6); the invented attempt limit (h17) 0 → 1 of 3 right; two sign-in replies
read as promising more. No gain beyond the noise: reverted. Reading the failures showed h09's
expectation was wrong: the terms do say how price changes work, and the chat quoted them, so a
right answer may do that instead of pointing to the contact page. With the case fixed, the
baseline re-run: **passed 51 of 54, 94.4% (84.9–98.1)**, made up 5.6%, markers 54/54; every
miss is h17 ("How many times can a candidate take the test?" in Japanese: it answers "once",
which the platform guide doesn't state). That gap is the guide's: it should say whether a
candidate can take a test again.

## Help chat: currencies in its guide (2026-10-21, kept)

Prices became EUR in the EU and nearby, GBP in the UK and USD elsewhere, per person and per
company. The guide gained one fact line about currencies and lost "$0 subscription"; the FAQ it
reads names prices in the visitor's currency. `help_chat.py`, `help_questions.json`, 18 messages
× 3, `gpt-6-luna` at none, same judge; both runs on the same working tree, before and after the
prompt change:

| Run | Passed | Made up | Sign-in marker | Price (help / judge) |
|---|---|---|---|---|
| Before | 88.9% (77.8–94.8) | 7.4% (2.9–17.6) | 100% | $0.013 / $1.08 |
| After | 94.4% (84.9–98.1) | 7.4% (2.9–17.6) | 100% | $0.012 / $1.06 |

No difference beyond the intervals; kept because the facts are needed for currency questions.
The failures are the known h17 (an invented retake limit) and one h04 (viewers and billing).

## Help chat: four more currencies (2026-10-21, kept)

The guide's currency line now names CAD, AUD, ILS and PLN, and the FAQ gained "Which currency
do I pay in?". Same test, dataset, model and judge as the run above: passed 94.4% (84.9–98.1),
made up 5.6% (1.9–15.1), sign-in marker 100%; $0.013 help, $1.10 judge. No difference beyond
the intervals; the only failures are the known h17 (an invented retake limit).

## Help chat: automatic top-up's pause and price notice (2026-10-21, kept)

The guide's automatic top-up line now says a declined charge is tried again after 1, 3 and 7
days, then pauses until the card's owner updates it ("Update card" on the billing page), that a
new price is emailed at least 30 days ahead, and that a currency change applies at once. Same
test, dataset, model and judge as the run above: passed 94.4% (84.9–98.1), made up 5.6%
(1.9–15.1), sign-in marker 100%; $0.013 help, $1.13 judge. No difference beyond the intervals;
the only failures are the known h17 (an invented retake limit).

## Help chat: Mira, an AI assistant that says so (2026-10-22, kept)

The help chat is the same Mira as the in-app assistant, for visitors: its instructions open "You
are Mira, prepza's AI assistant" and say that asked its name, who it is or whether it's human, it
says it's Mira, an AI, never a person; its guide calls the header's button "ask Mira".
`help_questions.json` gained 6 identity questions (h19–h24: English, French, Korean, Polish,
Hebrew). Same test, model and judge, 3 repeats: before (`results/help_chat_mira-base.json`)
passed 72.2% (61.0–81.2), identity 1 of 18, the rest 51 of 54, made up 6.9%; after
(`…_mira-new2.json`) passed 94.4% (86.6–97.8), identity 18 of 18, the rest 50 of 54, made up
4.2% (1.4–11.5), sign-in marker 100% both times. A first wording that also told it to offer help
made an off-topic refusal two sentences long (h12, 1 of 3), so it was dropped. The remaining
failures are the known h17 (an invented retake limit) and one h12.

## Help chat: the reply's language chosen by code, the visitor's messages as data (2026-10-22, kept)

The help chat let the model infer the reply's language ("the page's, unless the user writes in
another"); now code chooses it (the question's own when its script or at least two of a
Latin-script language's common chat words show it, else the page's) and the prompt names it.
Each of the visitor's messages comes inside `<visitor_message>`, read as data. `help_chat.py`,
`help_questions.json`, 24 × 3, `gpt-6-luna` at none, judged by `gpt-6.1-sol` high, before →
after: passed 93.1% (84.8–97.0) → 97.2% (90.4–99.2); made up 4.2% → 2.8%; sign-in marker 100%
both; language cases 3 → 4 of 6 (the misses are h17's invented retake limit); $0.024 help, $1.27
judge. Kept: better, nothing worse.

## The scope rule names no language of its own (2026-10-22, kept)

The scope rule both chats share (`prepza_common.ai.scope`) asked to decline "in the user's
language", a language the model would infer, while each prompt names the reply's language chosen
by code; it now says "in the language you answer in". `help_chat.py`, 24 × 3, against
`results/help_chat_h1.json` (`…_scope.json`): passed 97.2% → 95.8% (88.5–98.6), one answer;
off-topic 3 of 3 and injection 6 of 6 both; language cases 4 → 3 of 6, the misses h17's known
invented retake limit. `assistant_actions.py`, 2 repeats (`results/assistant_actions_scope.json`):
task success 97.1% (92.7–98.9), injection safe 100%, its failures (c04, e12, m05, m06) cases that
failed before. Within the noise; kept so no prompt leaves a language to inference. $1.89.

## Help chat: the shareable link on the Settings tab (2026-10-23, kept)

The shareable link moved from an interview's Candidates tab to its Settings tab, and the help
chat's guide says so (`00af4873e`). A new case, h25 ("Where do I turn on the link I can post with
a job ad?"), checks the answer names the Settings tab. `help_chat.py`, 25 × 3, `gpt-6-luna` at
none, judged by `gpt-6.1-sol` high, against `results/help_chat_scope.json` (24 × 3) →
`…_link.json`: passed 95.8% (88.5–98.6) → 94.7% (87.1–97.9); h25 3 of 3; made up 4.2% → 4.0%;
sign-in marker 100% both; off-topic 3 → 2 of 3 (h12 declined in two sentences, not one); the
other misses are h17's known invented retake limit. Within the noise. $1.53.

## Help chat: moved from rounds to the assistant (2026-10-29, kept)

The help chat moved to the assistant with its prompt, model and settings unchanged; rounds still
owns the site's documents and sends them (`GET /internal/help/knowledge`). The rendered messages
for three cases (two pages, two countries, a signed reply) were byte-identical before and after.
`help_chat.py`, 25 × 3, `gpt-6-luna` at none, judged by `gpt-6.1-sol` high, in rounds just
before (`results/help_chat_before_move.json`) → in the assistant (`…_after_move.json`): passed
96.0% (88.9–98.6) both; made up 4.0% both; sign-in marker 100% both; language 3 of 6 both; the
misses are h17's known invented retake limit. $1.64 and $1.17.
