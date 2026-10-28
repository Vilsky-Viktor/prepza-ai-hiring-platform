# Runbooks: the platform

What to do when the site or an API is down or slow, work waits or stops, the database strains, or a deploy's migration fails. The format, the switches and how to declare an incident are in [Runbooks](../runbooks.md). Pages (CRITICAL) reach the phone and email; tickets (WARNING) only email ([monitoring.tf](../../infra/terraform/monitoring.tf)).

- [Site or API down](#site-or-api-down)
- [API errors burning the budget](#api-errors-burning-the-budget)
- [Candidate answers slow](#candidate-answers-slow)
- [Server errors](#server-errors)
- [Events waiting or dead-lettered](#events-waiting-or-dead-lettered)
- [A scheduled job failed](#a-scheduled-job-failed)
- [A web hook signature refused](#a-web-hook-signature-refused)
- [Emails bouncing](#emails-bouncing)
- [The database under strain](#the-database-under-strain)
- [A failed backup](#a-failed-backup)
- [A stuck generation](#a-stuck-generation)
- [A failed migration during a deploy](#a-failed-migration-during-a-deploy)

## Site or API down

**How you notice:** **prepza <name> is down** (a page): the site's `/` or an API's `/ready` failed its uptime check from more than one of the three regions (Europe, the USA, Asia-Pacific), by an error, a timeout or a page without the expected text ([monitoring.tf](../../infra/terraform/monitoring.tf)). `/ready` fails when the service can't reach its database; Redis isn't checked. Users can't load pages, or the part that API serves fails.

**What the system does by itself:** Cloud Run replaces an instance that crashes, and a new one gets traffic only once `/ready` answers (the startup probe, [services.tf](../../infra/terraform/services.tf)). Nothing restarts an instance that answers but fails.

**What to do**

1. See which check fails and since when, and whether a deploy ran just before (GitHub → Actions → Deploy).
2. Read the service's errors (the command in [Before you start](../runbooks.md#before-you-start)) and its revisions:
   ```bash
   gcloud run services describe library --region=europe-west1 --format='value(status.conditions)'
   ```
3. After a deploy: roll back as in [infra/README.md](../../infra/README.md#deploys) ("Rolling back"). Errors about the database: check Cloud SQL's instance and [The database under strain](#the-database-under-strain). Every check down at once with Google Cloud's status page red: wait, and post on the status page.
4. Declare an incident if it lasts ([Runbooks](../runbooks.md#incidents)).

**Resolved when** the check passes from every region and the alert closes.

## API errors burning the budget

**How you notice:** **prepza API errors burning the budget fast** (a page) or **prepza API errors burning the budget** (a ticket): the public APIs, every backend but the site's pages, measured at the load balancer, answer too many requests with a 5xx for the objective, 99.5% over 28 days ([monitoring_slo.tf](../../infra/terraform/monitoring_slo.tf)). The fast one spends 2% of the month's error budget in an hour; the slow one would spend it all by the period's end.

**What the system does by itself:** nothing beyond each service's own retries. **prepza server errors** names the service with the most ([Server errors](#server-errors)).

**What to do**

1. Find the backend: Cloud Monitoring → **SLOs** → `prepza`, or the load balancer's 5xx by backend:
   ```bash
   gcloud logging read 'resource.type="http_load_balancer" AND httpRequest.status>=500' --freshness=1h --limit=50 --format='value(resource.labels.backend_service_name,httpRequest.status,httpRequest.requestUrl)'
   ```
2. Read that service's errors and Sentry; after a deploy, roll back ([infra/README.md](../../infra/README.md#deploys)). A provider failing behind it has its own runbook ([providers](providers.md)).
3. Once the month's budget is spent, reliability work (the cause, its test and alert) comes before new features until it recovers.

**Resolved when** the burn rate falls under the threshold and the alert closes.

## Candidate answers slow

**How you notice:** **prepza candidate answers slow** (a page) or **prepza candidate answers slowing** (a ticket): fewer than 95% of the interview service's (rounds) requests answer within 2 seconds at the load balancer, over 28 days ([monitoring_slo.tf](../../infra/terraform/monitoring_slo.tf)). Candidates wait at every question.

**What the system does by itself:** Cloud Run adds rounds instances up to its `max` (`locals.tf`); nothing else.

**What to do**

1. Check rounds' instance count and request latency in the Cloud Run console. At `max`, raising it needs the database's connection budget ([.claude/rules/database.md](../../.claude/rules/database.md)).
2. Check the database ([The database under strain](#the-database-under-strain)) and Cloud SQL Query Insights for rounds' slow queries.
3. After a deploy, roll back ([infra/README.md](../../infra/README.md#deploys)).

**Resolved when** the burn rate falls under the threshold and the alert closes.

## Server errors

**How you notice:** **prepza server errors** (a ticket): one Cloud Run service answered more than 5% of its requests with a 5xx for 10 minutes ([monitoring.tf](../../infra/terraform/monitoring.tf)). It names the service, the site's pages included, which the API objective leaves out.

**What the system does by itself:** nothing.

**What to do:** read that service's errors (command in [Before you start](../runbooks.md#before-you-start)) and Sentry. A provider in the traceback has its runbook ([providers](providers.md)); a database error, [The database under strain](#the-database-under-strain); a new error after a deploy, a fix or a rollback.

**Resolved when** the share falls under 5% and the alert closes.

## Events waiting or dead-lettered

**How you notice:** **prepza events waiting** (a ticket): a consumer's subscription (`<service>-events`) or the funnel's has held an event unhandled for over 15 minutes ([monitoring_backlog.tf](../../infra/terraform/monitoring_backlog.tf)). **prepza events dead-lettered** (a page): an event failed 50 deliveries and waits in `events-dead-letter` ([monitoring.tf](../../infra/terraform/monitoring.tf)). What that consumer does (emails, credits, the action log) happens late or not at all.

**What the system does by itself:** Pub/Sub retries each push with backoff (10 seconds to 10 minutes) for 50 attempts, several hours, then moves it to `events-dead-letter`, which keeps it 7 days ([pubsub.tf](../../infra/terraform/pubsub.tf)). Consumers are idempotent, so a retry or replay changes nothing twice. An event no retry can handle (data its handler needs missing or malformed, ids nothing knows, another service answering 400, 404, 410 or 422) is logged as an error, "Dropped event … no retry can handle it", and acknowledged instead ([unhandleable.py](../../packages/common/src/prepza_common/events/unhandleable.py)): it shows in Sentry, not in `events-dead-letter`.

**What to do**

1. Read the consumer's errors (its service name is the subscription's first part) and Sentry. notifications failing to send email: [Resend down](providers.md#resend-down).
2. Fix the cause (a provider, a bad deploy, a bug in the handler).
3. Replay the dead-lettered events once it's fixed, with the loop in [infra/README.md](../../infra/README.md#notes) ("Dead-lettered events"), within the 7 days.

**Resolved when** the subscription's oldest event is minutes old, `events-dead-letter` is empty and both alerts close.

## A scheduled job failed

**How you notice:** **prepza scheduled job failed** (a ticket): Cloud Scheduler logged a failed run, with the job's name ([monitoring.tf](../../infra/terraform/monitoring.tf), the jobs in [jobs.tf](../../infra/terraform/jobs.tf)).

**What the system does by itself:** a daily job is retried 3 times; a frequent one (every minute or few) just runs again next time. The email runs aren't retried: the next run and the catch-up hour send what's left ([infra/README.md](../../infra/README.md)).

**What to do**

1. Read the job's last attempts and its service's errors at that time:
   ```bash
   gcloud scheduler jobs describe billing-reconcile --location=europe-west1
   ```
2. Fix the cause; the email runs that fail on Resend: [Resend down](providers.md#resend-down).
3. Run a daily job again by hand once fixed: `gcloud scheduler jobs run <job> --location=europe-west1`. Every job is safe to run twice.

**Resolved when** the job's next run succeeds and the alert closes (after a day).

## A web hook signature refused

**How you notice:** **prepza web hook signature refused** (a page): Paddle's or Resend's web hook failed its signature check; the log line names the service ([monitoring.tf](../../infra/terraform/monitoring.tf)). Usually the secret is wrong, so every event is refused: paid top-ups get no credits, bounces aren't recorded.

**What the system does by itself:** the event is refused with a 401 and the provider retries it (Paddle for about two days, Resend's Svix for about a day); billing's daily reconciliation applies the payments whose web hooks never came ([A payment not credited](providers.md#a-payment-not-credited)).

**What to do:** compare the secret in Secret Manager (`paddle-webhook-secret` or `resend-webhook-secret`) with the provider's dashboard, add the right one and restart the service ([Paddle down](providers.md#paddle-down), step 4; for Resend, notifications), then resend the refused events from the provider's dashboard.

**Resolved when** new events are accepted (no new refusals in the logs) and the alert closes.

## Emails bouncing

**How you notice:** **prepza emails bouncing** (a page): more than `email_bounce_alert_hourly` (default 20) emails bounced, failed or were marked as spam in an hour ([monitoring_log_alerts.tf](../../infra/terraform/monitoring_log_alerts.tf)). Resend may suspend sending for every email if it goes on.

**What the system does by itself:** a hard bounce or a complaint puts the address on prepza's suppression list, the invite shows as undelivered, and a complaint about optional mail turns it off ([Notifications and emails](../features/notifications.md)).

**What to do**

1. In Resend's dashboard, see which emails bounce and why: one company's list of bad addresses, a DNS change ([infra/README.md](../../infra/README.md#email-deliverability)), or a wave of spam complaints.
2. One company's bad list: look at its support page in the admin zone and contact it; suspend it if it goes on ([Admin zone](../features/admin-support.md)).
3. DNS: check SPF, DKIM and DMARC as in [infra/README.md](../../infra/README.md#email-deliverability).

**Resolved when** bounces fall under the threshold, Resend shows no warning on the account and the alert closes.

## The database under strain

**How you notice:** a ticket: **prepza database connections high** (over 80% of `max_connections`), **prepza database CPU high** (over 80% for 15 minutes), **prepza database memory high** (over 90% for 15 minutes) or **prepza database disk filling** (over 85%) ([monitoring_database.tf](../../infra/terraform/monitoring_database.tf)). Users feel it only once requests slow down or fail, which the uptime checks and the objectives page.

**What the system does by itself:** each service's pool is bounded, so connections can't run away; storage grows by itself within its limit; Cloud SQL keeps serving under load, more slowly.

**What to do**

1. Cloud SQL → **Query Insights**: the slowest and most frequent queries, by database.
2. Connections: lower a service's `max` instances or raise `db_tier` and `db_max_connections` ([infra/README.md](../../infra/README.md)). CPU or memory: fix the heavy query (an index, a smaller result) or raise `db_tier`. Disk: find the table that grew and check its retention job.

**Resolved when** the metric is back under its threshold and the alert closes.

## A failed backup

**How you notice:** **prepza database backup failed** (a ticket): Cloud SQL logged a failed backup run ([monitoring_database.tf](../../infra/terraform/monitoring_database.tf)). Nothing changes for users; point-in-time recovery still covers 7 days.

**What the system does by itself:** the next day's automated backup runs as usual.

**What to do**

1. Check the instance's backups and start one by hand:
   ```bash
   gcloud sql backups list --instance=prepza --limit=5
   gcloud sql backups create --instance=prepza
   ```
2. Once the automated backups succeed again, delete the one made by hand (`gcloud sql backups delete <id> --instance=prepza`), at most 14 days later, so backups last no longer than the privacy policy says.

**Resolved when** an automated backup succeeds and the hand-made one is deleted.

## A stuck generation

**How you notice**

- **prepza generation queue backed up:** over 50 tasks queued for 15 minutes ([monitoring_backlog.tf](../../infra/terraform/monitoring_backlog.tf)).
- **prepza generations failing:** over 2 generations failed in an hour; the sweep's "stuck generations as failed" counts too ([monitoring_log_alerts.tf](../../infra/terraform/monitoring_log_alerts.tf)).
- **prepza generation tasks failing:** over 20% of task attempts failed for 30 minutes; Cloud Tasks drops a task after its last attempt ([monitoring_log_alerts.tf](../../infra/terraform/monitoring_log_alerts.tf)).
- Users: a generation's page keeps showing its progress and never ends, and a user reports it.

**What the system does by itself**

- **Delivery:** the `generation` queue tries a task up to 3 times (10 to 120 seconds apart), 10 at once at most ([jobs.tf](../../infra/terraform/jobs.tf)). A job first moves its generation from queued to running in one step, so a repeated delivery does nothing ([jobs.py](../../services/generation/src/generation/services/jobs.py)).
- **Time limit:** a run stops after 25 minutes and is saved as failed ([generation.py](../../services/generation/src/generation/constants/generation.py)).
- **The sweep** (Cloud Scheduler job `sweep`, every 5 minutes) marks as failed, "Generation stopped unexpectedly. Please try again.", a generation running untouched for 35 minutes (its worker died) or queued for 2 hours (its task never came). The `generation.failed` event tells companies, and the user can **Retry**; a task that comes after all finds it no longer queued and does nothing ([schedules.py](../../services/generation/src/generation/services/schedules.py), [generations.py](../../services/generation/src/generation/repositories/generations.py)).

**What to do**

1. Check the worker and the queue:
   ```bash
   gcloud run services describe generation-worker --region=europe-west1 --format='value(status.conditions)'
   gcloud tasks queues describe generation --location=europe-west1
   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="generation-worker" AND severity>=ERROR' --freshness=1h --limit=50
   ```
2. If the queue's state is `PAUSED`, resume it: `gcloud tasks queues resume generation --location=europe-west1`.
3. If the errors are OpenAI's, follow [OpenAI down](providers.md#openai-down); if Redis's, [Redis down](providers.md#redis-down); if the database's, [The database under strain](#the-database-under-strain).
4. If the worker crashes or is stuck on a bad revision, move it to the previous revision in the Cloud Run console, or roll back the release ([infra/README.md](../../infra/README.md#deploys), "Rolling back").
5. Let the sweep fail the stuck generations; to run it now rather than within 5 minutes:
   ```bash
   gcloud scheduler jobs run sweep --location=europe-west1
   ```
   It fails only generations past the limits above. Nothing marks one failed sooner, and an operator can't retry a company's generation: its owner clicks **Retry** (a template's: **Retry** on its page in the admin zone). Retry is refused while the emergency pause is on.

**Resolved when** the queue's depth falls, the alerts close, the worker logs `Marked N stuck generations as failed` for the ones the sweep caught, and a new generation finishes.

## A failed migration during a deploy

**How you notice**

- **prepza migration failed:** a Cloud Run job (a `<db>-migrate` job or `db-roles`) finished as failed ([monitoring_log_alerts.tf](../../infra/terraform/monitoring_log_alerts.tf)). The **Deploy** run also fails in GitHub Actions, at its **Migrations** step (or **Database users**).
- Users see nothing: the services step hasn't run, so every service still runs the previous version ([infra/README.md](../../infra/README.md#deploys)).

**What the system does by itself**

- The deploy runs the 9 `<db>-migrate` jobs one at a time, in the order library, generation, rounds, companies, billing, notifications, ats, api, assistant, and stops at the first failure; it moves no service ([deploy.yml](../../.github/workflows/deploy.yml)).
- A migrate job isn't retried (`max_retries = 0`, [services.tf](../../infra/terraform/services.tf)).
- One service's migrations run in a single transaction, so the one that failed left its database as it was ([billing's env.py](../../services/billing/migrations/env.py), the same in each service). The databases migrated before it keep their new schema; the old version keeps working on it, as migrations only add ([Deployment](../deployment.md#migrations)).

**What to do**

1. In the failed run, see which `<db>-migrate` job failed, then read its logs:
   ```bash
   gcloud run jobs executions list --job=companies-migrate --region=europe-west1 --limit=3
   gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="companies-migrate"' --freshness=1h --limit=100
   ```
2. **A passing failure** (the database restarting, a connection refused): run the same version again, in **Actions → Deploy → Run workflow**, with the tag and **Run migrations** ticked. The migrations that already ran do nothing the second time.
3. **A wrong migration** (it fails on the data, say): fix it in a new commit and release a new tag ([infra/README.md](../../infra/README.md#deploys)). Don't redeploy the failed tag.
4. **A migration that ran but did damage** (it deleted or changed data): turn maintenance mode on and restore that database from a point in time before the deploy, as in [infra/README.md](../../infra/README.md#restore-drill).
5. If the migrations passed and the **Services** or **Smoke test** step failed, services may already run the new images: roll back as in [infra/README.md](../../infra/README.md#deploys) ("Rolling back"), with **Run migrations** off.

**Resolved when** a Deploy run passes every step, the smoke test included, and the release shows on GitHub.
