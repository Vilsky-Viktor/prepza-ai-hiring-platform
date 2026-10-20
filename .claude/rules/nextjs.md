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
