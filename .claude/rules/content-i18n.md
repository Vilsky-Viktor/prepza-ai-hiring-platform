---
paths:
  - "frontend/messages/**"
  - "frontend/content/**"
  - "frontend/i18n/**"
  - "packages/common/src/prepza_common/messages/**"
  - "packages/common/src/prepza_common/i18n.py"
  - "services/billing/app/services/catalog.py"
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

## Messages

- A number in a message is `{count, number}` or `#` inside a plural, never a bare `{count}`.
  Every counted noun is a plural in English too, so each language can choose; `=N` for exact
  values; `other` is required.
- Each locale fills its CLDR plural categories: other only (ja, ko, zh, th, vi, id); one, other
  (en, de, nl, et, tr, hi, fa; hi and fa `one` is 0 and 1); fil one/other by its own rule; one,
  many, other (fr, es, it, pt; `many` only for compact millions); one, two, other (he); one, few,
  many, other (ru, uk, pl); zero, one, two, few, many, other (ar). ru, uk, pl and ar without
  `few`/`many` are wrong for most numbers.
- `select` for variants chosen by data (kind, state, a missing name); avoid ordinals.
- Punctuation and spacing between sentences live in the message (ja/zh "。" and "：", hi "।",
  French space before ":"), never added in code.
- Don't reuse one key in two places because the English matches: grammar differs by context.
  Keys name their purpose; a short note for translators only where a key is ambiguous (the
  `translate` skill).
- Messages are typed through next-intl's `AppConfig` (`Messages: typeof en`); a missing key
  falls back to English and is reported.
- Backend text with numbers or dates (emails, Paddle item names) formats them with `babel` in the
  recipient's language; no English item names or ISO dates in other languages' text.
- Content belongs to its language, not the viewer's: it's stored with its `language`, shown with
  that `lang`/`dir`, and a company's data is never machine-translated for display.

Research (local notes, git-ignored): `internal_docs/i18n-best-practices.md`.
