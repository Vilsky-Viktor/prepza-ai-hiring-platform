# In-app assistant

Anyone asks the assistant from the "ask agent" button in the header (or at the end of the home page). A signed-in user asks about their companies and about prepza, and gets a streamed answer built from the same pages' data they can already see; a signed-out visitor gets answers about prepza from the FAQ's knowledge. Asked to do something it has an action for (create a company, …), it prepares it at once and the user confirms it on a card; it never runs anything by itself. This page describes the panel and the service behind it (`services/assistant`). The same service offers its tools to the user's own AI apps (Claude, ChatGPT) over MCP: see [AI apps over MCP](mcp.md).

- [The panel](#the-panel)
- [What it answers](#what-it-answers)
- [The page the user is on](#the-page-the-user-is-on)
- [Actions](#actions)
- [A conversation](#a-conversation)
- [Voice](#voice)
- [Secrets pasted into the chat](#secrets-pasted-into-the-chat)
- [Limits](#limits)
- [Roles, tenancy and privacy](#roles-tenancy-and-privacy)
- [What's stored](#whats-stored)
- [Retention and deletion](#retention-and-deletion)
- [Tools](#tools)
- [Settings](#settings)

## The panel

- "ask agent" in the header (a pill with a bright arc circling its blue border; the icon alone below `md`) and at the end of the home page open it, with the input ready to type in (not on touch screens, where the keyboard would cover it). Its code loads the first time it's opened (or at once when it was open before a reload, to bring the chat back), so pages where nobody opens it never download it. From then on it's mounted once for the whole site, so a conversation stays while the user moves between pages, and closing never stops or loses it.
- Wider screens: a drawer at the end side, beside the page, which still scrolls; a click on the page closes it (not one in its own menus and dialogs). Its inner edge drags (or, focused, the arrow keys) to a width between 360px and 900px or 70% of the window, kept per browser. The wheel over it scrolls only its messages.
- Phones: the whole screen, the page behind it doesn't scroll, and following a link closes it.
- Its header: a company picker (signed in), New chat, History (past conversations, opened or deleted after a confirmation) and Close. The picker has the user's companies and "all companies": on a company's pages it starts on that company, elsewhere on all companies, and the user can change it; the pick is kept with the restored chat, and opening a past conversation picks its company. Each message goes with the pick: with a company, the model applies everything to it and never asks which; with all companies, it asks which company for anything that targets one (unless the user named it or has only one), and creating a company needs none.
- A reload brings back a recent chat only: one whose last message is at most `RESTORE_MINUTES` (30) old. Signed in, `GET /conversations/active` gives it (or a `204`); the browser keeps only whether the panel was open and the company pick (localStorage). Signed out, the tab's sessionStorage keeps the visitor's messages with their last one's time, and the window comes from `GET /config`. With a recent chat the panel reopens if it was open; otherwise it starts closed, on a new chat (the old one stays in the history). Signing out forgets both stores. A visitor who signs in keeps their chat on screen, and their first message saves it as the start of a new conversation (`earlier`).
- An empty conversation shows a welcome for where the user is: `GET /welcome?company_id=` decides the stage from what companies shows them (no company, a company not verified, verified without interviews, interviews without candidates, candidates), and the panel shows that stage's text and 3–4 questions to tap (`assistant.welcome` messages), first "What can I do on this page?" on any page with a guide. Signed-out visitors get the `signed_out` welcome without a call.
- Each answer is a card (with the tools at work and the dots while it's written, and its error), and what it shows (below) right under it; answers stream in limited markdown (emphasis, lists, code and links; no images or HTML); a link keeps its address only to a page the panel knows (the pages it names, `LINK_PAGES`), by its path alone, since text the model read (a candidate's answer, a job description) could steer it into others, such as an AI app's approval or a redirect; Stop replaces Send while one streams; a failed answer shows its error and Try again; `session_expired` refreshes the token and sends once more.
- Under each written answer, small thumbs up and down at its right edge (the help chat's answers too): one vote an answer, the same thumb again clears it, the other changes it; a vote that couldn't be saved goes back as it was, with an error. Signed in, `PUT /conversations/{id}/messages/{message_id}/vote` (`{"value": 1 | -1 | null}`) saves it with the answer, only on an answer in the user's own conversation (404 otherwise), and opening the conversation shows it again. Signed out, see [the help chat](site.md#faq-and-help-chat). With Langfuse set up, each vote is also sent as a score on the answer's trace (see [Votes in Langfuse](#votes-in-langfuse)).
- Blocks under an answer use the app's own rows: candidates as in an interview's list, interviews as in a company's list, balances as in the company header, and links to the pages the data came from.
- History titles: the start of the first question at first; after the first answer, and after every 5th question, one cheap call to the assistant's model (no reasoning, a few tokens; it counts toward the budgets) writes a one-line summary of up to 60 characters in the conversation's language, without emails or candidates' names. It comes as a `{"title"}` event after `{"done"}`; a failure keeps the old title.
- Asked to sign out, the assistant signs the user out at once: its `sign_out` tool only makes the turn send `{"sign_out": true}`, and the panel runs the site's sign-out and shows the visitor's welcome.
- **Signed out** it's the same panel with FAQ answers only: the questions go to rounds' help chat (its limits, nothing stored, see [Public site](site.md#faq-and-help-chat)), with no tools, actions, history, company or voice. Asking to sign in, or to do something that needs an account, brings a sign-in card; signing in from it keeps the panel open, now signed in.
- Both prompts keep to prepza and hiring with it (`prepza_common.scope.SCOPE_RULE`): anything else is declined in one friendly sentence, with no tools called.

## What it answers

- **Their data:** companies and roles, balances, the credit history and reserved credits (not invoices: their links are the payment provider's, so it points to the billing page), referrals, auto top-up, the team, the action log (the owner's), interviews and whether their questions are ready, their questions and the reports on them, reports, candidates (in one interview or across a company), one candidate's results, a pause, prices, ATS connections, linked jobs and their stages, an ATS job's description (to make an interview from it), Slack, API keys and web hooks, notifications, their account and email settings, templates (and those to copy), prepza's news, and their own practice.
- **How prepza works:** how-to, pricing, credits, payments, refunds, the terms and the privacy policy, from the platform guide (rounds' `GET /help/guide`, the same knowledge as the help chat signed-out visitors ask), in the user's language.
- **Hiring advice:** how to hire and screen, what to test, timing a test and extra time, AI in hiring and the law, connecting an ATS, AI agents, MCP and the API, from the site's guide articles: `list_guides` names them and `get_guide` reads one (rounds' `GET /help/guides` and `GET /help/guides/{slug}`), in the user's language (English until an article is translated). The answer is a few sentences from the article, with a link to it under the answer (`show`'s `guide` page, named by the article's title). Questions about how prepza does one of these (its ATS integrations, MCP, the API) read the guide too. AI apps over MCP and API keys with the `mcp` permission get both tools. Measured in `evals/` (`scripts/guides.py`).
- **The page they're on:** what it's for and what they can do there, from its guide (`get_page_guide`), and "here" means its interview, candidate or template (see [below](#the-page-the-user-is-on)).
- Tools are for the model to read; the user sees its answer, in text. A simple fact (an average, a count, a yes or no) is text only. Under an answer, the model may put one list of rows and one link with its `show` tool (`app/constants/show.py`):
  - rows (candidates, interviews or balances) only when the user asked to list or show them, or when a row is the answer (the best candidate's; for a tie, all who share it), with only the rows that answer. Each row opens its own page. The text is one short line that adds what the rows don't show, with grades as percentages. The assistant reads them with the user's token, so only what they may see shows, and keeps their ids.
  - one link to the most specific page (the interview's candidates for a position, the candidate's report for a candidate), named by what it opens ("open Senior Backend"). The URL comes from a fixed map of the app's pages filled with ids; the model never writes one, and never a generic "companies" link. When the model gives none and the turn read one interview (or one candidate), the assistant adds that link itself; a single row shows alone, as it opens its page already.
  - Both go under the answer once it's written. The links (here and on action cards) are links, styled as small buttons.
- Reports are downloaded and shared from their pages: the assistant links to the candidate's or the interview's page.

## The page the user is on

Every message carries the page it's asked on (`page`): its guide's key (`prepza_common.page_keys`, which every page registers in the frontend, see [page guides](companies.md#page-guides)), its path with the query (the tab, `?tab=candidates`), and the ids its route names (`company_id`, `interview_id`, `candidate_id` (the invite), `template_id`, `practice_round_id`), read from the route's parameters (`lib/page-context.ts`). The admin zone's pages register no key, so the panel sends no page there.

- It's only context, checked like any input (`schemas/chat.py`): an unknown key is dropped, the path is cut to 200 characters, an id must look like one. The ids are never trusted: the tools read with the user's token, so one that isn't theirs is a 404 there.
- The prompt's context line names the page, its quoted path and each id ("the interview with id …"), and says the ids stand only for what the user points at ("here", "this", "these"): a question naming an interview or a candidate is about that one (found by its name, even on another one's page), and any other covers all the user's data. A question about using the page calls `get_page_guide` (rounds' `GET /help/pages/{key}`, in the user's language); one about its data calls the usual tools with its ids, without asking which.
- Each message is stored with its page (`messages.page`), and the model reads an earlier question with the page it was asked on ("[Asked on …]"), so "here" means where the user was when they asked, also after moving between pages.
- `get_page_guide` is the panel's only: AI apps over MCP have no page, so they're never offered it.
- Signed out, the help chat gets the page's key and answers about the page from its guide (English, replying in the page's language).
- Measured in `evals/` (`page_context.py`): with the page context, general questions are answered at least as well as without it, and page questions much better (see the evals README).

## Actions

An action is a tool that changes something (`app/constants/actions.py`): a user-facing `POST`, `PUT`, `PATCH` or `DELETE` route with `confirm: True` (the loader refuses a write without it), whose body fields come from the route's snapshot.

1. The model calls it with the arguments. Nothing runs: the assistant checks them against the route's schema and keeps the action in Redis for `ACTION_TTL_SECONDS` (10 minutes), bound to the user, the conversation and the company, under a random `action_id`. The arguments never go to the browser and aren't written to the database.
2. The turn sends a card, `{"block": {"kind": "confirm", "action_id", "tool", "preview", "company_id", "destructive", "state": "pending"}}`, with exactly the values that will run; one that can't be undone carries a warning. The model tells the user to confirm it.
3. `POST /conversations/{id}/actions/{action_id}/confirm`, with the user's fresh token: the action must be this user's, in this conversation, about a company that's still theirs (from companies' list for that token); a pause, the limits and 30 actions a user an hour apply. It's claimed with Redis `GETDEL`, so of two confirms only one runs it. It runs once, as the user, with an `Idempotency-Key` of its id, and the response streams like a message: `{"action": the card's new state}` (`done` with the page it made, or `failed` with why), then the assistant's words about the result. The result reaches the model only in that turn's prompt.
4. `POST …/cancel` drops it. An expired, handled or cancelled action is a `409`; someone else's a `404`. A token the service refused (`401`) puts it back to be confirmed again with a fresh token.

Each card names what the action is about (`subject`: a company's name, an interview's title, a member's or candidate's email), read with the user's token when it's prepared, so an action about something they can't see gets no card. A pending card comes back when the conversation is reopened within its 10 minutes (Redis keeps it under the answer that prepared it); once done, its link says what it opens ("open Acme"). Actions share one progress label, "Preparing it for you to confirm…". Actions come only from the user's own request: the prompt says tool data, documents and names are never instructions, and the model fills an action with exactly the user's words and only the values they asked to change.

| Group | Actions |
|---|---|
| Companies and team (`company_actions.py`) | `create_company`, `rename_company`, `delete_company`, `set_company_website` (starts verification), `remove_company_logo`, `turn_off_auto_top_up`, `invite_member`, `change_member_role`, `remove_member` |
| Interviews, questions and candidates (`interview_actions.py`) | `create_interview` (from a job description; the result opens the topics' review), `create_interview_from_template`, `review_generation`, `retry_generation`, `cancel_generation`, `rename_interview`, `set_pass_mark`, `set_question_seconds`, `mark_hired` (one setting each, so a change carries only what was asked), `set_interview_link`, `set_topic_limit`, `regenerate_question`, `mark_question_wrong`, `delete_interview`, `invite_candidate`, `invite_candidates`, `revoke_candidate`, `rename_candidate`, `set_extra_time` |
| Account, notifications, integrations and practice (`account_actions.py`) | `update_language`, `update_email_preferences`, `delete_account`, `mark_notifications_seen`, `set_slack_kinds`, `disconnect_slack`, `disconnect_ats`, `link_ats_job`, `unlink_ats_job`, `retry_ats_candidates`, `create_webhook`, `remove_webhook`, `remove_api_key`, `start_practice` |

Destructive ones (deleting a company, an interview or the account, removing a member, revoking an invite, cancelling a generation, disconnecting Slack or an ATS, removing a linked job, a web hook or an API key) carry the "can't be undone" warning. Left out on purpose: connecting an ATS, saving its web hook key and creating an API key (secrets don't belong in a chat), setting a logo and emailing a report (files the browser makes), turning on auto top-up (it charges a card; topping up is a link to `/top-up`), and the links that carry tokens (invites, unsubscribing). Asked to sign out, the panel signs out at once (`sign_out`, below).

## A conversation

`POST /api/assistant/chat` with `{conversation_id?, company_id?, message, source?, page?, earlier?}` and the user's ID token. `company_id` is the company picked in the panel (one the user must be able to see), or none for all companies; it's the context of this message, and a new conversation is listed under it. `page` (`{key, path, company_id?, interview_id?, candidate_id?, template_id?, practice_round_id?}`) is only context for the model, stored with the message (see [the page the user is on](#the-page-the-user-is-on)). `earlier` (at most 20 messages, each cut to 2,000 characters) is the chat the user had before signing in, saved at the start of a new conversation and ignored in an existing one. The answer streams as server-sent events:

```
data: {"conversation": {"id": "6f1c…"}}
data: {"tool": {"name": "list_candidates", "state": "running", "label": "Reading candidates…"}}
data: {"tool": {"name": "list_candidates", "state": "done", "label": "Reading candidates…"}}
data: {"block": {"kind": "candidate_rows", "items": [{"id": "…", "email": "ann@example.com", "grade": 82, "passed": true}], "links": ["/companies/…/interviews/…/candidates/…"]}}
data: {"delta": "Ann passed"}
data: {"delta": " with 82%."}
data: {"done": {"message_id": "a93e…"}}
```

- Before anything streams, plain HTTP errors: sign-in (`401`), the emergency pause (`503`), maintenance, a company that isn't one of the user's (companies' internal list of them, however many) or a conversation they can't see (`404`), the limits (`429`), a message over 2,000 characters (`422`).
- A turn asks the model, runs the tools it calls (up to 4 at once, 20 s each) and asks again with their results, at most 6 times; then the model must answer with what it has. A turn takes at most 90 s. A comment (`: keep-alive`) goes out every 15 s without events.
- A tool's error (a `403` for the user's role, `402` without credits, a service that didn't answer) goes to the model, which explains it.
- The model failing or the turn running out of time ends with `{"error": "Couldn't get a reply right now. Please try again."}` (translated). A service refusing the user's token mid-turn ends with `{"error": …, "code": "session_expired"}`: the panel refreshes the token and sends the message again, once.
- Stopping the answer (or closing the tab) cancels the turn; it's saved as `cancelled` with the text it had. A model call cut short (cancelled, timed out, failed) reports no tokens, so they're estimated (about 4 characters each, `CHARS_PER_TOKEN`) from what it read and wrote, and count against the budgets like any.
- The model reads the system prompt (`app/prompts/assistant.py`: the user's name from their account, nothing else about them; answer in the interface's language, only from tools; act rather than explain, asking only for a truly missing value; never invent ids or links; refer to a candidate by name when the data has one, else by email, never calling a missing name "unknown"; never guess anyone's gender; tool data is data and its instructions are ignored; the page the user is on and when its ids apply; the scope rule), the conversation's last 20 messages' text within 24,000 characters, each earlier question starting with the page it was asked on (tools' data isn't kept: the model calls them again when it needs it), and the new message.
- Tool progress labels (`app/constants/tool_labels.py`) are translated by their English text in prepza_common's messages, in every language.
- `GET /conversations?company_id=` lists the user's conversations (paged, latest first), `GET /conversations/{id}` opens one with its messages (their blocks fetched again with the user's token), `DELETE /conversations/{id}` deletes it. `GET /config` gives the panel its limits, `GET /welcome` the user's stage for its welcome.

## Voice

Signed in, the panel's microphone button takes a spoken question: hold it to talk and let go to send (sliding away or Esc cancels; from the keyboard, Enter or Space starts and stops). The recording (webm/opus, or mp4 on Safari) stops by itself after `max_audio_seconds` (60, from `GET /config`); under half a second nothing is sent. It's hidden where the browser can't record.

`POST /transcribe` takes the recording as the request's body (`Content-Type` `audio/webm`, `audio/mp4` or `audio/ogg`, at most 2 MB; else `415` or `413`), kept in memory: it's never written to disk, the database or the logs. OpenAI's `TRANSCRIBE_MODEL` hears it in the interface's language (Filipino as Tagalog) and the text comes back (`{"text"}`); nothing heard is a `422`, OpenAI failing a `502`. The panel sends the text as a message with `source: "voice"`. Sign-in, the emergency pause and the limits apply: 60 transcriptions a user an hour, and their tokens count against the user's and everyone's budgets.

## Secrets pasted into the chat

A message holding a secret (a key, a token, a password) is caught before anything else happens to it, by one detector in `prepza_common/secrets_check.py` shared with the help chat and voice:

- Known formats: prepza's `pz_` API keys and `whsec_` web hook secrets, Slack tokens and web hook URLs, OpenAI, Anthropic, GitHub, Stripe, Paddle, AWS and Google keys, JWTs and private keys.
- A word saying it's a secret (secret, key, token, password, credential and the like in the 23 languages, `secret_words.py`) anywhere in the message: then any standalone value of 16+ characters mixing letters and digits counts, unless it's a URL, an email, a UUID, a path or glued words (`postgresql16django5`).
- Without such a word, a value of 20+ characters whose letters and digits switch often (`94uf9jf394ur0fj394g3ffh3`), or that mixes upper case, lower case and digits and looks random. Order ids, product codes and UUIDs aren't caught.

On a match, the message (or the chat carried from before signing in) isn't stored, counted, shown to the model, given a title or logged. The answer streams `{"removed": true}` (the panel replaces the question with a muted "Message removed: it contained a secret", on screen and in what it keeps for a reload) and a fixed, translated reply: secrets never go through the chat, enter it yourself in its form. When the message names where it belongs (an ATS or "integration", Slack, the API or a web hook) and the panel is about a company, the reply names that page and links to it ("open integrations"); otherwise it says to use the right form on the site. A voice message with a secret is a `422`, and its text never comes back.

## Limits

Counted in Redis. Each is one of `prepza_common.limit_list`'s, at the default below until a superadmin changes it in the admin zone's Controls tab (see [Admin zone](admin-zone.md#limits)):

| Limit | Default |
|---|---|
| Messages per user | 30 an hour, 200 a day |
| Messages per company (its members together) | 1,000 a day |
| Messages for everyone | 20,000 a day |
| Tokens per user, per company, for everyone | 2 million, 6 million, 200 million a day |

The limits for everyone hold only people in a company that never topped up, so free accounts can't use them up for paying ones; whether a company paid is asked of billing at most every 10 minutes (`PAID_CACHE_SECONDS`), and counts as not when billing can't say.
| Actions a user confirms | 30 an hour |
| Voice messages a user has transcribed | 60 an hour |

- A message counts as it's sent, and a confirmed action as a message; a turn's tokens (every model call, input and output, titles and transcriptions included) are added when it ends, so going over refuses the next message, never the running one.
- The emergency pause and maintenance mode refuse new messages too.
- For people in a company that never topped up, or in none, messages and voice messages are also refused (503) once the day's AI spend cap for them is reached (`AI_SPEND_UNPAID_DAY`, see [Generation](../generation.md#rate-limits)).
- Every model call (answers, titles, transcriptions) is recorded with its cost for the admin zone's AI costs page (see [Credits and payments](billing.md#ai-usage-and-limit-hits)).

## Roles, tenancy and privacy

- Signed-in users only. Every tool and action calls the services' user-facing routes with the user's own token, never a service-to-service bypass, so roles, credits, the pause and every other rule apply unchanged there: a viewer reads what a viewer sees. The token is never stored, logged or shown to the model.
- A company that isn't among the user's is refused before anything is called with it: the picked company, any `company_id` a tool is given (in the panel and through an AI app alike), and a pending action's company on confirm. The list is companies' internal one (`/internal/users/{id}/companies`, every company, no page limit), kept 10 seconds (`constants/tenancy.py`) so a confirm reads it once, and read again after an action that made a company.
- Never `/internal/` or `/superadmin/` routes, and a write only with `confirm: True` (the tool loader refuses them).
- Reads of a candidate's results go to companies with a signed `X-Assistant` header: the action log records them as the assistant's (`via: "assistant"`, or `"mcp"` through an AI app), and they're kept out of the "results viewed" funnel.
- Questions and the data the tools read are sent to OpenAI (no training). Each tool's data is trimmed to the fields it needs. A link's code reaches the model only as the full link the app's page copies (`TOKEN_LINKS`): a candidate's invite link (owners and admins, until they finish) and an interview's shareable link. Team members' join links are never read: they give access to the company, and AI apps use the same tools. Every model call is made with `store=false` (`prepza_common.llm.chat_model`), so OpenAI keeps nothing beyond its 30-day abuse monitoring; the assistant's tool loops send the model's encrypted reasoning back with each call instead (`MODEL_INCLUDE`).
- Logs and error reports never hold what was said, tool arguments or results: failures are logged by their type only, and Sentry gets no variables' values, in any service (`prepza_common.sentry.init_sentry`).

## What's stored

- Kept (Postgres `assistant`): the user's messages (with the page each was asked on: its key, path and ids) and the assistant's answers (text, the user's vote on it, and its Langfuse trace id when Langfuse was set up), each answer's blocks as references only (their kind, the ids of what they showed and their links, which are app paths of ids), and which tools an answer called with how long they took and how they ended (argument names, no values; no results). Opening a conversation fetches its blocks again with the user's token: what they may see now, without anything deleted or erased since.
- Not kept: tools' results (other people's data, such as candidates' results), pending actions' arguments (Redis, 10 minutes) and voice recordings (in memory only).

### Votes in Langfuse

With `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` set (local only for now: not in Terraform until the legal version that lists Langfuse is in force), the assistant's and the help chat's answers are traced to Langfuse (`LANGFUSE_HOST`, its EU cloud by default) through its LangChain callback (`prepza_common.tracing`): each answer gets one trace, which all its model calls report to, and its id is kept with the answer. A vote is then sent in the background as a Langfuse score on that trace (`prepza_common.answer_votes`): name `user_vote`, value 1 for a thumbs up and 0 for a thumbs down, one score a trace (a stable id, so a changed vote replaces it), deleted when the vote is cleared. Each send reads the vote as it is then, one at a time an answer, and is tried 4 times with growing waits before it's logged and dropped; the vote itself stays saved. Without the keys nothing is traced, no trace id is kept and nothing is sent. A conversation's title is its own trace, tagged with the conversation's id. Generation traces to Langfuse with the same keys (see [Generation settings](../generation.md#generation-settings)).

## Retention and deletion

- Conversations nobody added to for `ASSISTANT_RETENTION_DAYS` (90) are deleted daily (`/internal/schedules/retention`, in batches of 500), with their messages and tool calls.
- Deleting a company (`company.deleted`) deletes its conversations; a redelivered event deletes nothing more.
- Opening a conversation about a company the user can no longer see (removed from its team, or the company is gone) deletes it, and it's not found.
- Deleting an account deletes the user's conversations, their pending actions in Redis and their connected AI apps; "Download my data" includes their conversations, messages, the blocks' references and their connected AI apps (library calls `/internal/users/{id}`).
- Expired AI app connections and apps with none go daily too (see [AI apps over MCP](mcp.md#connections-and-tokens)).

## Tools

Each read is a user-facing GET route of companies, billing, library, notifications, ats, api or rounds, listed in `app/constants/tools.py`, `company_tools.py` and `detail_tools.py`. Its function, as the model sees it, is built at startup from committed OpenAPI snapshots of those services (`app/openapi/`).

To add one:

1. Add an entry: its service, `GET`, the path as that service sees it, the parameters the model may set, the fields it reads (`fields`), `max_items`, and how the panel shows it (`render`, `link`).
2. Add its progress label to `app/constants/tool_labels.py`, and its translations to prepza_common's messages.
3. Refresh the snapshots if the route is new: `./scripts/assistant-openapi.sh` with the stack running (CI fails when they differ).
4. The unit tests check that each entry resolves in its snapshot, is a read or a confirmed write, and has a label.

An action is the same in `app/constants/company_actions.py`, `interview_actions.py` or `account_actions.py` (gathered in `actions.py`), with its method, `confirm: True`, the body fields the model may set (`body`), what its card shows (`preview`), whether it can't be undone (`destructive`), and the page its result opens (`render: "link"`, `link` filled from the arguments and the result). The panel names it by its tool in the `assistant.actions` messages.

## Settings

| Setting | Default | What it sets |
|---|---|---|
| `ASSISTANT_MODEL`, `ASSISTANT_REASONING_EFFORT` | `gpt-6-luna`, `low` | The chat model |
| `TRANSCRIBE_MODEL` | `gpt-4o-mini-transcribe` | Voice input |
| `ASSISTANT_RETENTION_DAYS` | 90 | Days a conversation is kept after its last message |
| `OPENAI_API_KEY` | | OpenAI's key |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `LANGFUSE_ENVIRONMENT` | Off; `https://cloud.langfuse.com` (EU); `production` | Trace answers, marked with their environment (`development` locally), and titles and send votes to Langfuse (also rounds' help chat), see [Votes in Langfuse](#votes-in-langfuse); local only for now |
| `SITE_URL` | required (`http://localhost:8090` locally) | Where AI apps connect (`<SITE_URL>/mcp`), see [AI apps over MCP](mcp.md#settings) |
| `FIREBASE_WEB_API_KEY` | required (`demo-api-key` locally) | Firebase's public web key, for AI apps' calls as the user |
