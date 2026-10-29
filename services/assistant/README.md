# assistant

Mira, prepza's in-app AI assistant: signed-in users' conversations, streamed over server-sent
events (`POST /chat`), voice messages turned into text (`POST /transcribe`), and tools made from
the other services' user-facing routes, called with the user's own token, so every role and rule
applies; actions that change something wait for the user's confirmation. It serves the same tools
to the user's own AI apps over MCP (`/mcp`), with its OAuth authorization server, and deletes
Langfuse's traces on time. It also runs the help chat for signed-out visitors
(`POST /help/chat`, votes at `PUT /help/answers/{id}/vote`; `HELP_MODEL`,
`TURNSTILE_SECRET_KEY` and the `HELP_*` limits), answering from the knowledge site sends it
(`GET /internal/help/knowledge`). It keeps conversations, AI apps' connections and the help
chat's votes (`help_votes`) in its own database, and its rate and spending limits in Redis.
What it does and its settings: [the assistant](../../docs/features/assistant.md),
[the help chat](../../docs/features/site.md#faq-and-help-chat),
[AI apps over MCP](../../docs/features/mcp.md);
the AI rules: `.claude/rules/ai.md`, `mcp.md`.

## Layout

```
src/assistant/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1): chat,
│                           # transcribe, conversations, actions, MCP and its OAuth, consent,
│                           # the help chat and its votes
├── api/dependencies.py     # The signed-in user with their token; calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (a company, a candidate, an interview or an account
│                           # deleted);
│                           # dispatch.py picks one
├── services/               # A turn and its tools, actions, titles, limits, MCP, OAuth,
│                           # updates, transcription, the help chat and its votes
├── repositories/           # Conversations, messages, AI apps' connections, help votes (Postgres);
│                           # pending actions and consent requests (Redis)
├── models/, schemas/       # SQLAlchemy tables and plain data; request and response models
├── helpers/, constants/    # Pure functions; fixed values (the tools, actions, limits)
├── prompts/                # The system prompts (the assistant, MCP, titles, tool routing,
│                           # the help chat)
├── openapi/                # The other services' OpenAPI snapshots the tools are built from
│                           # (written by scripts/assistant-openapi.sh)
└── integrations/           # OpenAI, Firebase tokens, the other services (site's help
                            # knowledge too), Langfuse, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together (a new conversation with its first question; an account's conversations with its AI
apps' connections), and call OpenAI, Redis, Langfuse and the other services outside it. A plain
read may open `async with Session() as session:` in the route. `tests/unit/test_layers.py`
checks the imports and that no repository commits; retention and the deletions after a company's
or a candidate's events take the session factory, each batch its own transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `assistant`
(`assistant.api.v1.chat`).

## Commands

```bash
docker compose up -d --build assistant        # the service and its migrations
cd services/assistant && uv run pytest        # unit tests
scripts/integration.sh assistant              # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                  # refresh the other services' snapshots
evals/run.sh assistant <script.py>            # offline evals (they call OpenAI: they cost)
evals/run.sh assistant help_chat.py           # the help chat's offline eval
```
