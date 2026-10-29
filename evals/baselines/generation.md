# Baselines of generation's prompt changes

The runs behind changes to generation's prompts (questions, options, re-generation, extraction,
topics, key checks) from 2026-10-20 on, by date; the first baselines and the eval changes are in
`README.md`.

## Question prompts: role, instructions first, data tagged (2026-10-20)

`questions.py`, `answers.py` and `regenerate.py` start with a generic role (an assessment
designer who writes questions for skills tests in any field); their instructions move into a
system message that changes with no call, so the provider caches it, and the call's values and
the topic's existing questions, tagged as data, come last in the request. Same wording
otherwise. `gpt-6.1-sol` low, judged by `gpt-6.1-sol` high, before → after:

| Set | Keys | One defensible answer | Clarity | Relevance | Distractors | Price |
|---|---|---|---|---|---|---|
| 53 subtopics × 6, 2 multi (300 → 312 questions) | 98.3% (96.2–99.3) → 98.7% (96.8–99.5); multi 100% → 100% | 98.3% → 98.4% | 4.97 → 4.97 | 4.30 ± 0.10 → 4.24 ± 0.10 | 2.92 ± 0.10 → 2.88 ± 0.10 | $1.21 → $0.90 (**$0.0040 → $0.0029 a question, −28%**), 301 → 284 s |
| Re-generation, 40 (two runs after) | 100% → 95% (2 misses, one subtopic) and 100% | 100% → 95%, 100% | 5.00 → 4.92, 5.00 | 4.58 → 4.50, 4.47 | 3.38 → 3.27, 3.25 | $0.49 → $0.33, $0.25 |
| Other languages (72 → 71) | 100% → 100% | 100% → 100% | 4.99 → 5.00 | 3.89 → 3.85 | 2.28 → 2.15 (± 0.24) | $0.24 → $0.23 |

No quality metric moved beyond its interval; the price per question fell by about a quarter on
the full set (the ~2,500 tokens of rules are now a cached prefix) and by a third to a half on
re-generation. The self-check dropped 5 of 106 multi-answer questions for an open condition (11
of 104 before). Kept: cheaper, and the role and tagged data rule 19 asks for.

## Topic and extraction prompts: role, data tagged (2026-10-20)

The topic draft, its revision and the extraction start with a role; the requirements, current
topics and reviewer instructions move to the user's message, tagged and read as data (the
posting already was). Full pipeline, `gpt-6.1-sol` low, two domains, before → after (after also
has the question prompts' change above), 40 questions of each judged:

| Domain | Topics | Keys | Clarity | Relevance | Distractors | Price, time |
|---|---|---|---|---|---|---|
| spanish_travel (basic) | 10 → 10, the same subjects regrouped | 100% → 100% | 4.95 → 5.00 | 4.92 → 4.97 | 2.23 → 2.30 | $1.29 → $0.93, 303 → 264 s |
| senior_accountant (hard) | 10 → 10, the same subjects regrouped | 100% → 95% (83.5–98.6; 2 keys with an unstated condition) | 4.97 → 4.88 | 2.75 → 2.98 | 2.65 → 2.80 | $1.83 → $1.63, 594 → 584 s |

Both plans cover every requirement within the limits; nothing moved beyond its interval. Kept
for rule 19 (a role, the company's text read as data) rather than for a measured gain. The hard
accountant's relevance near 3 in both runs is the hard-level gap already known (Luna and Sol
rows above).

## Key-check prompts: role, data tagged, strict batch (2026-10-20)

The verifier's key check, the blind confirmation and the self-check get a reviewer's role in a
system message, with the question, options and reports tagged; the Batch API request, which sent
its JSON schema without `strict`, now sets it (checked once against the API). `gpt-6.1-sol`
medium, before → after: single-answer traps fixed 60/60 → 60/60, real keys kept 60/60 → 60/60
($0.0009 → $0.0010 a check); multi-answer 263/263 → 263/263 both ($0.0012). The self-check, on
a fresh build of 311 questions (53 subtopics × 6, 2 multi): dropped 7 of 106 for an open
condition (5 before); keys 98.4% (96.3–99.3) against 98.7%, multi-answer 98.0% (92.9–99.4)
against 100%, distractors 2.95, clarity 4.97, relevance 4.22: within the intervals. Kept for
rule 19 and the strict batch schema.


## Verifier: the key check no longer sees where the key is (2026-10-22, kept)

The key check listed the marked options first, so for a single-answer question option 0 was
always the claimed key, and a check that agreed with it kept the question with no blind second
look. The options now come in an order shuffled by the question's id (the same for a batched
check and its reply, `option_order`), and the prompt says no option is marked; `KeyCheck` says
2 or 3 for a select-all-that-apply key, as the prompt does. `verify_test.py` now asks through the
service's own `key_check_prompt` and order. `gpt-6.1-sol` medium, before → after: single-answer
traps fixed 60/60 → 60/60, real keys kept 60/60 → 60/60 ($0.0010 a check both); multi-answer
263/263 → 263/263 both ($0.0012). No difference; kept for rule 19 (a checker works out the
answer with positions and marks hidden).

## Extraction: one cached system message, the posting tagged (2026-10-22, kept)

The extraction's system message changed with each call (the title rule and the language were
filled in), shouted ("EVERY", "ALL", "ONE", "YES/NO"), walked through a procedure, used a
dataset's role as its example ("Senior Accountant at Acme") and contradicted its schema (the
title's description said "the role and company", the template rule "never the company"). Now
one fixed system message holds the role and the rules with their reasons; the posting goes in
the user's message inside `<job_posting>`, with the kind of test and the language last; the
examples are placeholders; native wording is asked for. `planning_test.py` (13 postings × 2, 6
revisions × 2), `gpt-6.1-sol` low, judged by `gpt-6.1-sol` high, before → after: code checks
92.3% → 96.2%; extraction covered 92.3% → 92.3%, invented 3.8% → 3.8%, titles 100% both;
topics covered 84.6% → 92.3%, coherent 100% → 96.2%; revisions (unchanged prompt) applied 66.7%
→ 83.3%, kept 75.0% both; judge traps 62 of 62 both; $0.014 a plan both, 23 → 27 s. All within
the intervals; kept for rule 19.

## Question prompts: the topic tagged, native wording (2026-10-22, kept)

The question, option and re-generation requests now put the topic and subtopic (from the
company's posting or a reviewer) inside `<topic>`, marked as data like the existing questions,
and their system messages ask for wording a native speaker in the field would use, never
translated from English; "Write ONE" lost its capitals. `gpt-6.1-sol` low, judged by
`gpt-6.1-sol` high, against the 2026-10-20 runs (prompts unchanged since):

| Set | Keys | One defensible answer | Clarity | Relevance | Distractors | Price |
|---|---|---|---|---|---|---|
| 53 subtopics × 6, 2 multi (312 → 307) | 98.7% → 99.0% (97.2–99.7); multi 100% → 100% | 98.4% → 98.7% | 4.97 → 4.97 | 4.24 → 4.25 ± 0.11 | 2.88 → 2.93 ± 0.11 | $0.0029 → $0.0031 a question |
| Re-generation, 40 | 95–100% → 97.5% | 95–100% → 97.5% | 4.92–5.00 → 4.97 | 4.47–4.50 → 4.53 | 3.25–3.27 → 3.23 ± 0.27 | $0.25–0.33 → $0.35 |
| Other languages (71 → 72) | 100% → 100% | 100% → 98.6% | 5.00 → 4.99 | 3.85 → 3.67 ± 0.22 | 2.15 → 2.25 ± 0.24 | $0.23 → $0.21 |

Every metric within its interval; kept for rule 19 (company text tagged, native wording asked
for).

## The verifier's rewrites and new options through the Batch API (2026-10-22, kept)

A flagged question's rewrite and new options (and a broken key's replacement) now go through
OpenAI's Batch API at half price: the new question, then its options, each a batch request with
the same prompts, schemas and checks as the direct calls. `regenerate_test.py --mode rewrite`
and `--mode new-options` send those requests at once, on the fixed 40 of
`multi_questions.json`, judged by `gpt-6.1-sol` high. Rewrite, direct (2026-10-22) → batch
requests: written 40 → 40, keys 97.5% → 100% (91.2–100), clarity 4.97 → 4.97, relevance 4.53 →
4.53, distractors 3.23 → 3.27 (± 0.27); $0.35 → $0.33 at once, half that in a batch. New options
(no eval before; its first run): 40 written, keys 100%, distractors 2.85 ± 0.30, relevance 4.08.
Within the intervals; kept for the price.

## The eval gate before a pattern ships (2026-10-29, built)

`pattern_gate.py` writes a fresh set without and with a rule on the same subtopics and judges both
on every dimension and on the rule's own mistake (`judges/pattern_failure.md`, 12 of 12 on its
traps). No pattern is approved yet, so a dry run on a rule that isn't one ("The correct option is
much longer and more detailed than the others, which gives it away."), 16 subtopics of
`inputs.json` × 6 each way (2 multi), `gpt-6.1-sol` low, judged by `gpt-6.1-sol` high, without →
with:

| Mistake | Keys single | Keys multi | Clarity | Level fit | Distractors | Seconds |
|---|---|---|---|---|---|---|
| 0.0% (0.0–3.9) → 0.0% (0.0–3.9) | 95.3% (87.1–98.4) → 98.4% (91.7–99.7) | 100% (89.0–100) → 100% | 4.92 ± 0.08 → 4.97 ± 0.06 | 4.36 ± 0.17 → 4.26 ± 0.18 | 2.95 ± 0.20 → 2.98 ± 0.19 | 28.3 ± 2.1 → 28.0 ± 1.9 |

Nothing moved beyond the noise, and the mistake never showed without the rule: it doesn't ship,
as the gate says. $1.48, 538 s. No rule is in use (`QUALITY_RULES` is empty), so the prompts
read exactly as before.
