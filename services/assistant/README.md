# assistant

Mira, prepza's in-app AI assistant: signed-in users' conversations, streamed over server-sent
events (`POST /chat`), voice messages turned into text (`POST /transcribe`), and tools made from
the other services' user-facing routes, called with the user's own token, so every role and rule
applies; actions that change something wait for the user's confirmation. It serves the same tools
to the user's own AI apps over MCP (`/mcp`), with its OAuth authorization server, and deletes
Langfuse's traces on time. It keeps conversations and AI apps' connections in its own database,
and its rate and spending limits in Redis. What it does and its settings:
[the assistant](../../docs/features/assistant.md), [AI apps over MCP](../../docs/features/mcp.md);
the AI rules: `.claude/rules/ai.md`, `mcp.md`.

## Layout

```
src/assistant/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1): chat,
│                           # transcribe, conversations, actions, MCP and its OAuth, consent
├── api/dependencies.py     # The signed-in user with their token; calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (a company, a candidate or an interview deleted);
│                           # dispatch.py picks one
├── services/               # A turn and its tools, actions, titles, limits, MCP, OAuth,
│                           # updates, transcription
├── repositories/           # Conversations and messages, AI apps' connections (Postgres);
│                           # pending actions and consent requests (Redis)
├── models/, schemas/       # SQLAlchemy tables and plain data; request and response models
├── helpers/, constants/    # Pure functions; fixed values (the tools, actions, limits)
├── prompts/                # The system prompts (the assistant, MCP, titles, tool routing)
├── openapi/                # The other services' OpenAPI snapshots the tools are built from
│                           # (written by scripts/assistant-openapi.sh)
└── integrations/           # OpenAI, Firebase tokens, the other services, Langfuse, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

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
```
