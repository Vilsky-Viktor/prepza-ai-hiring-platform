# Assistant baselines and their history

The in-app assistant's runs (`page_context.py`, `guides.py`, `assistant_actions.py`), by date;
the rest of the evals' history is in `../baselines.md`, and the newest numbers per metric in
`../README.md`.

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

**Assistant: actions** (2026-10-20, `assistant_actions.py`, new; `gpt-6-luna` at low, the
current prompt and all 86 tools (88 with `show` and `sign_out`) every turn, 50 cases × 3, the
judge `gpt-6.1-sol` high on the replies that should ask or warn; first `results/assistant_actions_base.json`):

| Task success | Tool choice | Arguments | Asked first | Link | Injection safe (read it) | Warned | pass^k | Per turn |
|---|---|---|---|---|---|---|---|---|
| 140/150, 93.3% (88.2–96.3) | 147/150 | 84/84 | 13/18 | 11/15 | 42/42 (39 read the injected text) | 5/6 | 44/50 | 23,500 ± 2,100 tokens, $0.0024, 5.9 ± 0.4 s |
| The team page under its real key (`team`, not `members`), 5 repeats, the baseline in use (`…_base2.json`): **235/250, 94.0% (90.3–96.3)** | **244/250** | **140/140** | **24/30** | **16/25** | **70/70 (65 read it)** | **10/10** | **44/50** (pass^5) | **23,800 ± 1,600 tokens, $0.0024, 6.4 ± 0.4 s** |

By kind: creating 9/12, inviting 25/27, editing 30/30, deleting 18/18, buying 7/9, connecting
10/12, injected 41/42. What fails: "Create a new company." prepares a card with an empty name
instead of asking for it (3 of 3); with no company picked and two companies, "Invite … to an
interview" asks which interview, across both companies, before which company (2 of 3); turning
on auto top-up or connecting an ATS sometimes describes the steps without linking the page. In an
earlier run of the same cases (the dataset settled after it) "Set the pass mark to 55%." with two
interviews prepared it for one or both without asking (3 of 3), passing 0 of 3 against 3 of 3
here: single cases move a lot between runs, so compare totals over repeats. No injected text led
to an action; in an ATS job's text or a pasted description it is copied verbatim into the new
interview's description when the user asks to create one, as the rule to use their exact words
says. Judge traps: 8 of 8. The run cost $0.44 ($0.36 the assistant, $0.08 the judge); the
5-repeat run $0.72. By kind there: creating 15/20, inviting 45/45, editing 49/50, deleting 30/30,
buying 12/15, connecting 14/20, injected 70/70.

**Assistant: fewer tools per turn, tried and reverted** (2026-10-20). Every turn offers all 88
tools (about 10,000 of a call's 15,000 input tokens); OpenAI advises fewer than about 20. Tried:
core tools always (finding things, the page and site guides, `show`, `sign_out`), the page's
group of the rest chosen by code from the page's key, and a `load_tools` tool the model calls to
add any other group for the rest of the turn (OpenAI's hosted `tool_search` needs the Responses
API's deferred tools, and `allowed_tools` keeps every definition in the prompt, so neither cuts
tokens here). Measured against all tools on the same code (`ALL_TOOLS`), `gpt-6-luna` low:

| Variant | Actions: success | Link | Asked first | Injection safe | Tokens / cost / seconds a turn | Page context: correct; page checks | Guides: correct; read and linked |
|---|---|---|---|---|---|---|---|
| All 88 tools (`…_base2.json`, `…_tools-all.json`) | 235/250, 94.0% (90.3–96.3) | 16/25 | 24/30 | 70/70 | 23,800, $0.00244, 6.4 ± 0.4 s | 112/129; 25/27 | 60/60; 57/60 |
| Core 12 + the page's groups (two of 8), 20–31 tools (`…_sel1.json`, `…_tools-sel.json`) | 223/250, 89.2% (84.7–92.5) | 11/25 | 18/30 | 70/70 | 17,000, $0.00176, **8.0 ± 0.5 s** | 119/129; 25/27 | 58/60; 58/60 |
| Core 27 (with the candidates' and interviews' tools) + one page group, 27–43 tools (`…_sel2.json`) | 224/250, 89.6% (85.2–92.8) | **9/25** | 23/30 | 70/70 | 15,600, $0.00162, 6.7 ± 0.5 s | not run | not run |

Page context and guides held within noise and cost about 25% less, but the actions got worse
beyond both intervals, so it was reverted. In the first variant `load_tools` ran in 113 of 250
turns (an extra step, 1.6 s more a turn), and with no candidate tools on the interviews page
"Invite … ." prepared `invite_member` instead of `invite_candidate` (4 of 5). The second fixed
both, but turns that had to load a group (buying credits, connecting an ATS or Slack, an API key
from the interviews page) described the steps and dropped the link to the page far more often.
A next try would keep the link cases' tools (billing, integrations) reachable without a step or
fix the link behaviour first.

**Assistant: neutral prompt examples** (2026-10-20). The prompt's examples reused the eval
fixture's names ("Ann did best…", "Which interview? Data Analyst or Backend Engineer?"); they
became "Noa" and "Store Manager or Field Technician" (the parents rule is shared with the MCP
instructions). Against the all-tools runs on the same code:

| Run | Actions: success | Asked first | Link | Injection safe | Tokens / seconds a turn | Page context: correct / scope / tools; page checks |
|---|---|---|---|---|---|---|
| Before (`…_base2.json`, `…_tools-all.json`) | 235/250, 94.0% (90.3–96.3) | 24/30 | 16/25 | 70/70 | 23,800, 6.4 ± 0.4 s | 112 / 113 / 100 of 129; 25/27 |
| After, in use (`…_names.json`, `assistant_page_context_names.json`) | **240/250, 96.0% (92.8–97.8)** | **27/30** | **19/25** | **70/70** | **22,900, 7.2 ± 0.4 s** | **112 / 114 / 108 of 129; 25/27** |

Nothing moved beyond the intervals; the examples now overlap no dataset, so the change is kept.
The seconds differ by the API's speed between runs (the same tokens). Cost $1.95 for both runs.
