---
paths:
  - "frontend/**"
---

# Frontend (Next.js)

## Layout

The frontend has only the parts it uses (rule 4: no Redux, axios, Jest or Husky; it uses
vitest, Playwright, next-intl's `messages/` and `i18n/`, Tailwind):

```
src/
├── app/                  # App Router: pages, layouts, route groups, API routes
├── components/           # common/, ui/ (shadcn), sections/, templates/, icons/
├── features/<name>/      # A feature's components/, hooks/, services/, types/, utils/
├── config/, contexts/, hooks/, lib/, providers/, styles/, types/ (api/), utils/
└── stores/               # Only if client state is ever needed
public/assets/            # fonts/, images/, svgs/
tests/                    # vitest
```

From today's layout: everything under `src/`; `constants/` → `config/`; feature folders in
`components/` (company, billing, assistant, generation, landing, …) → `features/<name>/`; shared
components → `components/common/`; providers → `providers/`; `app/globals.css` → `styles/`.

## Languages and direction

Every page works in all 23 languages, three of them right to left (ar, he, fa). Messages
themselves: `.claude/rules/content-i18n.md`.

- `<html lang dir>` per page; any block in another language than the page (an interview's
  questions, an article, a language's own name) carries its own `lang` and `dir`
  (`textDirection(language)`).
- Logical utilities only: `ms-/me-/ps-/pe-/start-/end-/text-start/rounded-s/border-s`, and
  `rtl:` only where no logical utility exists; never `ml-/mr-/pl-/pr-/left-/text-left` (centring
  with `left-1/2 -translate-x-1/2` is fine). Inline styles use `insetInlineStart`, not `left`.
- Mirror icons and controls that show direction or progress (arrows, chevrons, send, back,
  sliders, progress bars and their end labels, `rtl:-scale-x-100`); never mirror logos,
  checkmarks, clocks, media play, numbers or code. Base UI gets the page direction through
  `DirectionProvider`; arrow keys follow the visual direction.
- Values typed by people (names, companies, emails, titles, answers) are isolated inside a
  sentence with `<bdi>` (a `t.rich` tag), or FSI/PDI in attributes; free-text inputs and
  textareas take `dir="auto"`; emails, URLs, code and numbers stay `dir="ltr"` inside RTL text.
- Numbers, money, percentages, dates, lists and relative times go through `lib/format.ts` or
  next-intl's formatter with the active locale; never `toFixed`, string building or ISO dates in
  text. The currency code comes from the backend; calendar days format in UTC so they never
  shift; moments format in the browser's time zone.
- Never join translated sentences or pieces in code (no `" "` or `", "` between messages):
  one message per sentence, punctuation inside it.
- Count characters by grapheme (`Intl.Segmenter`, one shared helper) for initials and
  truncation, never by UTF-16 unit.
- Layouts allow for expansion (short strings can grow 200–300%): no fixed-width buttons or labels.
- Fonts cover every script shipped (subsets per script, `latin-ext` for pl, tr, et, vi where the
  font has it); no `letter-spacing` on Arabic or Persian, no forced `uppercase` on other
  languages' text; tall scripts get more line height, CJK larger sizes.
- Locale choice: the URL prefix (public pages), then the saved setting, then `Accept-Language`;
  `zh-TW`, `zh-HK` and other Traditional Chinese never silently get Simplified.

Research (local notes, git-ignored): `internal_docs/best-practices/i18n.md`.
