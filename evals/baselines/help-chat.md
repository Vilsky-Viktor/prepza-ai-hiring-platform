# Help chat baselines

Each change to the help chat (the signed-out and in-app help, `help_chat.py`) with the runs behind
it; the newest numbers are summed up in `../README.md`, the first baseline in `README.md`.

Contents: [Help chat: a tighter rule for what the information doesn't say (2026-10-20, reverted)](#help-chat-a-tighter-rule-for-what-the-information-doesnt-say-2026-10-20-reverted) ·
[Help chat: currencies in its guide (2026-10-21, kept)](#help-chat-currencies-in-its-guide-2026-10-21-kept) ·
[Help chat: four more currencies (2026-10-21, kept)](#help-chat-four-more-currencies-2026-10-21-kept) ·
[Help chat: automatic top-up's pause and price notice (2026-10-21, kept)](#help-chat-automatic-top-ups-pause-and-price-notice-2026-10-21-kept) ·
[Help chat: Mira, an AI assistant that says so (2026-10-22, kept)](#help-chat-mira-an-ai-assistant-that-says-so-2026-10-22-kept) ·
[Help chat: the reply's language chosen by code, the visitor's messages as data (2026-10-22, kept)](#help-chat-the-replys-language-chosen-by-code-the-visitors-messages-as-data-2026-10-22-kept) ·
[The scope rule names no language of its own (2026-10-22, kept)](#the-scope-rule-names-no-language-of-its-own-2026-10-22-kept) ·
[Help chat: the shareable link on the Settings tab (2026-10-23, kept)](#help-chat-the-shareable-link-on-the-settings-tab-2026-10-23-kept) ·
[Help chat: moved from rounds to the assistant (2026-10-29, kept)](#help-chat-moved-from-rounds-to-the-assistant-2026-10-29-kept) ·
[Help chat: the page guide's contact card (2026-10-29, kept)](#help-chat-the-page-guides-contact-card-2026-10-29-kept) ·
[Help chat: allowed domains only for the SDK (2026-10-29, kept)](#help-chat-allowed-domains-only-for-the-sdk-2026-10-29-kept) ·
[Help chat: two brand fonts (2026-10-29, kept)](#help-chat-two-brand-fonts-2026-10-29-kept)

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

## Help chat: the page guide's contact card (2026-10-29, kept)

Every page guide's dialog now ends with a "contact us" button to the contact page, for a problem,
an idea or a missing feature, and the help chat's guide says so. `help_chat.py`, 25 × 3,
`gpt-6-luna` at none, judged by `gpt-6.1-sol` high, before (`results/help_chat_pagehelp-base.json`)
→ after (`…_pagehelp-new.json`): passed 96.0% (88.9–98.6) → 100% (95.1–100); made up 4.0% →
0.0%; sign-in marker 100% both; language 3 → 6 of 6 (h17's invented retake limit didn't come
up). Within the noise; kept so the guide says what is true. $1.66 and $1.58.

## Help chat: allowed domains only for the SDK (2026-10-29, kept)

The help chat's guide now says an API invite's return address only has to be https (http on
localhost while testing), the SDK's allowed domains only govern embedding, and the API and web
hooks are limited by IP per key. `help_chat.py`, 25 × 3, `gpt-6-luna` at none, judged by
`gpt-6.1-sol` high, before (`results/help_chat_returnurl-base.json`) → after
(`…_returnurl-new.json`): passed 97.3% (90.8–99.3) → 100% (95.1–100); made up 4.0% → 0.0%;
sign-in marker 100% both. Within the noise; kept so the guide says what is true. $1.58 after.

## Help chat: the average time per question (2026-10-29, kept)

The help chat's guide now says the test's setting is the average time per question: each
question gets its own time from it (short questions less, longer ones and code more, from half
to twice the average), the total stays the questions times the average, and extra time adds to
the average; the interview page guides say the same. `help_chat.py`, 25 × 3, `gpt-6-luna` at
none, judged by `gpt-6.1-sol` high, before (`results/help_chat_returnurl-new.json`, the same code
otherwise) → after (`…_fitted-times-new.json`): passed 100% (95.1–100) → 97.3% (90.8–99.3); made
up 0.0% → 1.3%; sign-in marker 100% both; the misses are h12's poem not declined (twice) and
h17's known invented retake limit, neither about timing. Within the noise; kept so the guide
says what is true. $1.59.

## Help chat: two brand fonts (2026-10-29, kept)

The Brand tab's line now says a company picks two fonts, one for titles and one for the text,
each from Poppins, Geist and about twenty popular web fonts. `help_chat.py`, 25 × 3, `gpt-6-luna`
at none, judged by `gpt-6.1-sol` high, against the fitted-times run just before
(`results/help_chat_fitted-times-new.json`) → after (`…_two-fonts.json`): passed 97.3%
(90.8–99.3) → 96.0% (88.9–98.6); made up 1.3% → 4.0%; sign-in marker 100% both; every miss is
h17's known invented retake limit (3 of 3), not about brands. Within the noise; kept so the guide
says what is true. $1.62.

## Help chat: answer patterns (2026-10-29, kept)

The candidate page's guide, the FAQ and the help chat's guide now say that a finished candidate's
report shows two answer-pattern signals (times about the same on every question; hard questions
right while easy ones were wrong) and questions to ask in a live interview. `help_chat.py`,
25 × 3, `gpt-6-luna` at none, judged by `gpt-6.1-sol` high, against the two-fonts run just before
(`results/help_chat_two-fonts.json`) → after (`…_answer-patterns.json`): passed 96.0%
(88.9–98.6) → 97.3% (90.8–99.3); made up 4.0% → 2.7%; sign-in marker 100% both; who-are-you
18 of 18; the misses are h17's known invented retake limit (2 of 3), not about integrity. Within
the noise; kept so the guides say what is true. $1.75.

## Help chat: run again for the feedback cases (2026-10-29, no change)

Run again when thumbs-down answers became a source of feedback cases (`disliked_answers.py`,
`--dataset help_feedback.json`); none exist yet (no thumbs down in Langfuse or locally), so this
is the hand-written set, 3 repeats: passed 98.7% (92.8–99.8), made up 4.0% (1.4–11.1), sign-in
marker 100%; identity 18/18. Misses: h04 twice (says viewers see billing), h17 once (invents a
one-attempt limit). Within the noise of the last run. $1.75 (the judge $1.72).

## Help chat: an interview's notes (2026-10-30, kept)

The platform guide, the FAQ and the page guides now name the interview's Notes tab, the counts
beside a company's menu pages, and API keys that read and add notes. `help_chat.py`, 25 × 3,
`gpt-6-luna` at none, judged by `gpt-6.1-sol` high (`results/help_chat_notes-docs.json`), against
the feedback-cases run: passed 98.7% (92.8–99.8) → 96.0% (88.9–98.6); made up 4.0% → 2.7%
(0.7–9.2); sign-in marker 100% both; identity 18 of 18. Misses: h17's known invented retake limit
(2 of 3) and h12 once (a poem request not declined); none about notes or menus. Within the
noise; kept so the guides say what is true. $1.73.

## Help chat: API keys in the action log (2026-10-30, kept)

The platform guide, the FAQ and the action log's page guide now say that an API key's actions
show under the key's name (and a deleted key's as such). `help_chat.py`, 25 × 3, `gpt-6-luna` at
none, judged by `gpt-6.1-sol` high (`results/help_chat_key-author.json`), against the notes run:
passed 96.0% (88.9–98.6) → 98.7% (92.8–99.8); made up 2.7% → 1.3% (0.2–7.2); sign-in marker
100% both; identity 18 of 18. Misses: h17's known invented retake limit once and one language
case. Within the noise; kept so the guides say what is true. $1.35.

## Help chat: voice mode (2026-10-30, kept)

The platform guide, the FAQ and the interview settings' and preview's page guides now describe
voice mode (Mira reading each question aloud, answers by voice or tap, the six languages, the
voice never kept) and quote the multi-answer tag as candidates now see it ("Pick multiple
options"). `help_chat.py`, 25 × 3, `gpt-6-luna` at none, judged by `gpt-6.1-sol` high
(`results/help_chat_voice-mode.json`), against the API-keys run: passed 98.7% (92.8–99.8) → 96.0%
(88.9–98.6); made up 1.3% → 4.0% (1.4–11.1); sign-in marker 100% both; identity 18 of 18.
Misses: h17's known invented retake limit (3 of 3); none about voice mode. Within the noise;
kept so the guides say what is true. $1.79.

## Help chat: Open to offers and the Discover tab (2026-10-30, kept)

The help chat's prompt, the FAQ (Open to offers, UK and US), the page guides (the interview's
Discover tab, settings, practice results) and the privacy policy and terms now cover a
candidate's own interview mode, the Discover tab and Open to offers. `help_chat.py`, 25 × 3,
`gpt-6-luna` at none, judged by `gpt-6.1-sol` high (`results/help_chat_offers-discover.json`),
against the voice-mode run: passed 96.0% (88.9–98.6) → 96.0% (88.9–98.6); made up 4.0% → 2.7%
(0.7–9.2); sign-in marker 100% both; identity 18 of 18. Misses: h17's known invented retake
limit (2 of 3) and h12 once (two sentences where one was asked); none about offers or Discover.
Within the noise; kept so the guides say what is true. $2.04 (the judge $2.01).

2026-10-30, the invite dialog no longer sets a candidate's mode (only their page does): passed
98.7% (92.8–99.8), made up 2.7% (0.7–9.2), sign-in marker 100%, identity 18 of 18. Misses: h17's
known invented retake limit and h02 once (generation limits). Within the noise. $1.98.

2026-10-30, voice mode's question time runs while Mira reads it (the guide's "starts once the
reading ends" reworded, the whole test as long as in click mode): passed 97.3% (90.8–99.3), made
up 2.7% (0.7–9.2), sign-in marker 100%, identity 18 of 18 (`results/help_chat_voice-clock.json`).
Misses: h17's known invented retake limit (2 of 3). Within the noise; none about
voice mode. $1.97.

2026-10-30, the per-company daily preview limits (click and voice mode) and the interview cap
(at most 60 questions per candidate over all topics, 10 a topic by default, fewer past 6 topics)
in the guide and the topics page guide, one run for both: passed 96.0% (88.9–98.6), made up 2.7%
(0.7–9.2), sign-in marker 100%, identity 18 of 18 (`results/help_chat_question-cap.json`).
Misses: h17's known invented retake limit (1 of 3), h12 twice (two sentences where one was
asked) and h06 once (deletion without "once the candidate started"); none about previews or the
cap. Within the noise; kept so the guides say what is true. $1.79.

2026-10-30, the trust page (the footer's company column and its page guide) and the owner's
bias-audit export on the Action log page (what the CSV holds, no data on sex, race or ethnicity,
the daily limit from `BIAS_AUDIT_EXPORTS_PER_DAY`) in the guide, page guides and FAQ: passed 96.0%
(88.9–98.6), made up 5.3% (2.1–12.9), sign-in marker 100%, identity 18 of 18
(`results/help_chat_trust-bias-audit.json`). Misses: h17's known invented retake limit (3 of 3)
and h04 once (billing for viewers); none about the trust page or the export. Within the noise;
kept so the guides say what is true. $1.90.
