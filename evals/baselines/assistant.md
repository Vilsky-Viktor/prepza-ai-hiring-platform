# Assistant baselines and their history

The in-app assistant's runs of `page_context.py` and `guides.py`, by date; the runs of
`assistant_actions.py` are in `assistant-actions.md`, the rest of the evals' history in
`../baselines.md`, and the newest numbers per metric in `../README.md`.

## Page context (2026-10-17)

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

## Guides (2026-10-17)

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

## Price fields in the user's currency (2026-10-21, kept)

The price catalog's fields changed with currencies (`from_dollars` became `from_cents`, a pack's
`title` went; amounts are in the user's saved currency), and `get_auto_top_up` gained `currency`
and `prices`. `page_context.py --only g23,g26` (the two price questions), 3 repeats, before and
after: correct 6/6 and 6/6 with and without the page context both times, right scope 6/6, no
wins or losses; $0.03 a run plus $0.04 judging. No difference; kept, as the old field names no
longer exist.
