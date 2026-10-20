---
name: finish-ui
description: Finish a UI change after the user has approved it in English - write and run its tests, translate it into all 23 languages, update docs, READMEs, help texts, the FAQ, the assistant's knowledge and articles, then commit it as one change. Use only once the user has approved the UI.
---

# Finish an approved UI change

Before approval, the `ui-build` skill applies: English only, no tests, no translations
(CLAUDE.md rule 14). Start this only after the user's own message approves the UI, and do every
part below; ask before skipping any.

## 1. Check the change against the rules

Re-read the diff against the rule files that loaded for it: `.claude/rules/nextjs.md`
(direction, formatting), `accessibility.md` (roles, focus, contrast, live regions),
`performance.md`, `seo.md` for public pages, `privacy.md` for new data. Fix what doesn't hold
before writing tests.

## 2. Tests (rule 8, the `verify` skill)

- Unit tests for logic on both sides: `services/<svc>/tests/unit`, `frontend/tests`.
- Integration tests for anything touching the database, Redis or another service.
- A browser test for every new or changed screen or flow: `e2e_tests/signed-in/specs/` or
  `e2e_tests/pages/` (`.claude/rules/testing.md`), finding elements by role, position or
  `data-testid`, never by fixed wording; a screenshot step for a new screen.
- Run the affected suites and fix what fails.

## 3. Translations (the `translate` skill)

Every new or changed text in all 23 languages, frontend messages and backend messages alike;
removed texts removed everywhere; `node scripts/check-messages.mjs` prints `problems: 0`.

## 4. Everything else the change touches (rule 9)

Search for each, and update what describes the changed behaviour, in every language it exists in:

- READMEs: root `README.md`, `infra/README.md`, the changed code's README;
- `docs/` (`docs/features/<area>.md`);
- help texts and page guides (`services/rounds/app/page_guides/`), the help chat's guide
  (`services/rounds/app/prompts/help.py`);
- the FAQ and articles in `frontend/content/` (`.claude/rules/content-i18n.md`);
- the assistant's knowledge: its prompts, tool descriptions and snapshots (the `api-types`
  skill when routes or schemas changed);
- compliance notes, the privacy policy and the records of processing when data changed.

A prompt or tool description changed on the way? Run its eval first (the `run-eval` skill).

## 5. Commit

One commit for the change (rule 13), explicit paths only: check `git diff --cached` first, as
other agents stage files in parallel. Never push.

## Report

What the user now sees, the suites run with their counts, the languages done, the docs updated,
and anything not done or not verified.
