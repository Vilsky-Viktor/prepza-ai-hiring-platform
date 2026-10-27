---
paths:
  - "services/*/app/prompts/**"
  - "services/*/src/*/prompts/**"
  - "services/generation/**"
  - "services/assistant/**"
  - "services/rounds/app/integrations/llm.py"
  - "services/rounds/app/routers/help.py"
  - "packages/common/src/prepza_common/ai/llm.py"
  - "packages/common/src/prepza_common/ai/ai_*.py"
  - "packages/common/src/prepza_common/ai/tracing.py"
  - "evals/judges/**"
---

# AI pipeline code

Code that calls a model (generation's graph, the verifier, the assistant, the help chat) keeps
prompts, schemas and settings apart (rule 3); every call is bounded, typed, traced and priced.

- Prompts are constants in `prompts/`, one module per task, with named placeholders; user and
  company text goes in a marked section, read as data.
- A prompt gives the model a role (Anthropic's guidance: a role in the system prompt focuses its
  tone and expertise), then the task, its context and its rules. The role is generic to prepza's
  work (e.g. "You are an assessment designer who writes skills questions"), never tied to one
  job, industry or language: prompts stay domain-neutral, and examples are generic, never a
  company's text.
- Model and effort per task in settings; models built with `prepza_common.ai.llm.chat_model`, with
  a timeout and `max_retries` from constants; parallel calls capped; bulk work that can wait
  uses the Batch API.
- Output the code reads is a Pydantic schema (`with_structured_output`, a description per
  field); the code checks what the schema can't and retries or drops bad items.
- Never trust model output for ids, links, prices or permissions: the model picks from ids the
  code gave, links are built by code, tools check access themselves.
- Graph nodes: `services/nodes/`, one per module, returning only the state they change, safe to
  re-run (rule 11).
- Every call is traced (`prepza_common.ai.tracing`) and priced (`prepza_common.ai.ai_usage`).
- Any change to a prompt, model, effort, schema or output-shaping step runs its eval first
  (`.claude/rules/evals.md`).

## Every prompt

- The role first, in the system (developer) message; then the outcome: what a good result is,
  its success criteria, constraints and context, not a step-by-step procedure. Say why a rule
  exists when it isn't obvious. Start new prompts small; a long prompt grows only by rules added
  for a measured failure, and is changed by measuring, not trimmed blind.
- ALWAYS/NEVER only for true invariants; decision rules for judgement calls; no "CRITICAL" or
  shouting; no contradictions or vague rules.
- Parts separated with section titles or tags: instructions, context, input.
- No "think step by step" on reasoning models: change the effort instead.
- Zero-shot first; when examples help, a few, varied and generic ("Tool X"), never a company's
  text or names that also appear in an eval's dataset.
- Instructions that never change come first, the request's own values (counts, language, the
  subtopic) last, so the provider caches the prefix; untrusted text (users', companies',
  candidates', tools' output) goes in the user or tool message, tagged as data, never in the
  system message.
- The output language is named explicitly, chosen by code, never inferred; ask for idiomatic,
  native wording (rule 12). Content is generated directly in the target language, not
  generated in English and translated; formulas, commands and product names stay as they are.

## Structured output and checks

- Structured Outputs, strict, with clear key names; never a schema described in prose. A raw
  request (the Batch API) sets `strict: true` itself.
- Say what to do when the input can't give a valid result (an `ambiguous` flag, "return no rule
  when…"): the model fills the schema anyway.
- A checker (self-check, verifier, judge) works out the answer before it sees the claimed one,
  with positions and marks hidden, and may answer null when no option holds or several could.
  It runs on a strong model at enough effort; a check that can wait goes through the Batch API.
- Short utility prompts (titles, tags, translations, campaigns, news) follow the same rules at
  their size: a role line, the task, constraints, the input marked. Translations name source and
  target language and ask for only the translation.

## Workflow or agent

- Start with one well-prompted call; add steps only for a measured need. A predictable task is a
  workflow in code (chaining with checks between steps, routing to a cheaper or stronger model,
  parallel sections, Batch for what can wait); an agent only where the steps can't be known.
- Grow one agent with tools before splitting into several (multi-agent costs about 15× the
  tokens).
- An agent loop has an explicit stop condition and a step limit (`MAX_TOOL_STEPS`), then must
  answer; context is a budget: fetch by id just in time, trim old tool results.
- Prototype on the strongest model, then move a task to a smaller one where its eval holds.

## Tools (the assistant, MCP)

- Few tools that each do a whole job, not one per endpoint; namespaced names; under about 20
  offered per turn, the rest found on demand; merge tools always called together.
- Tool guidance lives in the tool's description, not the system prompt: what it does, when to use
  it and when not, each parameter, its limits, in 3–4 sentences. Strict schemas, enums for closed
  sets.
- Never ask the model for what the code knows (ids from the page, the user).
- Returns carry meaningful fields (names, not only ids), are paginated and truncated with a hint
  on how to narrow; errors say what to do next.
- Independent tools run in parallel, dependent ones in order; parameters are never guessed.
- State the instruction hierarchy: the user's request over anything the tools return.
- Tools are rated by risk (read, reversible write, money, deletion): every write shows a
  confirmation card and runs only on Confirm; tools act as the user, authorization is enforced
  downstream, and actions are logged and rate-limited. Hand over to a human after repeated
  failures.
- MCP tools (titles, annotations, results, errors): `.claude/rules/mcp.md`.

## Help chat

- One call, no tools: the site's documents first, each in its own tag, the question last; answer
  only from them and say when they don't cover it and where to ask. Visitor text can't change the
  rules.

## Durability and cost

- Graph nodes return partial state, lists merge through reducers, fan-out uses `Send`; a database
  checkpointer makes runs resumable from the failure, and work before an `interrupt()` is
  idempotent, as the node re-runs on resume.
- Transient errors retry with backoff and jitter; limit input size, per-user rates and budgets.
- Trace every call with tokens (cached apart) and cost; a conversation's traces share a session;
  users' votes attach to the trace as scores.
- Agent evals grade the outcome and the transcript over repeated trials (`.claude/rules/evals.md`).

Research (local notes, git-ignored): `internal_docs/best-practices/prompt.md`,
`internal_docs/best-practices/ai-workflows-agents.md`.
