# Rules for this repo

1. **An empty line before each block and each return.** In generated code, put an
   empty line before every block statement (`if`, `for`, `while`, `try`, `with`,
   `switch`, nested functions and similar) and before every `return`. The exception
   is when that statement is the first line of its enclosing block; formatters
   remove a blank line there anyway.

2. **Small files, simple functions.** A hand-written file has at most 300 lines (all
   lines, as `wc -l` counts them). When a change would take it past 300, first split it at
   a seam: one responsibility per file (rule 3), in the simplest way (rule 4), never at an
   arbitrary line; the pieces stay in the folder their layout rule gives them.
   - Exempt: generated files (lockfiles, OpenAPI snapshots, `frontend/src/types/api/`), data
     (`frontend/messages/`, the services' translated messages in
     `prepza_common/i18n/messages/`, page guides, the email texts in `templates/languages/`,
     `evals/datasets/`, fixtures), binary files and articles in `frontend/content/`. Tests
     are not exempt; they split by area.
   - Functions: complexity at most 15 (Ruff `C901`, ESLint `complexity`), at most 12 branches
     and 50 statements in Python; how to split files and functions and size agents' files:
     `.claude/rules/code-size.md`.
   - CI fails on a hand-written file over 300 lines (`scripts/check_file_size.sh`).

3. **Separate logical modules.** Keep each kind of code in its own file for
   readability and maintainability: schemas, models, types, helper functions,
   prompts and constants each get their own module. Don't mix them with the logic
   that uses them.

   Group modules into folders by kind: a Python service's layout is in
   `.claude/rules/python-services.md`; within it, besides its folders, `prompts/`,
   `helpers/` (pure helpers), `integrations/` (external services) and `constants/` each
   keep their own folder.

4. **Keep code as simple as possible.** Strictly avoid overcomplicating and
   overengineering: no abstractions, layers, options or generalizations that the
   current need doesn't require. Choose the most direct solution that works.

5. **No business logic on the frontend.** Rules, thresholds, limits and decisions
   (what passes, what counts as done, what is allowed) live in the backend services,
   which return the results. The frontend only displays data, collects input and
   sends it to the API.

6. **Every page has the same width.** A page's `<main>` is
   `mx-auto max-w-page px-6` (`--container-page` in `globals.css`: 80rem, Tailwind's
   `max-w-7xl`), the width of the header and the footer, so content lines up with the
   logo and the menu on every page. No page is narrower or wider. Cards, forms and
   prompts inside a page may be narrower, but the page itself never is; running text
   (articles, legal documents, the about and accessibility pages) sits in a centred
   `mx-auto max-w-5xl` column.

7. **One design language across the app.** Build a new page or piece of UI from the
   patterns the app already has, never from scratch. Before writing it, find the
   closest existing page and copy its layout, sizes and components: a list page looks
   like the companies list (a `text-3xl` title with its main action button on the
   right, rows in one `divide-y rounded-2xl border` list), a page that starts a test
   looks like the home page's start (a large title and the shared `DescriptionBox`),
   and a detail page looks like a company's test page. Reuse the shared components
   (`DescriptionBox`, `BackLink`, `PageHeader`, `EditableTitle`, `TopicQuestions`)
   instead of new look-alikes. Keep it minimal: no new colors, shadows, gradients or
   effects unless asked.

8. **Every piece of functionality is covered by tests, on the backend and the
   frontend.** New or changed behaviour ships with its tests in the same change:
   unit tests for logic (`services/<svc>/tests/unit`, `frontend/tests`), integration
   tests for anything that touches the database, Redis or another service
   (`services/<svc>/tests/integration`, run with `scripts/integration.sh`), and a
   browser test for every user-facing flow or screen (`e2e_tests/pages` signed out,
   `e2e_tests/signed-in` signed in). A bug fix comes with a check that fails without it,
   added to an existing test of that behaviour where one fits; a new test only when none does.
   Run the affected suites before calling the work done. Every test of every kind (unit,
   integration, browser, load, evals, scripted end-to-end) starts absolutely clean: its own data
   and users, a fresh browser, no state left by another test, and passes alone and in any order
   (details in `.claude/rules/testing.md`).

   Tests check what the product does, never fixed wording. The line: does the text depend on
   what happened, or would it read the same whatever happened?
   - Tested: data (anything from input, the API or the database: names, emails, notes,
     amounts, counts, prices, grades, dates and the formats the code gives them); error and
     refusal messages, word for word, as their text is the reason the system gives; whether a
     state-dependent element appears (a notification, toast, badge or notice), its kind
     (error or success) and the data it carries, found by role, a `data-testid` or a state
     attribute, never by its fixed wording; and an accessible name where it is the feature
     itself (an icon-only button's label).
   - Not tested: fixed text that reads the same whatever happens: headings, labels,
     placeholders, descriptions, help texts, tooltips, empty-state sentences, and the wording
     of success toasts and notices. No locator depends on it either: find elements by role and
     position, or by a `data-testid` when nothing else tells them apart.

9. **READMEs stay current.** When a change affects anything a README describes
   (features, behaviour, setup, settings, commands, tests, deployment), update that
   README in the same change: the root `README.md`, `infra/README.md` and any README
   next to the changed code. Describe what is true now, not the change itself.

10. **No duplicated functionality or logic.** Before writing something, look for code
    that already does it and reuse it. Logic repeated across services goes into a
    shared library (`packages/common`, `prepza_common`); repeated frontend logic into
    one helper or component. A logically grouped domain that several services keep
    reimplementing gets its own service.

11. **Check every event-driven flow end to end.** When code publishes, consumes or
    schedules events (outbox, Pub/Sub, webhooks, scheduled jobs), trace the whole flow
    from producer to every consumer, and check it for the common issues: idempotency
    (a redelivered or duplicate event changes nothing twice), race conditions
    (concurrent handlers, out-of-order events, read-then-write without a lock or a
    unique constraint), rate limits (of external APIs and of our own services, with
    retries and backoff), and failures (what is retried, what is lost, what a handler
    does halfway through).

12. **Translate the meaning, not the words.** In every language, use the words and
    phrases that carry exactly the intended meaning in our domain (hiring, candidates,
    tests, practice). When a word is ambiguous, look up what that language normally
    uses for it in hiring and HR. A literal translation can narrow or change the
    meaning: English "learner" covers anyone learning, while its literal translation
    elsewhere may mean only a school pupil or a university student; Persian «نامزد»
    for "candidate" also means an election candidate or a fiancé («متقاضی» is right).

13. **Commit messages.**
    - **Imperative mood:** the subject is a command ("Add", "Fix", "Remove"), never past
      tense; it completes "If applied, this commit will...".
    - **Short subject:** at most 50 characters (72 at the very most), so Git tools and
      GitHub never cut it off.
    - **No period** at the end of the subject, and its **first letter capitalized**.
    - **A blank line** between the subject and the body.
    - **Body wrapped at 72 characters**, so `git log` reads well in a terminal.
    - **Why over how:** the body explains why the change was needed; the diff shows how.

14. **UI changes: approval first, then everything else.** For any change a user sees,
    build it in English only and show it (the user reviews it on the local site, plus
    screenshots from one short run), then wait for the user's approval. Until then, write no
    tests, run no test suites and translate nothing: running tests slows the local site down
    so much that the user can't move between pages to review it. Once the UI is approved,
    write and run its tests, translate it into every language, and update READMEs, docs,
    help texts, the FAQ, the assistant's knowledge and articles.

## Area rules, research and workflows

Rules for each area of the repo (Python services, the frontend, AI code, evals, tests,
infrastructure, content and more) live in `.claude/rules/<area>.md`, one file per area. Each
loads automatically when files matching its `paths` are read or edited, and binds as these
rules do; read the matching file before planning or delegating work in an area. Where an area
rule and rules 1–14 disagree, rules 1–14 win. The research behind the area rules (sources, gap
tables) is in `internal_docs/*-best-practices.md`, local notes that aren't committed. Workflows
(building UI, translating, verifying, migrations and more) are skills in `.claude/skills/`.
