# Runbooks

What to do when a provider fails, a generation hangs, a deploy's migration fails or AI spending runs high. Each runbook says how you notice, what prepza already does by itself, the steps, and how to know it's over. The alerts are the ones in `infra/terraform/monitoring*.tf` (see [infra/README.md](../infra/README.md#bootstrap-once), step 5); the names below are their titles in the alert emails.

- [Before you start](#before-you-start)
- [Paddle down](#paddle-down)
- [A payment not credited](#a-payment-not-credited)
- [OpenAI down](#openai-down)
- [Resend down](#resend-down)
- [A stuck generation](#a-stuck-generation)
- [A failed migration during a deploy](#a-failed-migration-during-a-deploy)
- [Redis down](#redis-down)
- [AI spend high or AI stopped](#ai-spend-high-or-ai-stopped)

## Before you start

- **The switches** are in the admin zone: **Admin zone → Controls** (`/superadmin/controls`). The emergency pause answers new interviews, invites, practice, previews, generations, the help chat and the assistant with a 503; maintenance mode closes the whole site but keeps `/internal/` and `/webhooks/` open, so no event, job or payment is lost ([Admin zone](features/admin-zone.md#controls)).
- **Both switches live in Redis.** With Redis down they count as off and can't be turned on ([Admin zone](features/admin-zone.md#emergency-pause)).
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

## Paddle down

**How you notice**

- **prepza Paddle failing:** over 3 calls to Paddle's API failed in 15 minutes: no answer, a 5xx, or Paddle refusing billing itself (`401` or `403`: the API key wrong, expired or short of a permission; `429`: over Paddle's rate limit). billing logs each as "Paddle unavailable"; a refusal of the request, such as a declined card, doesn't count ([paddle.py](../services/billing/app/integrations/paddle.py), [monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)). **prepza server errors** may fire too, once failed checkouts and invoices pass 5% of a service's requests ([monitoring.tf](../infra/terraform/monitoring.tf)).
- **prepza web hook signature refused** means our secret is wrong, not that Paddle is down (see the last step).
- Users: **Top up** says "Couldn't open the checkout. Please try again." ([buy-button.tsx](../frontend/components/billing/buy-button.tsx)); invoice downloads fail; turning automatic top-up off, or deleting a company or an account with one, fails and can be tried again ([auto_top_ups.py](../services/billing/app/services/auto_top_ups.py)). Prices still show: the catalog comes from billing's settings, not from Paddle ([billing.py](../services/billing/app/routers/billing.py)).

**What the system does by itself**

- Billing never retries a call to Paddle beyond the shared client's connection retries (3, with a 30-second timeout, [http.py](../packages/common/src/prepza_common/http.py)). A checkout that fails is simply not created; nothing is charged.
- **Paddle's web hooks:** Paddle retries a web hook until it gets a 2xx, and granting credits is idempotent, so a late or repeated `transaction.completed` adds the credits once ([billing.py](../services/billing/app/routers/billing.py), [topups.py](../services/billing/app/services/topups.py)). Payments made during the outage get their credits when Paddle delivers; any web hook Paddle gives up on (after about two days) is applied by billing's daily reconciliation, which logs each one it had to apply ([Missed web hooks](features/billing.md#missed-web-hooks)).
- **Automatic top-ups:** a charge Paddle doesn't answer (a timeout or a 5xx) isn't counted as declined; if it went through, the web hook adds the credits, and no other charge follows until they come, for at most a day (`AUTO_TOP_UP_UNCREDITED_WAIT`). A declined card (any other 4xx) tells the company's owners and admins and is tried again after 1, 3 and 7 days, then paused until its card is updated (at once for a decline that can't pass later); Paddle refusing billing's key or rate limit isn't told to the owner as their card's, and waits like a charge Paddle didn't answer ([auto_top_ups.py](../services/billing/app/services/auto_top_ups.py), [Credits and payments](features/billing.md)).

**What to do**

1. Check Paddle's status page. If Paddle is down, there's nothing to switch: wait. Maintenance mode wouldn't help, as it leaves billing open.
2. If Paddle is up, read billing's errors (command above). A `401` or `403` from Paddle means the API key: Paddle's keys expire (90 days by default, a year at most), so check its expiry and permissions in Paddle's dashboard against `paddle-api-key` (its permissions are in [Credits and payments](features/billing.md#setting-up-paddle)), add the right one and restart billing:
   ```bash
   printf '%s' "$PADDLE_API_KEY" | gcloud secrets versions add paddle-api-key --data-file=-
   gcloud run services update billing --region=europe-west1 --update-labels=restarted=$(date +%s)
   ```
3. Once Paddle is back, open its dashboard → **Developer tools → Notifications** and check the web hook deliveries. Paddle retries failed ones by itself; resend any that it gave up on.
4. **prepza web hook signature refused** with `paddle` in the log: compare `paddle-webhook-secret` with the destination's secret key in Paddle, add the right one as above (`paddle-webhook-secret`), restart billing, then resend the refused events from Paddle's dashboard. Until then, paid top-ups get no credits.

**Resolved when** a top-up's checkout opens again, billing logs no new Paddle errors, Paddle's dashboard shows the web hooks delivered, and the alert closes.

## A payment not credited

**How you notice:** **prepza payment not credited**, on the first of these lines in billing's logs ([monitoring_billing.tf](../infra/terraform/monitoring_billing.tf)):

- **"… : refund it"** (an error): billing refused to credit a paid transaction it can't give credits for: one it didn't create ("wasn't created by billing"), one for a company deleted after the checkout ("pays into a wallet that's gone"), or an item it doesn't sell ("isn't one we sell") ([topups.py](../services/billing/app/services/topups.py));
- **"Transaction … has no valid owner"**: a payment with no company in its custom data, so nobody was credited;
- **"Reconciliation credited transaction …"** or **"Reconciliation counted adjustment …"**: the daily reconciliation applied a payment or a refund whose web hook never came; the company now has the right credits, but web hooks are failing ([reconciliation.py](../services/billing/app/services/reconciliation.py), [Missed web hooks](features/billing.md#missed-web-hooks));
- **"Reconciling … failed"**: reconciling one transaction or adjustment raised an error; it stays uncredited until a run succeeds.

**What the system does by itself:** nothing is credited for a "refund it" or "no valid owner" line; billing answers Paddle 200, so it isn't retried. Reconciliation runs daily and tries a failed item again the next day.

**What to do**

1. Read the lines (the ids are Paddle's transaction and adjustment ids):
   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="billing" AND (jsonPayload.message:"refund it" OR jsonPayload.message:"has no valid owner" OR jsonPayload.message:"Reconciliation" OR jsonPayload.message:"Reconciling")' --freshness=2d --limit=50
   ```
2. **"refund it":** open the transaction in Paddle's dashboard (**Transactions**, search by its id) and refund it in full (or the item named), with a note. The refund's web hook takes back nothing, as nothing was credited.
3. **"no valid owner":** find the buyer from the transaction's customer in Paddle. If they meant to top up a company, give its credits in the admin zone (**Support → the company → Adjust credits**, with the transaction id in the note, [Admin zone](features/admin-support.md)); otherwise refund it as above.
4. **"Reconciliation credited / counted":** the credits are right now. Find why the web hook didn't arrive: **prepza web hook signature refused** or **prepza Paddle failing** around that time ([Paddle down](#paddle-down)), or Paddle's dashboard → **Developer tools → Notifications** showing failed deliveries.
5. **"Reconciling … failed":** read the traceback under the line and Sentry, fix the cause; the next daily run applies it, or run the job now:
   ```bash
   gcloud scheduler jobs run billing-reconcile --location=europe-west1
   ```

**Resolved when** every transaction named is refunded or credited, the reason web hooks were missed is fixed, and the alert closes.

## OpenAI down

**How you notice**

- **prepza OpenAI failing:** over 10 OpenAI errors in 15 minutes ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)). It counts errors whose traceback or message names `openai.`: generation's and the help chat's failures by their traceback, the assistant's by its message, which names only the error's type, such as `openai.APIConnectionError` ([turns.py](../services/assistant/app/services/turns.py)).
- **prepza generations failing:** over 2 generations failed in an hour, counted from the logs: a run that errored, or the sweep marking stuck ones failed ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)). A failed generation doesn't fail its task, which saves the failure on the generation ([jobs.py](../services/generation/app/services/jobs.py)), so **prepza generation tasks failing** fires for other tasks, such as news translations, and a worker that crashes.
- Users: a generation ends as failed, "Generation failed. Please try again.", with **Retry**; the help chat and the assistant answer "Couldn't get a reply right now. Please try again."; voice input fails with a `502` ([assistant.md](features/assistant.md)). Candidates' interviews don't call OpenAI.

**What the system does by itself**

- **Generation:** each AI call is tried again up to twice (`LLM_MAX_RETRIES`), and one silent for 5 minutes counts as hung (`LLM_TIMEOUT_SECONDS`, [generation.py](../services/generation/app/constants/generation.py)). A run that still fails is saved as failed, and companies hears it through the `generation.failed` event. Nothing retries it: the user does, and **Retry** continues from the run's last checkpoint ([retry.py](../services/generation/app/services/retry.py), [Generation](generation.md)).
- **Regenerating one question:** past 110 seconds the old question stays and the company is told to try again ([Generation](generation.md)).
- **Help chat:** 3 retries, a 60-second timeout ([rounds llm.py](../services/rounds/app/integrations/llm.py)). **Assistant:** 2 retries, a 60-second timeout; the failed answer is saved as failed and its tokens still count toward the budgets ([assistant llm.py](../services/assistant/app/integrations/llm.py), [turns.py](../services/assistant/app/services/turns.py)).
- **Answer-key checks** (OpenAI's Batch API, every 10 minutes): a batch that expires or fails keeps the results it has, and the rest go out again ([Generation](generation.md)).
- **News translations:** the job fails, so Cloud Tasks runs it again (up to 3 attempts), and library's daily schedule sends any post still missing a language again ([Admin zone](features/admin-zone.md#news)).

**What to do**

1. Check OpenAI's status page, then the account's usage limits and credit balance in OpenAI's dashboard.
2. Read the errors of `generation-worker`, `rounds` or `assistant` (command above). An authentication error means the key: add the right one to `openai-api-key` and restart the four services that read it:
   ```bash
   printf '%s' "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=-
   for service in generation generation-worker rounds assistant; do
     gcloud run services update $service --region=europe-west1 --update-labels=restarted=$(date +%s)
   done
   ```
3. If OpenAI is down, wait. The users see a "try again" message, not a broken page. The emergency pause would replace those with a clear 503, but it also stops candidate invites and new interviews, which don't need OpenAI: turn it on only if the failures cost money (**prepza AI spend high**) or a long outage is announced.
4. Once it's back, there's nothing to replay: failed generations wait for their owner's **Retry**. A template's generation has the same **Retry** on its page in the admin zone. There's no way to retry a company's generation for it.

**Resolved when** a test question in the help chat gets an answer, `generation-worker` logs no new OpenAI errors, and the alert closes.

## Resend down

**How you notice**

- **prepza events waiting:** an event waits unhandled for over 15 minutes, here on notifications' subscription ([monitoring_backlog.tf](../infra/terraform/monitoring_backlog.tf)).
- **prepza scheduled job failed:** the morning runs (digest, reminders) fail on an email they can't send; the bulk sender's runs (legal notices, campaigns) don't: a failed email is tried again in two later runs, then marked failed on its send ([bulk.py](../services/notifications/app/services/bulk.py)) ([member_sends.py](../services/notifications/app/services/member_sends.py)).
- **prepza server errors** may fire too: a failed email answers Pub/Sub with a 500.
- After several hours: **prepza events dead-lettered**.
- **prepza emails bouncing** (more bounces or spam marks than `email_bounce_alert_hourly` in an hour) and **prepza web hook signature refused** with `resend` in the log aren't outages: the first is about the addresses or the content (see the alert's text in [monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)), the second a wrong `resend-webhook-secret`.
- Users: candidate invites and reminders, team invites, shared reports and contact messages arrive late. Firebase's sign-in emails don't go through Resend and still arrive ([infra/README.md](../infra/README.md#email-deliverability)).

**What the system does by itself**

- **Event emails** (invites, reports, contact messages): a failed send answers Pub/Sub with an error, and Pub/Sub retries with backoff (10 seconds to 10 minutes), for 50 attempts, several hours, before dead-lettering the event ([events.py](../services/notifications/app/routers/events.py), [infra/README.md](../infra/README.md)). A wrong API key and Resend's own errors are retried the same way; only a `400` or `422` is final, and an invite refused that way shows as undelivered ([constants/email.py](../services/notifications/app/constants/email.py), [delivery.py](../services/notifications/app/services/delivery.py)).
- **No email twice:** each send carries an idempotency key (the event's id), and Resend sends the same key once within 24 hours ([resend.py](../services/notifications/app/integrations/resend.py)).
- **Over Resend's rate limit:** the event answers `429` and Pub/Sub retries; a morning run stops and the next minute's run goes on ([schedules.py](../services/notifications/app/routers/schedules.py)).
- **Morning emails:** a run that fails gives back the claim on the email it failed, so the next run, a minute later, sends it. A failed run isn't retried itself: the next one goes on, until the hour ends, and the catch-up hour three hours later sends what's left ([member_sends.py](../services/notifications/app/services/member_sends.py), [infra/README.md](../infra/README.md)).

**What to do**

1. Check Resend's status page and its dashboard (sending suspended, the domains still verified).
2. Read notifications' errors (command above, `service_name="notifications"`). A `401` or `403` means the key: add the right one and restart:
   ```bash
   printf '%s' "$RESEND_API_KEY" | gcloud secrets versions add resend-api-key --data-file=-
   gcloud run services update notifications --region=europe-west1 --update-labels=restarted=$(date +%s)
   ```
3. If Resend is down, wait: Pub/Sub keeps retrying for several hours. Nothing needs switching.
4. If **prepza events dead-lettered** fires, replay the dead-lettered events once Resend is back, with the loop in [infra/README.md](../infra/README.md#notes) ("Dead-lettered events"). A replay more than 24 hours after an email's first attempt isn't covered by Resend's idempotency key, so an email that went through but wasn't confirmed could arrive twice.
5. Morning emails that didn't go out within their hour go out in its catch-up hour, three hours later (digest 10:00, reminders 11:00 UTC; [jobs.tf](../infra/terraform/jobs.tf)); the bulk sender's runs go on every minute until 18:59 UTC, and what's left waits for the next day; the digest covers the same 24 hours ([digest.py](../services/notifications/app/services/digest.py)). If Resend is still down then, they wait for the next day.

**Resolved when** notifications' subscription has no backlog (**prepza events waiting** closes), `events-dead-letter` is empty, and a test invite to your own address arrives.

## A stuck generation

**How you notice**

- **prepza generation queue backed up:** over 50 tasks queued for 15 minutes ([monitoring_backlog.tf](../infra/terraform/monitoring_backlog.tf)).
- **prepza generations failing:** over 2 generations failed in an hour; the sweep's "stuck generations as failed" counts too ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)).
- **prepza generation tasks failing:** over 20% of task attempts failed for 30 minutes; Cloud Tasks drops a task after its last attempt ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)).
- Users: a generation's page keeps showing its progress and never ends, and a user reports it.

**What the system does by itself**

- **Delivery:** the `generation` queue tries a task up to 3 times (10 to 120 seconds apart), 20 at once at most ([jobs.tf](../infra/terraform/jobs.tf)). A job first moves its generation from queued to running in one step, so a repeated delivery does nothing ([jobs.py](../services/generation/app/services/jobs.py)).
- **Time limit:** a run stops after 25 minutes and is saved as failed ([generation.py](../services/generation/app/constants/generation.py)).
- **The sweep** (Cloud Scheduler job `sweep`, every 5 minutes) marks as failed, "Generation stopped unexpectedly. Please try again.", a generation running untouched for 35 minutes (its worker died) or queued for 2 hours (its task never came). The `generation.failed` event tells companies, and the user can **Retry**; a task that comes after all finds it no longer queued and does nothing ([schedules.py](../services/generation/app/services/schedules.py), [generations.py](../services/generation/app/storage/generations.py)).

**What to do**

1. Check the worker and the queue:
   ```bash
   gcloud run services describe generation-worker --region=europe-west1 --format='value(status.conditions)'
   gcloud tasks queues describe generation --location=europe-west1
   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="generation-worker" AND severity>=ERROR' --freshness=1h --limit=50
   ```
2. If the queue's state is `PAUSED`, resume it: `gcloud tasks queues resume generation --location=europe-west1`.
3. If the errors are OpenAI's, follow [OpenAI down](#openai-down); if Redis's, [Redis down](#redis-down); if the database's, the database alerts' text.
4. If the worker crashes or is stuck on a bad revision, move it to the previous revision in the Cloud Run console, or roll back the release ([infra/README.md](../infra/README.md#deploys), "Rolling back").
5. Let the sweep fail the stuck generations; to run it now rather than within 5 minutes:
   ```bash
   gcloud scheduler jobs run sweep --location=europe-west1
   ```
   It fails only generations past the limits above. Nothing marks one failed sooner, and an operator can't retry a company's generation: its owner clicks **Retry** (a template's: **Retry** on its page in the admin zone). Retry is refused while the emergency pause is on.

**Resolved when** the queue's depth falls, the alerts close, the worker logs `Marked N stuck generations as failed` for the ones the sweep caught, and a new generation finishes.

## A failed migration during a deploy

**How you notice**

- **prepza migration failed:** a Cloud Run job (a `<db>-migrate` job or `db-roles`) finished as failed ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)). The **Deploy** run also fails in GitHub Actions, at its **Migrations** step (or **Database users**).
- Users see nothing: the services step hasn't run, so every service still runs the previous version ([infra/README.md](../infra/README.md#deploys)).

**What the system does by itself**

- The deploy runs the 9 `<db>-migrate` jobs one at a time, in the order library, generation, rounds, companies, billing, notifications, ats, api, assistant, and stops at the first failure; it moves no service ([deploy.yml](../.github/workflows/deploy.yml)).
- A migrate job isn't retried (`max_retries = 0`, [services.tf](../infra/terraform/services.tf)).
- One service's migrations run in a single transaction, so the one that failed left its database as it was ([billing's env.py](../services/billing/migrations/env.py), the same in each service). The databases migrated before it keep their new schema; the old version keeps working on it, as migrations only add ([Deployment](deployment.md#migrations)).

**What to do**

1. In the failed run, see which `<db>-migrate` job failed, then read its logs:
   ```bash
   gcloud run jobs executions list --job=companies-migrate --region=europe-west1 --limit=3
   gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="companies-migrate"' --freshness=1h --limit=100
   ```
2. **A passing failure** (the database restarting, a connection refused): run the same version again, in **Actions → Deploy → Run workflow**, with the tag and **Run migrations** ticked. The migrations that already ran do nothing the second time.
3. **A wrong migration** (it fails on the data, say): fix it in a new commit and release a new tag ([infra/README.md](../infra/README.md#deploys)). Don't redeploy the failed tag.
4. **A migration that ran but did damage** (it deleted or changed data): turn maintenance mode on and restore that database from a point in time before the deploy, as in [infra/README.md](../infra/README.md#restore-drill).
5. If the migrations passed and the **Services** or **Smoke test** step failed, services may already run the new images: roll back as in [infra/README.md](../infra/README.md#deploys) ("Rolling back"), with **Run migrations** off.

**Resolved when** a Deploy run passes every step, the smoke test included, and the release shows on GitHub.

## Redis down

**How you notice:** **prepza Redis failing**, over 20 Redis errors in 10 minutes ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)). The uptime checks stay green: `/ready` checks only the database.

**What happens:** the emergency pause and maintenance mode count as off and can't be turned on ([pause.py](../packages/common/src/prepza_common/pause.py), [Admin zone](features/admin-zone.md#controls)); rate limits refuse or let the request through uncounted, by limit ([rate_limit.py](../packages/common/src/prepza_common/rate_limit.py)); live updates fail (the alert's text). Services retry a command whose connection dropped ([infra/README.md](../infra/README.md#bootstrap-once), step 4).

**What to do:** check Upstash's status and its plan's command limit, and the `redis-url` secret, as in [infra/README.md](../infra/README.md) (the Upstash paragraph at the top and bootstrap step 4). While Redis is down, each running service keeps the edited limits it last read (one started during the outage has every limit at its default) and the unpaid users' daily AI spend cap refuses nothing. A flushed or replaced Redis lifts the pause and maintenance mode, and starts the day's counts over (the shared budgets, the unpaid AI spend): turn the switches on again if they were on. Edited limits come back by themselves within 5 minutes, from billing's database (`billing-limits` job).

**Resolved when** the alert closes and the services log no new `redis.exceptions` errors.

## AI spend high or AI stopped

**How you notice**

- **prepza AI spend high:** all AI calls together cost over `ai_spend_alert_hourly` (default $20) in an hour, from the `prepza_ai_spend` metric: every call logs "AI used: action=… cost=$…" ([ai_usage.py](../packages/common/src/prepza_common/ai_usage.py), [monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)).
- **prepza AI stopped for many:** one of these lines was logged ([monitoring_logs.tf](../infra/terraform/monitoring_logs.tf)):
  - **"Unpaid AI spend near the daily cap"**: unpaid companies and people without a company spent 80% of today's cap (`AI_SPEND_UNPAID_DAY`, $15 by default);
  - **"Unpaid AI spend reached the daily cap"**: their AI features (generation, the assistant, the help chat) answer 503, "AI features are paused for today…", until midnight UTC; paid companies go on;
  - **"OpenAI quota exhausted"**: OpenAI refused a call with `insufficient_quota`, the account is out of money, and every AI call fails;
  - **"Shared limit used up: limit=NAME"**: a limit for everyone (such as `DAILY_GENERATION_LIMIT`, `TOKENS_PER_DAY`, `HELP_TOKENS_PER_DAY`) was reached, so that use stops for everyone it holds until its window ends.

**What the system does by itself:** nothing is paused. The cap and the shared limits refuse until midnight UTC (or their window's end) and then let calls through again; the counts start over each day.

**What to do**

1. Open **Admin zone → Stats → AI costs** for today's month: **By action**, **Companies that cost most** and **Users that cost most** show where the money went, and **Shared budgets today** how full each is. To read the log lines:
   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" AND (jsonPayload.message:"Unpaid AI spend" OR jsonPayload.message:"Shared limit used up" OR jsonPayload.message:"OpenAI quota exhausted")' --freshness=1h --limit=20
   ```
2. **Real use** (more sign-ups, a busy day): raise the limit in **Controls → Limits**: `AI_SPEND_UNPAID_DAY` at 80%, before anyone is refused, or the shared limit named in the log line. Lower it again later if you like; every change is kept with who made it.
3. **Abuse or a loop** (one company or user far ahead, the same action again and again): open its support page from the list. Suspend a company that abuses prepza ([Admin zone](features/admin-support.md)); lower the per-user or per-company limit it uses; for a runaway generation or job, see [A stuck generation](#a-stuck-generation). If the money keeps going, turn on the emergency pause.
4. **"OpenAI quota exhausted":** top up the OpenAI account (or raise its monthly limit) in OpenAI's dashboard at once. Nothing needs restarting: the next call goes through. Failed generations wait for their owners' **Retry**, as in [OpenAI down](#openai-down).

**Resolved when** the hourly spend is back under the alert level, the log lines stop, and the alerts close.
