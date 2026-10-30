# Baselines of the small utility prompts

The runs behind the README's numbers for translations, code-language tags, the weekly quality
patterns, the assistant's conversation titles, voice messages, voice mode's answer matching and the
shared bank's filter, by
date; the rest are in
`README.md`.

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

The title prompt (`assistant/src/assistant/prompts/titles.py`) gained an editor's role and says
why names stay out (others in the company see the history); the conversation goes in the user's
message inside `<conversation>`, read as data; the title comes back as structured output
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

## Voice messages: `gpt-transcribe` instead of `gpt-4o-mini-transcribe` (2026-10-29, kept)

OpenAI shuts `gpt-4o-mini-transcribe` (and `whisper-1`, `gpt-4o-transcribe`) down on
2027-02-26 and recommends `gpt-transcribe` for recorded speech; it takes the language as
`languages` (a list) and reports the audio's seconds, not tokens. `voice.json` grew to all 23
interface languages (26 messages, audio rebuilt; v03 also accepts "70 percent"), 3 repeats,
`transcription_test.py`, before → after: heard right 100% (95.3–100) both; character errors
0.4% ± 0.3 both (paired per message −0.0% ± 0.5); right script 100% both; median 2.9 → 2.8 s.
Price $0.003 → $0.0045 a minute, about $0.0003 → $0.0004 a message. Kept: as accurate, and the
old model is going away; every language code is accepted (Filipino as `tl`).

## Voice messages: audio by `gpt-realtime-2.1-mini` instead of `gpt-4o-mini-tts` (2026-10-29, kept)

OpenAI shuts its text-to-speech models (`gpt-4o-mini-tts`, `tts-1`, `tts-1-hd`) down on
2027-01-06 and names `gpt-realtime-2.1-mini` (Realtime API) as the replacement
(developers.openai.com/api/docs/deprecations). `voice.json`'s 26 clips rebuilt once with it
(voice `marin`, "Say exactly the following" with no context, PCM encoded to Ogg Opus by ffmpeg),
`transcription_test.py` on `gpt-transcribe`, 3 repeats, before → after: heard right 100%
(95.3–100) → 98.7% (93.1–99.8); character errors 0.4% ± 0.3 → 0.7% ± 0.4; right script 100%
both; median 2.8 → 2.9 s; $0.0004 → $0.00035 a message. Within the noise and above the 95%
target; the one miss is v14 (Filipino, "aplikanteng" heard as "aktibong", 1 of 3). The old clips,
rerun the same day, still gave 100% / 0.4%. Two earlier tries were dropped: the message sent as a
user turn (voice `alloy`, then `marin`) let the model drift (Thai and Filipino words misspoken,
an Italian clip opening with "Ecco come suona la frase"), 92.3–96.2% heard right.

## Shared question bank filter: first prompt (2026-10-30, kept)

A new prompt (`prompts/bank_filter.py`: a role, the question tagged as data, keep it out when in
doubt) after a code check for emails and web addresses. `bank_filter.json` (55), 3 repeats,
`bank_filter_test.py`: `gpt-6.1-sol` low and `gpt-6-luna` none both 0 leaks, private kept out
100% (95.1–100), general passed 96.7% (90.7–98.9); $0.159 and 2.4 s a run of 165 checks on
`gpt-6.1-sol`, $0.008 and 1.8 s on `gpt-6-luna`. The one miss on both is b54 (a generic "our
warehouse counts stock every Friday", kept out: the cautious side). Kept on `gpt-6.1-sol` low: a
checker runs on a strong model (`.claude/rules/ai.md`), a leak costs far more than the call, and
each question is checked once. On 150 local companies' questions (`--local`, not committed) it
passed all 150 (97.5–100): generated from job texts, they named no organisation or person.

## Voice mode's answer matching: first prompt (2026-10-30, kept)

A new prompt (rounds' `prompts/voice_match.py`: a listener's role, the four intents, the question
and the reply tagged as data, unclear when in doubt; never the answer key) with code checks after
it (`helpers/voice_match.py`: one option on a single-answer question, a yes or no only while a
choice waits). `voice_answers.json` (153 answers in English, Spanish, German, French, Portuguese
and Italian; 35 also spoken, with accents and noise, heard by `gpt-transcribe` first),
`voice_answers_test.py`, `gpt-6-luna` at effort none:

| Run | Right as text | Wrong matches (text) | Right spoken | Wrong matches (spoken) | Price, time |
|---|---|---|---|---|---|
| First prompt, 1 repeat | 100% (97.6–100) | 0% | 91.4% (77.6–97.0) | 2.9% (1 of 35) | $0.022 a run, 2.0 s median |
| With the unclear-part rule, 2 repeats | 100% (98.8–100) | 0% (0.0–1.2) | 92.9% (84.3–96.9) | 0% (0.0–5.2) | $0.045 a run, 2.4 s median, 3.6 s p90 |
| Other examples in the prompt, 2 repeats (reverted) | 99.3% | 0% | 92.9% | 1.4% (1 of 70) | $0.045 a run, 2.3 s |
| The rule as "every part must be related", 3 repeats (kept) | 99.6% (98.4–99.9) | 0% (0.0–0.8) | 94.3% (88.1–97.4) | 0% (0.0–3.5) | $0.068 a run, 2.0 s median, 3.2 s p90 |

The one wrong match of the first run was fr19 spoken: "Git et Subversion" heard as "Dub and
subversion", matched to Subversion alone; the rule added after it ("a part that seems to name an
option but can't be related to one: unclear") turned it unclear, but not every time: with other
examples in the prompt the same miss came back once, and "see" alone went unclear without its
example. The rule now says every part that names an option must be related to one, or the whole
reply is unclear; the examples are the first ones again. Text misses left: "dee" and "sure" (1 of
3 each), unclear. Every spoken miss left is the
hearing, not the matching: a one-word "oui" or "sim" heard as nothing, and "é a C" heard as "E,
A, C"; each is unclear, so the candidate says it again or taps. About $0.0002 a spoken answer
(hearing $0.00015, matching $0.00004), so about $0.01 for a 40-question interview with its
confirmations. Not measured: real candidates' microphones and rooms.

The reading aloud (`gpt-4o-mini-tts`, the speech endpoint, which reads the text and nothing
else) has no eval: the code builds the script. OpenAI shuts the model down on 2027-01-06 and names
the Realtime API as the replacement; a conversational audio model tried as a stand-in
(`gpt-audio-mini`, asked to read a question word for word) answered it instead ("La risposta
corretta è B"), so the switch needs an eval that compares what is said with the script before it
ships.
