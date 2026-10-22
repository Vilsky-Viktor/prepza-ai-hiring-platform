# Runbooks

What to do when an alert fires, how to run an incident and how to learn from it. Each runbook section says how you notice, what prepza already does by itself, the steps, and how to know it's over. The alerts are in `infra/terraform/monitoring*.tf` (see [infra/README.md](../infra/README.md#bootstrap-once), step 5); each one's email links its section.

- [Before you start](#before-you-start)
- [Alerts and their runbooks](#alerts-and-their-runbooks)
- [Incidents](#incidents)
- [Postmortems](#postmortems)
- [When you're unreachable](#when-youre-unreachable)
- [Reviews](#reviews)
- [Providers](runbooks/providers.md): Paddle, a payment not credited, OpenAI, Resend, Redis, AI spend.
- [The platform](runbooks/platform.md): the site or an API down or slow, waiting events, scheduled jobs, web hooks, bounces, the database, backups, generations, migrations.

## Before you start

- **The switches** are in the admin zone: **Admin zone → Controls** (`/superadmin/controls`). The emergency pause answers new interviews, invites, practice, previews, generations, the help chat and the assistant with a 503; maintenance mode closes the whole site but keeps `/internal/` and `/webhooks/` open, so no event, job or payment is lost ([Admin zone](features/admin-zone.md#controls)).
- **Both switches live in Redis.** With Redis down each instance keeps the state it last read (off if it never read one), and they can't be turned on or off ([Admin zone](features/admin-zone.md#emergency-pause)).
- **Billing isn't switched** by maintenance mode ([Admin zone](features/admin-zone.md#maintenance-mode)).
- **The limits** are in **Admin zone → Controls → Limits**: each one's value, its default and its hits in the last 7 days; a change is in effect within 30 seconds ([Admin zone](features/admin-zone.md#limits)). **Admin zone → Stats → AI costs** (`/superadmin/stats/ai-costs`) shows what AI cost, by action, model, company and user, today's shared budgets and the limits hit ([Admin zone](features/admin-zone.md#ai-costs)).
- **Logs:** every command below assumes `gcloud config set project prepza-prod` and the region `europe-west1`. A service's recent errors:
  ```bash
  gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="billing" AND severity>=ERROR' --freshness=1h --limit=50
  ```
- **Restarting a service** after changing one of its secrets (services read `latest` only when they start, [infra/README.md](../infra/README.md#bootstrap-once) steps 8 and 9):
  ```bash
  gcloud run services update billing --region=europe-west1 --update-labels=restarted=$(date +%s)
  ```

## Alerts and their runbooks

Two severities. A **page** (CRITICAL) is a symptom users feel now; it reaches the phone (the Cloud Monitoring app, `alert_app_channel`, and SMS as a backup, `alert_sms`) and email. A **ticket** (WARNING) is a cause or a slow drift, by email only; handle it within a working day.

| Alert | Severity | Runbook |
|---|---|---|
| prepza <name> is down | page | [Site or API down](runbooks/platform.md#site-or-api-down) |
| prepza API errors burning the budget fast / burning the budget | page / ticket | [API errors burning the budget](runbooks/platform.md#api-errors-burning-the-budget) |
| prepza candidate answers slow / slowing | page / ticket | [Candidate answers slow](runbooks/platform.md#candidate-answers-slow) |
| prepza server errors | ticket | [Server errors](runbooks/platform.md#server-errors) |
| prepza events dead-lettered / events waiting | page / ticket | [Events waiting or dead-lettered](runbooks/platform.md#events-waiting-or-dead-lettered) |
| prepza scheduled job failed | ticket | [A scheduled job failed](runbooks/platform.md#a-scheduled-job-failed) |
| prepza web hook signature refused | page | [A web hook signature refused](runbooks/platform.md#a-web-hook-signature-refused) |
| prepza emails bouncing | page | [Emails bouncing](runbooks/platform.md#emails-bouncing) |
| prepza database connections, CPU, memory high, disk filling | ticket | [The database under strain](runbooks/platform.md#the-database-under-strain) |
| prepza database backup failed | ticket | [A failed backup](runbooks/platform.md#a-failed-backup) |
| prepza generations failing, generation tasks failing / generation queue backed up | page / ticket | [A stuck generation](runbooks/platform.md#a-stuck-generation) |
| prepza migration failed | page | [A failed migration during a deploy](runbooks/platform.md#a-failed-migration-during-a-deploy) |
| prepza Paddle failing | page | [Paddle down](runbooks/providers.md#paddle-down) |
| prepza payment not credited | page | [A payment not credited](runbooks/providers.md#a-payment-not-credited) |
| prepza OpenAI failing | page | [OpenAI down](runbooks/providers.md#openai-down) |
| prepza Redis failing | page | [Redis down](runbooks/providers.md#redis-down) |
| prepza AI spend high, AI stopped for many / AI spend high today | page / ticket | [AI spend high or AI stopped](runbooks/providers.md#ai-spend-high-or-ai-stopped) |
| Budget emails (50%, 90%, 100%, forecast) | ticket | [infra/README.md](../infra/README.md#bootstrap-once), step 5 |

A new alert ships with its section, and `scripts/tests/test_alert_runbooks.py` fails on an alert without a severity or a runbook link, or a link to a section that doesn't exist.

## Incidents

- **Declare one early:** when customers see the problem, when you need someone's help (a provider's support), or when an hour of work hasn't solved it. When unsure how bad it is, treat it as the worse case.
- **Keep a timeline** as you go, in UTC: what you saw, what you did, what changed. It becomes the postmortem's.
- **Tell customers** on the status page (Better Stack, set up at launch, see [infra/README.md](../infra/README.md#notes)) when they see it, and again when it's over. For a long outage or one affecting candidates, maintenance mode shows everyone a clear page ([Before you start](#before-you-start)).
- **A personal data breach** also follows the breach response plan and its clocks (`internal_docs/compliance/breach-response-plan.md`, local), from the moment you become aware of it.

## Postmortems

A short, blameless one after an outage users saw, any data loss, a manual intervention in production, a resolution that took longer than a working day, or a problem users reported before an alert did. One page, in `internal_docs/postmortems/<date>-<name>.md` (local):

- **Impact:** who saw what, for how long, and what it cost (failed payments, lost emails, refunds).
- **Timeline:** from the first sign to resolved, in UTC.
- **Causes:** the root cause and what contributed (a missing alert, a slow step). About systems, never people.
- **Actions:** each one a test, an alert or a fix, with its commit once done; a manual step that came back becomes automation.

## When you're unreachable

prepza is run by one person, so some waiting is accepted:

- **Accepted:** a page may wait until you're back; dead-lettered events are kept 7 days and replayed then; payments whose web hooks failed are applied by the daily reconciliation; a failed scheduled email run is caught up by its next run.
- **Before going offline for more than a day:** check that no alert is open, write the dates and who (if anyone) can reach you at the top of your incident notes, and leave nothing half-deployed.
- **The fallback** for anything that can't wait: maintenance mode, which closes the site without losing events, jobs or payments, and a post on the status page.

## Reviews

- **The objectives** (`infra/terraform/monitoring_slo.tf`): their error budgets monthly at first, then quarterly. When a budget is spent, reliability work comes before features until it recovers; change a goal only on purpose, with the review.
- **The restore drill** quarterly, timed against the recovery target ([infra/README.md](../infra/README.md#restore-drill)), its result kept with the review.
