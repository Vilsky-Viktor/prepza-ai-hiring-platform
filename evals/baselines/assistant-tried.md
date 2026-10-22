# Assistant: changes tried and not kept

Changes to the in-app assistant measured with `assistant_actions.py` (and, where noted, the page
context and guides evals) that did no better and were reverted or removed, by date; what is in
use is in `assistant-actions.md` and `assistant.md`.

Contents: [Fewer tools per turn](#fewer-tools-per-turn-tried-and-reverted-2026-10-20) ·
[Domain agents](#domain-agents-tried-and-removed-2026-10-21) ·
[Fuller tool descriptions](#fuller-tool-descriptions-tried-and-reverted-2026-10-22)

## Fewer tools per turn, tried and reverted (2026-10-20)

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

## Domain agents, tried and removed (2026-10-21)

**Assistant: domain agents, tried and removed** (2026-10-21, `assistant_actions.py`, `gpt-6-luna`
low, judge `gpt-6.1-sol` high, 66 cases × 5). Tried: a main agent with the common reads (17 tools:
companies, interviews, candidates, results, balances, the help, `get_updates`), `show`,
`sign_out` and one `delegate_<domain>` tool per domain (candidates, interviews, company and team,
billing, integrations, account); each domain agent got only its own tools (5 to 19), a few shared
finders and `show`, read the main agent's context, the conversation and its brief (the task and
the company's and interview's ids) as data, prepared the cards as the user and handed its reply
back; parts in several domains ran at once; each domain agent's calls traced under their own span
and priced. Six cases asking for several things in one message (`cross`: a candidate and a team
member, a candidate and credits, an interview and an invite to it, a new name and a member, a
pass mark and extra time, auto top-up off and a web hook) were added for it, with a routing check
(each expected action's domain agent called). Both arms on the same code, one after the other:

| Run | Task success | Arguments | Asked first | Link | Injection safe | Cross | pass^5 | Tokens / cost / seconds a turn |
|---|---|---|---|---|---|---|---|---|
| One agent, first pair (`…_sa-single.json`) | 320/330, 97.0% (94.5–98.3) | 187/187 | 41/45 | 42/45 | 85/85 | 24/30 | 90.9% | 21,200, $0.00217, 8.1 ± 0.4 s |
| Domain agents, first pair; the turn ended at the first card (`…_sa-sub.json`) | 323/330, 97.9% (95.7–99.0) | 185/185 | 43/45 | 45/45 | 85/85 | 25/30 | 95.5% | 12,700, $0.00135, 7.2 ± 0.4 s |
| One agent, final, with the link-beside-a-card fix (`…_final-single.json`, in use) | **323/330, 97.9% (95.7–99.0)** | **184/184** | **44/45** | **45/45** | **85/85** | **25/30** | **95.5%** | **23,700, $0.00242, 8.7 ± 0.5 s** |
| Domain agents, final: the main agent reads every delegate's result, delegates at once (`…_final-subagents.json`) | 321/330, 97.3% (94.9–98.6) | 183/186 | 44/45 | 44/45 | 85/85 | 29/30 | 87.9% | 17,000, $0.00178, 13.8 ± 1.0 s |

Routing was right in 100% of the final run's delegated actions (0.85 delegates a turn). The shipping
bar was success at least the one agent's with links improved, injection-safe 100%, at most about
9 s and no dearer a turn: the domain agents matched on success and injection and cost 27% less, but
links had nothing left to improve (the one agent reached 45/45 with the page-link fixes), pass^5
fell and turns took 13.8 s (21 s on the cross cases, against 12.8 s): a delegated action is at least
three model calls in a row (main, domain agent, main again), and stopping the main agent at the
first card, which made the first pair fast, dropped a request's second part ("…and give Ben 25%
extra time" lost 3 of 5). The final subagents run shared the API with another page-context run, so
its seconds are high, but no pairing brought it under the bar with the second part kept. The one
agent stays and the domain agents' code, setting and tests were removed. Cross cases are 6 of 66
here (30 of 330 turns); how often real users ask for two things at once is unknown (the local
conversations are test traffic, and prepared actions aren't stored), so the cross rows are a
check, not a weight. Page context and guides weren't run for the final pair: the actions decided
it. The single arm's "Invite … and top up credits for 50" failed 5 of 5 (the card, no top-up link)
until the prompt said to link a page beside a card for another part; it now passes 5 of 5. Spent
about $4 on these runs.

## Fuller tool descriptions, tried and reverted (2026-10-22)

Every tool got a 3–4 sentence description (what, when and when not, its parameters, its
limits) and the guide and `show` rules moved from the system prompt into the tools: tokens a
turn 21,600 → 39,200 and cost $0.0022 → $0.0040, task success 100% → 95.6% (90.7–98.0), six
cases failing (renames, invites, members). Then only the 15 tools whose route gives a bare title
("Get Company", "Me") got one, the prompt unchanged: tokens 25,000, success 97.1%, asked for the
parent 100% → 83.3%. Both reverted, as a cost beyond the noise with nothing better; with all 88
tools offered every turn, longer descriptions mostly add tokens. Fuller descriptions belong with
fewer tools a turn.
