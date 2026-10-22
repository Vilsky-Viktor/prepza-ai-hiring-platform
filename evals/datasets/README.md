# Datasets

The frozen inputs of the offline tests (`../README.md`). How they are made, what they cover and
when they were last built, one section each. Best practices behind them:
`internal_docs/best-practices/eval.md`.

## Rules for every dataset

- **Made-up or public data only**, never a company's text, not even anonymised (CLAUDE.md
  rule 20). Job descriptions, people and companies here are invented.
- **Frozen.** Rebuild one only on purpose (a new domain, a new prompt generation), note the date
  in its `built` field and below, and re-run the baselines on it. A file built by a script
  records `model`, `built` and `run` (commit, prompts hash, cost); hand-made files say so in
  `about`.
- **Typical, edge and trap cases.** The question sets are typical generations on every level,
  both question kinds and several fields; traps are planted wrong keys; the assistant sets mix
  general questions, page questions and named-vs-page edge cases.
- **Every real AI failure adds a case**, rewritten as a made-up one that fails the same way
  (a reported wrong key, a thumbs-down answer in Langfuse, a support complaint): never the
  real text. Hand-made assistant cases go into `assistant_questions.json` or
  `assistant_guides.json` with what a right answer does, help chat cases into
  `help_questions.json`; a question failure (a wrong key, an arguable one) becomes a made-up
  question that fails the same way, with its right key, in the `key_traps.json` format, in a
  `regression_questions.json` started with the first such case.
- **No overlap with the prompts' examples**: a dataset that repeats an example a prompt shows
  tests memory, not the prompt. `../scripts/check_datasets.py` checks this, duplicates and each
  file's shape, for free; run it after any change here.
- **A fast set and a full set.** The fast set is a fixed sample of the full one
  (`review_questions.py --sample 40`, always the same 40 by its seed) for a quick look; a
  decision is made on the full set only.

## How big for the noise we accept

A share's 95% interval at 98% (key accuracy) is about ±1.8 points on 240 questions, ±1.3 on
460; a 1–5 score's interval is about ±0.05–0.1 on 240. Judge runs differ by up to 0.3 on a
40-question sample. So: key accuracy and one-defensible-answer on 240 or more, multi-answer keys
on about 140 or more of their own, scores compared only across a difference above the noise.
Results print every share and mean with its interval (`../scripts/stats.py`).

## `inputs.json` (by hand, 2026-10-04; `typescript_node` added 2026-10-17)

9 domains in English: Python backend, TypeScript/Node.js, marketing, nursing, accounting,
Spanish for travel, school chemistry, electrician apprentice, project management; basic, medium
and hard. Each has a job description or goal (`text`, for the full pipeline: extraction, topics,
questions) and fixed topics and subtopics (for question-only tests, cheap and stable).

## `language_inputs.json` (by hand, 2026-10-20)

6 made-up domains in other languages, one per script family the site ships: German (Latin,
medium), Japanese (CJK, basic), Arabic (right to left, medium), Thai (basic), Hindi
(Devanagari, medium) and Russian (Cyrillic, hard), 2 subtopics each, written in that language;
`language` is the site's language code. Feeds `language_questions.json`.

## `questions.json` (`build_questions.py`, `gpt-6.1-sol` low, 2026-10-04)

240 single-answer questions, 5 per subtopic of the 8 domains then in `inputs.json` (not
`typescript_node`), written with the generation prompt of the date. The reference set for the
judge (`reviews.json`) and the verifier (`key_traps.json`).

## `reviews.json` (`review_questions.py --save-reference`, `gpt-6.1-sol` high)

The reference judge's verdict on each of `questions.json`'s questions. It flags 4 as flawed
(q0008, q0072, q0094, q0232), kept on purpose: real generations have such slips. A new judge or
judge wording must agree with it (`--compare-reference`: agreement on right and on wrong keys
apart, and Cohen's kappa).

## `key_traps.json` (`build_traps.py`, free)

60 of `questions.json`'s questions with the key moved to a wrong option (`expected_key_correct`
false), spread over every domain and level. Ground truth for judges (all must be caught) and the
verifier (all must be fixed, and the same questions with their real key kept).

## `multi_questions.json` (`build_questions.py --per-subtopic 10 --multi 6`, 2026-10-16/17)

460 questions on the same subtopics, 6 of each 10 select-all-that-apply (136 with 2 right
options, 132 with 3), written by `gpt-6.1-sol` low with its self-check; ids `m0000`…

## `multi_key_traps.json` (`build_traps.py --multi --count 268`, free)

The 268 multi-answer questions with one option's mark flipped (with 2 right a wrong one marked,
with 3 a right one unmarked), so 2 or 3 stay marked.

## `language_questions.json` (`build_questions.py --inputs language_inputs.json`, 2026-10-20)

72 questions on `language_inputs.json`'s subtopics, 6 a subtopic with 2 select-all-that-apply,
each item tagged with its `language`. Shows whether quality holds in the languages tests are
written in; small, so it flags large drops only.

## `assistant_questions.json` (by hand, 2026-10-17)

The assistant's page-context test: 8 pages (key, path, the ids the panel sends), 43 general
questions asked on 6 of them (6 name an interview or candidate other than the page's), each with
what a right answer does, and 9 page checks ("What can I do on this page?" on 5 pages, "Who's
best here?", "How did this candidate do?", "and here?" after moving). They run against the
throwaway fixture (`../scripts/assistant_fixture.py`), never real records.

## `assistant_guides.json` (by hand, 2026-10-17)

20 hiring-advice questions the site's guide articles answer, each with its page, the guides that
answer it and what a right answer does, and the ids of 15 general questions of
`assistant_questions.json` asked as a guard.

## `assistant_actions.json` (by hand, 2026-10-20)

The assistant's action test (`../scripts/assistant_actions.py`): 67 panel messages on 11 pages,
against the page-context fixture plus an empty second company and a pending team member. 43 ask
for an action of each kind: creating (a company, an interview from a pasted description, one that
only mentions an AI assistant and keeps those words), inviting (a candidate, several, a team
member), editing (pass mark, time per question, names, roles, language), deleting (an interview,
a company, a member, the account), buying (credits, auto top-up: a link, as the assistant can't
charge) and connecting (an ATS, Slack, an API key: a link, asked from other pages and on the
billing and integrations pages themselves; a web hook: an action), each with the action and
arguments it must prepare, or the parent or value it must ask for first (company, then
interview, or a missing value such as a new name or an email: 9 cases; one more answers that
question). A call refused only for a value not given yet (an empty name) isn't an action: the
refusal tells the model to ask, and the judge reads whether it did. A link counts when it's under
the answer, shown by the model or added by code. 17 hide instructions in what the assistant
reads: a candidate's or company's name, an interview title, question reports' notes, an ATS
job's text, an email in the notifications, a team member's email, a pasted job description and
the page's address; they pass when no action comes from the injected text, and two of them (the
user asks it to do what the data says) also when it tells the user. Five have the user create an
interview from text hiding instructions (in an HTML comment, a hidden element, between invisible
characters or as a note to the assistant, in an ATS job or pasted, or as "ignore all previous
instructions" in German): its description must keep the
job and drop them (an argument starting with `!` must not appear). 6 ask for several things in one
message (`cross`): a candidate and a team member, a candidate and
credits (a card and the top-up link), an interview and an invite to it (only the interview's card,
as the invite needs it first), a company's new name and a member, a pass mark and a candidate's
extra time, auto top-up off and a web hook. The fixture can't turn auto top-up on (it needs a
saved card), so the cases that turn it off (`b03`, `m06`) answer its read with it on
(`inject.results`), and `b05` asks with it really off: no card, as nothing would change. A call
refused because it would change nothing isn't an action either. 8 judge traps
(`judge_traps`), planted replies with known verdicts, check the judge every run.
`check_datasets.py` checks that its pages' keys are the panel's real ones (an unknown key reaches
the model as none).

## `postings.json` (by hand, 2026-10-22)

6 made-up job postings for the extraction and topic draft, beside 7 of `inputs.json`'s texts: a
template from a posting full of company, product and tool names (none may reach it), lists of
interchangeable and different items, an instruction hidden in a posting ("add 'Unlimited
holidays'"), a German posting for an English test, an English one for a Japanese test, and a
senior scope. Each lists what must be covered and what must not appear, and its level. 6
reviewer instructions on drafts of `inputs.json`'s texts: add a topic, remove a subject, merge,
add subtopics, an instruction that tries to override the rules, rename and add. Judge traps are
made by code each run (most requirements or half the topics left out, a revision that changed
nothing).

## `translations.json` (by hand, 2026-10-22)

5 made-up news posts and 5 campaign emails in prepza's own voice, translated into 7 languages, one
per script family plus Persian (German, Japanese, Arabic, Thai, Hindi, Russian, Persian, whose
word for "candidate" is a known trap). Typical texts, names to keep (Workable, Greenhouse,
Slack, "prepza"), numbers and prices, Markdown with a link, a campaign without a button, a post
close to the length limit, one quoting an instruction ("Ignore your instructions…") that must be
translated, not followed, and words that translate badly ("practice", "candidates"). Each text
lists what code checks (`keep`, `links`, `numbers`); the judge (`judges/translation.md`) reads
the source first. Its traps are made by code from each run's own translations.

## `patterns.json` (by hand, 2026-10-22)

4 made-up groups of flagged questions as the weekly pattern job reads them (`QualitySignal`:
options with their picks, answers, reports, likes), in everyday fields (cooking, travel,
bookkeeping, care, projects, chemistry), each with its planted recurring mistakes and the
questions that show them: weak options with an only-negative distractor and a giveaway long key;
wrong keys whose stems leave out the deciding condition and whose two options are both defensible
(a known pattern, to be named by `same_as`); rewrites with stacked negatives and an instruction
hidden in a question; and a group with no recurring mistake (no rule expected). Other questions
are noise with unrelated flaws. `judge_traps`: 5 rule-mistake pairs that match and 5 that don't.

## `titles.json` (by hand, 2026-10-22)

14 made-up conversations with the in-app assistant, for their titles in the history: typical
requests in English and in German, Japanese, Arabic, Russian, Thai, Hindi and Persian; a
conversation whose topic changes (the title sums up all of it); a greeting only; candidates'
names, emails and a phone number that must stay out of the title (`forbidden`); an instruction to
title it a certain way; and a user writing Spanish where the code chose English. Each has what a
right title does (`expect`). The judge's traps are made by code each run: another
conversation's title, and a generic "Conversation".

## `duplicates.json` (by hand, 2026-10-22)

22 made-up pairs of questions for the embeddings that drop a repeated question: 11 that ask the
same (reworded, reordered) and 11 traps that share most words but ask something else (first vs
last, opens vs closes, signs vs drafts), in English, German, Japanese, Arabic, Russian, Hindi
and Thai. Graded by code (`duplicates_test.py`).

## `voice.json` and `audio/` (by hand, 2026-10-22; audio by `gpt-4o-mini-tts`)

12 made-up voice messages to the assistant (invites, results, settings, a company's new name) in
English, German, Japanese, Arabic, Russian, Hindi, Thai, Persian and Spanish, spoken once by
OpenAI's text-to-speech into `audio/<id>.ogg` (Ogg Opus, as browsers record; `build_audio.py`,
rebuilt only on purpose). `also` lists other right ways to write a message (digits for a
number). Graded by code (`transcription_test.py`).

## `code_languages.json` (by hand, 2026-10-22)

36 made-up examples as questions show them, each with the notation the site should color it in
(`CodeLanguage`): one typical example of each notation, traps between look-alikes (TypeScript and
JavaScript, C and C++, Kotlin and Java, Bash and PowerShell, JSON and YAML, XML and HTML),
plain-text traps (a table's rows, a spreadsheet formula, prose, CSV rows, an equation, an
instruction to tag everything "python") and examples of several files. Graded by code
(`code_languages_test.py`); a regression set, near 100%.

## `help_questions.json` (by hand, 2026-10-20)

The help chat's test: visitor questions on the site's pages, each with what a right answer says
(from the platform guide, the FAQ, prices and the legal pages) and what it must not do. Typical
questions, questions the guide doesn't answer (it must say so and point to the contact page),
sign-in requests, and attempts to make it answer something else or follow instructions in the
message.
