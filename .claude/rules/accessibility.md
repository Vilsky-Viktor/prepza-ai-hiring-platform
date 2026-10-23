---
paths:
  - "frontend/**"
  - "services/rounds/**"
  - "services/companies/app/constants/invites.py"
  - "services/notifications/app/templates/**"
---

# Accessibility: WCAG 2.2 AA

Every page meets WCAG 2.2 AA in all 23 languages, light and dark. It matters by law: the AI Act
(accessibility for high-risk systems), the ADA and the UK Equality Act (reasonable adjustments
for applicants, extra time on a timed test), Section 508 and public buyers, who ask for proof.
A change to the candidate's pages updates `internal_docs/compliance/accessibility-review.md`
(local, rule 9).

## Building blocks

- Interactive parts are Base UI primitives or native elements: a `<button>` for actions, a link
  for navigation. Hand-made ones follow the WAI-ARIA Authoring Practices pattern; no
  accessibility overlay or extra ARIA library (rule 4).
  - Modal dialog: `role="dialog"`, `aria-modal`, a labelled title, focus kept inside, Escape
    closes, focus returns to the opener.
  - Menu button: `aria-haspopup`, `aria-expanded`, arrow keys between items, Escape closes. Site
    navigation is links, not a `menu`.
  - Slider: a label, `aria-valuetext` when the number alone means little, arrows, Page Up/Down,
    Home/End; also works with taps or clicks, never only by dragging.
  - Tabs: `tablist` > `tab` with `aria-selected` and `aria-controls`; each panel
    `role="tabpanel"` with `aria-labelledby`; arrow keys (mirrored in RTL), roving `tabindex`.
- Icon-only buttons use `IconButton` (its `label` is required) or an `aria-label`.

## Keyboard and focus

- Everything works from the keyboard with a visible focus indicator; never `outline-none`
  without a `focus-visible:` replacement.
- Focus moves to new content (a dialog, the next question) and back to the trigger when it
  closes. A skip link passes the repeated navigation.
- Sticky headers, footers and banners never fully hide the focused element (`scroll-padding`).

## Contrast

- From existing tokens (rule 7): text 4.5:1 (3:1 from 24 px, or 18.7 px bold); a control's
  boundary or state (an unchecked box, a switch's off track, a focus ring) 3:1 against what is
  next to it. Opacity on a text token (`/60`, `/70`) lowers contrast: compute it, never guess.
  Disabled controls and logos are exempt. If no existing token reaches the ratio, ask before
  adding one.

## Messages, forms and errors

- A message that appears without focus (an error, "saved", a limit, why a button stopped
  working) is in a live region that exists before the message: `role="status"` by default,
  `alert` only when urgent. A toast that disappears never holds the only way to act.
- Every field has a label (a placeholder alone vanishes on typing); multi-field forms show
  visible labels, built from an existing form's pattern (user-decided exception, 2026-10-23: the
  contact form shows placeholders only, each field keeping its name as `aria-label`). A labelled
  field shows its name inside it (`FloatingInput` and `FloatingTextarea` in
  `components/ui/floating-field.tsx`, `label` on `PillSelect` and `MenuPill`): a real
  `<label htmlFor>` that rests where the value goes while the field is empty and rises onto the
  top edge once it's focused or filled (CSS only, autofill included, no motion under reduced
  motion). A unit or sign sits inside the field (`suffix`, `prefix`), never as text beside it.
  A field's focus is a 1px border in `--ring` (3:1 on the field and the page in both themes), no
  extra ring; an invalid field keeps its 1px destructive border.
  Checkboxes, radios and switches keep their side labels. A field's error is text next to it that
  names the problem and how to fix it, linked with `aria-describedby` and flagged with
  `aria-invalid`. `autocomplete` on personal data.
- Don't ask for what the user already gave in the same process: prefill it or offer to pick it.
- Sign-in has no memory or puzzle test and allows paste and password managers.
- Help (contact, chat) sits in the same place on every page that has it.

## Targets, motion, language

- Targets at least 24 × 24 CSS px, or spaced so a 24 px circle around each doesn't overlap
  another (`icon-xs` is the smallest; small controls enlarge their hit area).
- Motion respects `prefers-reduced-motion`: non-essential motion stops, and the global reset
  sets `animation-iteration-count: 1` so infinite loops stop too. Nothing moves on its own for
  more than 5 seconds next to other content (a badge carries a state, not a looping animation).
  User-decided exception (2026-10-22): the landing page's moving pictures, the hero's play
  button's pulsing ring, the "ask Mira" button's circling arc and sparkles, and the bell's
  swing while anything is unread keep looping with no pause button; reduced motion still stops them. Don't re-raise it in audits.
- `<html lang dir>` per locale; text in another language (a language's own name in a picker, an
  interview's questions) carries its own `lang`; direction-neutral classes (`.claude/rules/nextjs.md`).

## Time limits

- Every time limit a person faces can be turned off, adjusted or extended, decided and enforced
  by the backend (rule 5). An interview's limit is essential to what it measures, so the company
  extends it per candidate before they start (extra time from the options the API sends); the
  server enforces it; the countdown is `role="timer"` with a polite warning before the end.
  Practice measures nothing, so it offers more time or none.

## Checked by tests

- Browser tests find elements by role and accessible name (rule 8), which checks roles and names
  as they go; an icon-only button's label is asserted.

Research (local notes, git-ignored): `internal_docs/best-practices/accessibility.md`.
