---
name: translate
description: Add or change a user-facing text in all 23 languages, frontend messages and backend service messages alike. Use whenever a change adds, rewords or removes text a user reads.
---

# Translate a text into every language

For a change a user sees, translate only after the user has approved the UI in English (CLAUDE.md
rule 14).

prepza speaks 23 languages (`frontend/constants/i18n.ts` `LOCALES`). A text changed in English
must change in all of them in the same commit.

## Where texts live

- **Frontend:** `frontend/messages/<locale>.json`, nested by namespace (`invite.extraTime`).
  `en.json` is the source.
- **Backend:** `packages/common/src/prepza_common/messages/<locale>.py`, a `MESSAGES` dict from
  the exact English text to its translation. Every message a service raises must be there:
  each service's `tests/unit/test_translations.py` fails otherwise.

Before writing a new text, search both places for the same sentence: when the backend already
has it translated, reuse those translations for the frontend key rather than translating again.

## How to translate (rule 12 in CLAUDE.md)

- Translate the meaning, not the words, in hiring and HR terms.
- Reuse the words each file already uses for the same thing ("invite", "interview", "company",
  "candidate"): read neighbouring keys of the same file first.
- Keep each file's form of address (informal or formal) as its other texts do.
- Keep ICU plurals valid: the same `{count, plural, ...}` selector, every CLDR category the
  language needs (ru, uk, pl `one/few/many/other`; ar all six; he `two`; the list is in
  `.claude/rules/content-i18n.md`), and `#` for the number; a count outside a plural is
  `{count, number}`.
- Punctuation and spacing stay inside each language's text (ja/zh "。", hi "।"); never rely on
  code to join sentences.
- Percent signs and numbers go where the language puts them ("%85" in Turkish, "85 %" in French).
- Watch for words with a second meaning (Persian «شرکت» is both "company" and "take part").

For more than a couple of languages, hand the 22 translations to a subagent with this context
and the exact English, then review its answer before using it.

## Check

```bash
cd frontend && node scripts/check-messages.mjs   # must print "problems: 0"
npx prettier --write messages/*.json
cd services/<svc> && uv run pytest -q tests/unit/test_translations.py
uvx ruff@0.16.10 check packages/common && uvx ruff@0.16.10 format packages/common
```

A removed text goes from all 23 files too; check nothing else reads it first
(`grep -rn` the key or the English sentence across `frontend`, `services` and `e2e_tests`).
