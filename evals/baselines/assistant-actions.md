# Assistant actions: baselines and their history

The runs of `assistant_actions.py`, the eval of the actions the in-app assistant prepares, by date,
from 2026-10-22 on; the first runs (2026-10-20 and 21) are in `assistant-actions-first.md`. Page
context and guides are in `assistant.md`, the rest of the evals' history in `README.md`, and the
newest numbers per metric in `../README.md`. Changes tried and not kept are in
`assistant-tried.md`.

Contents: [Mira](#mira-an-ai-assistant-that-says-so-2026-10-22-kept) ·
[A topic's question limit](#a-topics-question-limit-isnt-a-page-size-2026-10-22-kept) ·
[The turn's context](#the-turns-context-out-of-the-instructions-2026-10-22-kept) ·
[Strict tool schemas](#strict-tool-schemas-2026-10-22-kept) ·
[How to narrow a list](#how-to-narrow-a-list-cut-short-2026-10-22-kept) ·
[Fewer tools a turn](#fewer-tools-a-turn-chosen-by-a-routing-call-2026-10-23-kept) ·
[Handing over to a person](#handing-over-to-a-person-when-a-call-fails-2026-10-22-kept) ·
[The shared bank](#keeping-an-interviews-questions-out-of-the-shared-bank-2026-10-23-kept)

## Mira, an AI assistant that says so (2026-10-22, kept)

The same instructions change as in `assistant.md` (the assistant introduces itself as Mira, an
AI assistant, never a person). `assistant_actions.py`, 3 repeats, before
(`results/assistant_actions_mira-base.json`) and after (`…_mira-new.json`): task success 200/201,
99.5% (97.2–99.9), then 198/201, 98.5% (95.7–99.5); arguments, asked first, link and injection
safe 100% both times; judge traps 8 of 8; 21,440 then 21,970 tokens, $0.0022 then $0.0023 and
17.9 then 13.2 s a turn. No difference beyond the intervals: `e10` and `m05` failed once and
twice, cases that pass in other runs.

## A topic's question limit isn't a page size (2026-10-22, kept)

Every parameter named `limit` was capped at the tool's page size (20) and described as "Number
of items to return", so `set_topic_limit` couldn't give candidates more than 20 of a topic's
questions and read as paging. Only a query's `limit` is a page size now. A new case (e12: "only 8
questions from the Indexes topic") joins the set. `assistant_actions.py`, 2 repeats, `gpt-6-luna`
low, before → after: task success 100% (97.3–100) → 99.3% (96.0–99.9), arguments 100% both,
asked for the parent 100% → 94.4% (the known flaky e07, once), injection safe 100% both; e12 right
both times; $0.0022 a turn both. Within the intervals; kept (a correctness fix).

## The turn's context out of the instructions (2026-10-22, kept)

The user's name, the date, the company and the page moved from the system message to a tagged
`<context>` at the start of the new message (`assistant.md`). `assistant_actions.py`, 2 repeats,
`gpt-6-luna` low, against `results/assistant_actions_a1-topic.json` (`…_ctx.json`): task success
99.3% (96.0–99.9) both, arguments 100% both, asked for the parent 94.4% → 100% (82.4–100),
injection safe 100% both, judge traps 8 of 8; 21,900 tokens and $0.0022 a turn, 8.8 s. No
difference beyond the intervals; $0.37.

## Strict tool schemas (2026-10-22, kept)

Every tool goes to the model strict (each parameter required, an optional one as nullable; length
limits left to the code's check), but `update_email_preferences`, whose free map of values can't
be. `assistant_actions.py`, 2 repeats, against `results/assistant_actions_ctx.json`
(`…_strict.json`): task success 99.3% (96.0–99.9) both, arguments 100% both, links 100% both, asked
for the parent 100% → 94.4% (one turn of 18, its case still passing), injection safe 100% both,
judge traps 8 of 8; 21,600 tokens and $0.0022 a turn. The one failure (c04, a company named after
the user) passed 6 of 6 alone (`…_strict-c04.json`). No difference beyond the intervals; $0.39.

## How to narrow a list cut short (2026-10-22, kept)

A list cut at its tool's `max_items` said only `"more": true`; it now also says how to see the
rest (`narrow`): the tool's own filters (or asking the user) and, for a paged list, the next
offset. `assistant_actions.py`, 2 repeats, against `…_strict.json` (`…_narrow.json`): task
success 99.3% → 97.1% (92.7–98.9), within the intervals; arguments, links and injection safe
100% both; $0.0022 a turn. No list in the eval's fixtures is long enough to be cut, so no turn
read the hint: the four failures (a service that didn't answer, a topic not found, two asked
which company) passed 12 of 12 when run again (`…_narrow-recheck.json`). $0.43.

## Handing over to a person when a call fails (2026-10-22, kept)

A call that fails on prepza's side now tells the model, once a turn, not to retry, to say what
didn't work and to link the contact page (`show`, page `contact`). The model already stopped
after one failed call (0.8 a turn), so a second failure, the first threshold tried, never came:
the handover comes with the first. `assistant_handover.py` (new, 8 questions, 2 repeats, every
service down), with and without it (`results/assistant_handover_h4.json`): contact page linked
after a failure 0% (0–22.8) → 100% (75.7–100), never without one; no link written in the text
100% both (the first wording, "link the contact page", led to `[…](contact)` in the text in 5 of
16 answers, `…_h3.json`); stopped retrying and answered 100% both; $0.0017 → $0.0023 a turn.
`assistant_actions.py`, 2 repeats (`…_handover.json`): task success 98.5% (94.8–99.6), links,
arguments, asked first and injection safe 100%; its one failure was a local service that didn't
answer, which the handover answered as meant. $0.66 in all.

## Fewer tools a turn, chosen by a routing call (2026-10-23, kept)

Every turn offered all 88 tools (about 10,000 of a call's input tokens). Now one cheap call
(`ROUTING_MODEL`, `gpt-6-luna` at none) reads the new message with the conversation's last 4
messages and the page, and picks at most two of seven groups; the turn is offered the 13 core
tools, `show`, `sign_out` and those groups (15 to 47 tools). Unlike the 2026-10-20 trial
(`assistant-tried.md`) no `load_tools` step is needed: a turn has its group from its first call.
`assistant_actions.py`, 2 repeats, against `…_strict.json`, `…_narrow.json` and `…_handover.json`
(98.5–99.3%, 21,400–21,900 tokens, $0.0022 a turn):

| Run | Task success | Link | Asked first | Injection safe / read | Tokens, cost, seconds a turn |
|---|---|---|---|---|---|
| Routing on the message alone (`…_routed.json`) | 97.1% (92.7–98.9) | 17/18 | 18/18 | 100% / 85.3% | 12,800, $0.0013, 13.1 s |
| With the conversation (`…_routed2.json`) | 98.5% (94.8–99.6) | 18/18 | 18/18 | 100% / 85.3% | 12,600, $0.0013, 15.2 s |
| In the service (`…_routed-prod.json`) | 97.1% (92.7–98.9) | 16/18 | 18/18 | 100% / 85.3% | 12,700, $0.0013, 9.4 s |
| Groups named sharper (in use, `…_routed-prod2.json`) | **97.8% (93.7–99.2)** | **17/18** | **18/18** | **100% / 91.2%** | **12,500, $0.0013, 11.4 s** |

The message alone lost short replies ("The data analyst one.") to the wrong group; in the
service, "Create an API key" and question reports were missed until the groups named them. With
the routing call's tokens counted, a turn costs about 41% less, beyond the intervals; success
stays within them. `page_context.py` and `guides.py`, 2 repeats (`…_routed.json`), against
`…_ctx.json`: general correct with the page 88 → 84/102, scope 92 → 88, tools 78 → 84, page
checks 16/18 both, the guide called 10/10 both, $0.33 → $0.19 for the run; guides correct 39 →
39/40, complete 26 → 24, read the right one 38 → 40, linked 37 → 38, general correct 28 → 25/30,
$0.27 → $0.17. All within the judge's noise. $4.30 for the runs.

## Keeping an interview's questions out of the shared bank (2026-10-23, kept)

A new tool, `keep_questions_private` (the interview's `keep_private` setting, in the interview
setup group), and its case e13 ("Keep the Data Analyst interview's questions out of the shared
question bank."). `assistant_actions.py`, 2 repeats, 68 cases (`…_bank.json`): task success
94.2% (89.0–97.0) against 97.8% (93.7–99.2), within both intervals; e13 2 of 2, arguments 100%,
injection safe 100%, judge traps 8/8; 13,200 tokens, $0.0014, 11.4 s a turn. Of its 8 failures, 3
were OpenAI connection errors (i02, i04, i06) and e07 (a pass mark without an interview: it picked
one instead of asking) failed twice; run again with 3 repeats (`…_bank-recheck.json`), e07, i02,
i04, i06 and e13 passed 15 of 15. $0.30 in all.
