# Baselines of the small utility prompts

The runs behind the README's numbers for translations, code-language tags, the weekly quality
patterns and the assistant's conversation titles, by date; the rest are in `../baselines.md`.

## Code-language tags: a role and tagged examples (2026-10-22, kept)

The tagging job's prompt (`prompts/code_languages.py`) moved its task into a system message that
starts with a role, and the examples (tests' text) into the user's message inside `<examples>`,
read as data. `code_languages_test.py`, `code_languages.json`, 36 examples × 3, `gpt-6.1-sol`
low, graded by code, before → after: right 100% (96.6–100) → 100% (96.6–100), skipped 0 → 0;
$0.0181 → $0.0186 and 8.0 → 7.2 s a batch. No difference; kept for rule 19 (a role, the
examples as data, the "ignore the list" trap still tagged `text`).

## Translations: a role, tagged text, the language last (2026-10-22, kept)

News and campaign translations (`prompts/translations.py`, `news.py`, `campaigns.py`) moved from
one user message to a system message that starts with a translator's role and holds every rule,
and a user message with the text inside tags (read as data, never followed) and the target
language last. The rules no longer contradict each other (campaigns' text is Markdown; "plain
text only" is now news' rule) and ask for only the translation in each field.
`translations_test.py`, `translations.json` (10 texts × 7 languages), `gpt-6.1-sol` low, judged
by `gpt-6.1-sol` high, before → after:

| Run | Code checks | Faithful | Native | One language | Judge traps | Price, time a translation |
|---|---|---|---|---|---|---|
| Before | 100% | 88.6% (79.0–94.1) | 94.3% (86.2–97.8) | 100% | 97 of 97 | $0.0021, 4.9 s |
| After | 100% | 90.0% (80.8–95.1) | 98.6% (92.3–99.7) | 100% | 97 of 97 | $0.0023, 5.2 s |

No difference beyond the intervals; kept for rule 19 (a role, the text as data, no
contradiction). The dataset's n01 no longer expects "ATS" kept in Latin letters: it's a term,
not a name, and Arabic writes it out (the one code-check failure after the change).

## Quality patterns: a role, tagged questions, a rule for useless rules (2026-10-22, kept)

The weekly pattern job's prompt (`prompts/patterns.py`) moved from one user message to a system
message that starts with a reviewer's role and holds the task (fixed, so it caches), and a user
message with the flag's meaning, the known patterns and the questions inside tags, read as data.
One rule was added for a measured failure: every wrong-key run proposed "the marked answer is
wrong", which tells a writer nothing (a rule must say what in the writing caused it).
`ProposedPatterns.patterns` got its description. `patterns_test.py`, `patterns.json` (4 groups
× 3), `gpt-6.1-sol` medium, judged by `gpt-6.1-sol` high, before → after: planted found 100%
(79.6–100) both; kept rules supported 85.2% (67.5–94.1) → 100% (84.5–100); no rule when none 3 of
3 both; known named 3 of 3 both; nothing from the hidden instruction; judge traps 10 of 10 both;
$0.018 → $0.016 and 34 → 30 s a run. Kept: cheaper, and the useless rule is gone.

## Assistant titles: a role, the conversation as data, structured output (2026-10-22, kept)

The title prompt (`assistant/app/prompts/titles.py`) gained an editor's role and says why names
stay out (others in the company see the history); the conversation goes in the user's message
inside `<conversation>`, read as data; the title comes back as structured output
(`ConversationTitle`, 60 tokens at most instead of 40 for its JSON); and code cuts a long title at
a word's end. `titles_test.py`, `titles.json` (14 × 3), `gpt-6-luna` at none, judged by
`gpt-6.1-sol` high, before → after: code checks 88.1% (75.0–94.8) → 97.6% (87.7–99.6), the
Arabic title naming the candidate (2 of 3) gone; sums up 90.5% (77.9–96.2) → 88.1% (75.0–94.8);
right language 100% both; natural 95.2% → 100%; judge traps 11 of 11 both; $0.00002 → $0.00003
and 2.1 → 2.8 s a title. Kept: the privacy failure is gone, nothing worse beyond the intervals
(the remaining misses are a greeting titled "Hiring Assistance" and one partial summary).

## Translations through the Batch API (2026-10-22, kept)

Translations of news posts and campaigns no longer call the model at once: each language goes in
the next OpenAI batch at half price, with the same prompt, a strict schema built as the direct
call builds it, and the same limits checked on the reply. `translations_test.py` now sends those
batch requests at once (`batch_direct.py`); `translations.json`, 70 translations, `gpt-6.1-sol`
low, judged by `gpt-6.1-sol` high, direct call → batch request: code checks 100% both; faithful
90.0% (80.8–95.1) → 88.6% (79.0–94.1); native 98.6% (92.3–99.7) → 97.1% (90.2–99.2); one
language 100% both; judge traps 97 of 97 both; $0.158 both at once, so $0.079 in a batch. Within
the intervals; kept for the price (the user approved the wait: up to a day, usually an hour).
