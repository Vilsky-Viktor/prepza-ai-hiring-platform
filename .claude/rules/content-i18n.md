---
paths:
  - "frontend/messages/**"
  - "frontend/content/**"
  - "frontend/i18n/**"
  - "packages/common/src/prepza_common/messages/**"
---

# Content and messages

Markdown in `frontend/content` (`guides/`, `compare/`, `pages/`; a translation at
`<locale>/<folder>/<slug>.md`; `documents/` English only; `mcp/` runnable examples) and messages
in `frontend/messages` (rules 9, 12, 14).

- One file per article per language; the slug is the English file name, lowercase and
  hyphenated, the same in every language, never changed once published.
- Front matter: `title`, `seoTitle` (≤ 60 characters), `description` (≤ 155), `updated`
  (YYYY-MM-DD); the body starts with `# <title>`.
- Translations keep the original's sections, facts, numbers and links and change in the same
  change; facts about prepza match what the backend returns.
- Message keys nested by feature, camelCase, naming the purpose (`billing.topUpTitle`); every
  key in all 23 files; `pnpm check:messages` passes.
- A counted noun is an ICU plural, never `{count} candidates`; whole sentences, never joined
  pieces; formatting through `t.rich` tags. Text no longer shown is removed in every language.
