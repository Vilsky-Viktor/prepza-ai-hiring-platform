---
paths:
  - "services/*/app/prompts/**"
  - "services/generation/**"
  - "services/assistant/**"
  - "services/rounds/app/integrations/llm.py"
  - "services/rounds/app/routers/help.py"
  - "packages/common/src/prepza_common/llm.py"
  - "packages/common/src/prepza_common/ai_*.py"
  - "packages/common/src/prepza_common/tracing.py"
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
- Model and effort per task in settings; models built with `prepza_common.llm.chat_model`, with
  a timeout and `max_retries` from constants; parallel calls capped; bulk work that can wait
  uses the Batch API.
- Output the code reads is a Pydantic schema (`with_structured_output`, a description per
  field); the code checks what the schema can't and retries or drops bad items.
- Never trust model output for ids, links, prices or permissions: the model picks from ids the
  code gave, links are built by code, tools check access themselves.
- Graph nodes: `services/nodes/`, one per module, returning only the state they change, safe to
  re-run (rule 11).
- Every call is traced (`prepza_common.tracing`) and priced (`prepza_common.ai_usage`).
- Any change to a prompt, model, effort, schema or output-shaping step runs its eval first
  (`.claude/rules/evals.md`).
