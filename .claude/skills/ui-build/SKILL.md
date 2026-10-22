---
name: ui-build
description: Build or change a page or piece of UI in prepza's design language - reuse the existing pages' layouts and shared components, keep it simple, and show it before writing its tests. Use for any new or changed screen.
---

# Build UI the prepza way

The main rule: every screen is simple, seamless, unambiguous and intuitive. Check each change
against it. CLAUDE.md rules 5 to 7 apply in full.

## Start from what exists

1. **Change only what was asked.** Don't restyle or move anything else. For an open-ended layout
   request, offer two or three mockups first.
2. **Find the closest existing page and copy it** (rule 7):
   - a list page: the companies list (a `text-3xl` title with its main action on the right, rows
     in one `LIST_BOX` list, `divide-y rounded-2xl border`);
   - a page that starts a test: the home page's start (a large title and `DescriptionBox`);
   - a detail page: a company's test page.
3. **When asked for "like X"**, find X and reproduce it exactly. Name the component you're
   copying in your reply; if two could fit, ask which.

## Reuse these, never look-alikes

| Need | Use |
|---|---|
| Page header, back arrow, page help | `PageHeader`, `BackLink` (`help=` names its guide) |
| An editable title | `EditableTitle` |
| A job description box | `DescriptionBox` |
| A long list | `VirtualList` with `usePagedList` (loads more as you scroll; failures retry) |
| A choice from a few options | `PillSelect` (the gray pill opening the site's `DropdownMenu`); never a native `<select>` |
| A searchable choice | the `LanguagePicker` pattern: a Base UI `Combobox`, the search as the menu's first row with a magnifier, the menu as wide as the picker |
| A note or a warning | `InfoCard` / `WarningCard` (`components/warning-card.tsx`) |
| A confirmation | `ConfirmDialog`; steps to follow: `InstructionsDialog` |
| An integration row | `IntegrationRow` |
| A link page that can be gone or fail | `useLinkData` + `LinkStatus` |
| The emergency pause | `PausedNotice` |
| Dates, prices, percentages | `LocalDate`, `formatDay`, `formatPrice`, `formatPercent` (`lib/format.ts`): never hand-written |
| A service's refusal | `serviceRefusal(error, [statuses])` / `apiErrorMessage(error, fallback)` in a toast |

Primitives are in `components/ui/` (button, dialog, dropdown-menu, input, switch, tooltip, ...).
No new colors, shadows, gradients or effects unless asked.

## Layout rules

- **Same width everywhere** (rule 6): a page's `<main>` is `mx-auto max-w-page px-6` (80rem).
  Cards and forms inside may be narrower; the page never is; running text keeps a `max-w-3xl`
  column.
- **Titles** are lowercase, like the logo, and end with its blue dot; typed content keeps its
  case (`normal-case`).
- **Phones:** a header's button goes under the title, across the page
  (`max-sm:flex-col max-sm:items-stretch`); lists and cards reach the screen's edges
  (`-mx-6 sm:mx-0`, square corners); dialogs span the screen with their buttons side by side.
- **Right to left:** Arabic, Hebrew and Persian flip; use logical classes (`ps-`, `me-`,
  `text-start`), not `pl-`/`mr-`/`text-left`; people's text in a sentence goes in `<bdi>`, and
  text in another language carries its `lang` and `dir` (`.claude/rules/nextjs.md`).
- **Accessible from the start:** the rules in `.claude/rules/accessibility.md` (roles, focus,
  contrast from existing tokens, live regions, labels, 24 px targets, reduced motion), and
  `.claude/rules/performance.md` (Server Components, `"use client"` on the smallest leaf).

## Behaviour

- **No business logic in the frontend** (rule 5): limits, thresholds and what's allowed come
  from the API, and its messages are shown as they come.
- **Every text in 23 languages**: use the `translate` skill.
- **Every icon-only button** has an `aria-label` and a tooltip.

## Approval first (CLAUDE.md rule 14)

Build it in English only. Show it: the user reviews it on the local site, and send desktop and
phone screenshots from one short run (the `ui-check` skill). Then wait. Until the user approves
the UI, write no tests, run no test suites and translate nothing: a test run slows the local
site so much that the user can't move between pages to review it.

Once approved: the `finish-ui` skill (tests, translations, docs, one commit).
