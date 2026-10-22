# prepza.

⭐ Like it? Star it. ⭐ Helps a looooooot

Timed knowledge interviews for hiring, made from a job description or a ready-made template. A company pastes the role, reviews the topics, and invites candidates; each candidate gets their own random questions with a countdown on every one, and the company sees their scores and integrity signals. People preparing for a role practise free on the templates. Any role, 23 languages, from $2 per candidate.

**For private and research use only.** This repository may not be used for commercial purposes. See [LICENSE.md](LICENSE.md) (PolyForm Noncommercial 1.0.0).

![prepza](screenshot.png)

## Features

- **Interviews from a job description:** the AI proposes topics, the company reviews them for free, then each topic gets a bank of multiple-choice questions, about 1 in 10 of them "select all that apply", scored by points; on a topic about code, queries or commands about a third show a short example, and each is written to be read and answered within a minute (a minute and a half for the hardest).
- **Ready-made templates:** copy an interview by role, level and language at once, for free.
- **Timed and fair:** each candidate gets their own random questions, with a server-enforced countdown on every one.
- **Scorecards and reports:** grades against a pass mark, integrity flags, and PDF reports to download, email or share.
- **Invites three ways:** by email, from a list or file, or through one shareable link for a job ad.
- **Teams and verified companies:** owners, admins and viewers; a check next to a verified company's name.
- **The company's brand:** on its brand tab a company sets its logo, colors (a light and a dark set, refused when any text would be hard to read), font (prepza's Poppins and Geist pair or one of the most used web fonts) and how round cards and buttons are, with a live preview; candidates see the whole interview process in them, without prepza's header or footer, in the theme the link, SDK or API asks for, or their own.
- **Questions that fix themselves:** answers, votes and reports flag weak questions, and a verifier fixes them.
- **ATS integrations:** candidates from Workable, Greenhouse, Teamtailor, Recruitee and Breezy HR are invited automatically, and results go back.
- **Slack:** a company picks a channel and which of its notifications go there.
- **Public API:** API keys, each with only the permissions ticked for it (narrowed later, never widened), to list interviews, invite candidates (also straight from a company's own platform: no sign-in, no emails, back to that platform at the end, or the interview embedded in its own page with prepza's SDK, on a verified company's website) and read results, and signed web hooks when a candidate starts, finishes, isn't reached, expires or is removed, or an interview is ready, with a test send and a delivery log; the developer docs on the site cover the API, web hooks, the SDK, the MCP server and the objects.
- **AI apps over MCP:** Claude, ChatGPT and other AI apps connect at `/mcp` once the user allows them, and read and change what the user can, with the user's permissions; an agent on a server signs in with a company API key that has the MCP permission, limited to its company and its permissions. Asked what's new, an app hears what happened in the user's companies since its last check (candidates who started or finished, undelivered invites, questions flagged or fixed, low credits, ...), each update once per app, which a daily scheduled task in the app turns into a morning summary. The developer docs' MCP tab shows how, with example agents in Python and TypeScript.
- **Pay per candidate:** credits that never expire, $2–5 per candidate, with no paid subscription (an optional automatic top-up saves the card with Paddle as a $0 subscription).
- **Free practice:** people preparing for a role practise on the templates' practice questions, which companies' interviews never use.
- **23 languages:** the interface, generated interviews, emails and news posts.
- **News:** a public news page and every user's bell; posts are written in English in the admin zone and translated automatically.
- **Campaigns:** product updates and offers emailed to the users who chose them, written in the admin zone, translated and sent through one bulk sender that legal notices share, with its own suppression list.
- **Admin zone:** templates, news, campaigns, question quality, verification, support (finding an account, a company, an interview or a candidate; a company's credits and history, adjusting them; an account's companies, top-ups, email settings and whether its address is on the suppression list; a candidate's progress, credits and the company emails stopped for them; a company's and an account's AI cost), pass rates, stats, AI costs (by action, model and who it was for, the shared budgets and the limits hit), the pause and maintenance switches, and every usage limit, editable.

## Quick start

Requirements: Docker with Compose, and an OpenAI API key.

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env.
docker compose up --build
```

Then open the app at http://localhost:8090. Sign-in uses the Firebase Auth emulator (http://localhost:4100), and every email lands in Mailpit (http://localhost:8125). More in [Development](docs/development.md).

## Documentation

### Product

| Page | What it covers |
|---|---|
| [Companies](docs/features/companies.md) | Company names, the team and its roles, the brand (logo, font, corner rounding, light and dark colors on candidates' pages), verification, page guides |
| [Interviews](docs/features/interviews.md) | Making an interview, topic review, the interview page and its settings, preview |
| [Candidates](docs/features/candidates.md) | Invites, the shareable link, taking an interview, timing, scorecards, reports |
| [Templates and practice](docs/features/templates-and-practice.md) | The question bank, copying templates, slugs, free practice |
| [Credits and payments](docs/features/billing.md) | Credits, top-ups, automatic top-up, referrals, a company's billing tab, AI usage and limit hits, setting up Paddle |
| [ATS integrations](docs/features/ats.md) | Connecting Workable, Greenhouse, Teamtailor, Recruitee and Breezy HR, linked jobs, results back to the ATS |
| [Public API](docs/features/api.md) | API keys, their expiry and permissions, the routes, invites without sign-in, return addresses and themes, signed web hooks, the SDK that embeds the interview, the API page and the developer docs |
| [Notifications and emails](docs/features/notifications.md) | The bell, emails, legal notices and campaigns, Slack, setting up Resend and Slack |
| [In-app assistant](docs/features/assistant.md) | Mira, the "ask Mira" panel: answers about a user's companies and about prepza (FAQ answers when signed out), voice input, its limits, retention and tools |
| [AI apps over MCP](docs/features/mcp.md) | Connecting Claude, ChatGPT and other AI apps, and agents with an API key: the consent page, OAuth, the tools, what's new since the last check, connections, limits, the developer docs' MCP tab |
| [Admin zone](docs/features/admin-zone.md) | Superadmins' templates, news, campaigns, quality, support, pass rates, stats, AI costs, pause and maintenance mode, limits |
| [Admin zone: Support](docs/features/admin-support.md) | Finding an account, company, interview or candidate from a complaint, their support pages, credits, suspension, stopping emails, logs |
| [Public site](docs/features/site.md) | Home page, skills tests, articles, FAQ, legal pages, contact, SEO |
| [Languages](docs/features/languages.md) | The 23 languages, language addresses, fonts, right-to-left |

### Engineering

| Page | What it covers |
|---|---|
| [Architecture](docs/architecture.md) | Services, how they call each other, background jobs, events and Pub/Sub |
| [Generation and question quality](docs/generation.md) | The generation pipeline, question reuse and checks, generation settings, models, rate limits |
| [Development](docs/development.md) | Running locally, settings, the local stack, everyday commands, conventions |
| [Testing](docs/testing.md) | Unit, integration, browser, end-to-end and load tests; CI |
| [Deployment](docs/deployment.md) | Production images, migrations, Sentry, CI/CD, releases and rollbacks |
| [Runbooks](docs/runbooks.md) | What to do when an alert fires (each one's section: a provider failing, the site or an API down or slow, waiting events, the database, a stuck generation, a failed migration), how to run an incident and write its postmortem |
| [infra/README.md](infra/README.md) | Google Cloud with Terraform: bootstrap, deploys, restore drill |
| [packages/common](packages/common/README.md) | The code the API services share |
| [e2e_tests/load/README.md](e2e_tests/load/README.md) | Load test settings, thresholds and results |
| [evals/README.md](evals/README.md) | Offline evals of models and prompts |

## Project conventions

See [CLAUDE.md](CLAUDE.md): separate modules for schemas, models, prompts, helpers and constants; `app/main.py` only wires the app; at most 300 lines per file; the simplest solution that works; and no business logic on the frontend (rules, thresholds and decisions live in the services).
