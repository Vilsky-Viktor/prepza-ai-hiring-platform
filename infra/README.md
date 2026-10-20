# Google Cloud infrastructure

Terraform for prepza on Google Cloud, in one region (`europe-west1`, Belgium) behind Google's global load balancer:

- **Cloud Run:** the frontend, nine APIs (library, generation, rounds, companies, billing, notifications, ats, api, assistant) and the generation worker; notifications' bell stream runs as its own service (`notifications-stream`, same image) so open tabs never take the capacity event pushes need. That's 12 services from 10 images. Billed per request, and idle services cost nothing.
- **Cloud SQL Postgres 18** (as locally): one database per service, with daily backups (14 kept) and point-in-time recovery (7 days back). Google Cloud refuses to delete the instance (deletion protection on the instance itself, not only in Terraform), its backups outlive it, and Google's maintenance restarts it only on Sundays at 03:00 UTC.
- **Pub/Sub:** domain events. One `events` topic is pushed to library, companies (also `audit.recorded`, members' actions from billing, ats, notifications and api for the company's action log), notifications, ats, api, assistant and billing (every AI call and limit hit, `ai.used` and `limit.hit`, for the admin zone's AI costs page), each getting only the event types it handles (`locals.consumes` in `pubsub.tf`; add a type there when a consumer starts handling it; a filter is capped at 256 bytes, and changing one replaces that subscription, dropping the messages it still holds, so apply when its backlog is empty; a new consumer's subscription gets only the events published after it's created), with a dead-letter topic after 50 attempts (retries back off from 10 seconds to 10 minutes, so several hours of trouble).
- **Cloud Tasks:** generation jobs on the worker, each tried up to 3 times. **Cloud Scheduler** (`jobs.tf`): outbox flushes (library, companies, rounds, the generation worker, ats, billing, notifications and api; billing's, notifications' and api's carry their members' actions to companies' action log) and expired interviews every minute, generation sweeps, web hook retries and billing's limits sync (the limits edited in the admin zone written to Redis again, so a wipe heals itself) every 5 minutes, key-check batches and ATS recovery every 10 minutes, daily retention (generations; candidates and the company action log, 12 months; the assistant's idle conversations, AI apps' expired connections and apps idle for 30 days; AI usage and limit hits past 13 months, limit changes past 24), invite expiry and reminders, library's housekeeping (`bank-stages`: flags and news posts sent again, old event notes forgotten), every minute for an hour each morning the activity digest (7:00 UTC) and member reminders (8:00), each again for a catch-up hour three hours later (10:00, 11:00), every Monday at 05:00 UTC generation's question quality patterns (`quality-patterns`: last week's flagged and replaced questions turned into proposed general rules for the admin zone; **created paused**, since it reads every company's flagged questions and may run on real data only once the terms and privacy version that allows it, 2026-11-08, is in force: resume it by taking it out of `paused_schedules` in `jobs.tf`), and every minute from 8:00 to 18:59 UTC the bulk sender (`bulk-emails`: legal notices and campaigns, within 80% of Resend's daily quota, `RESEND_DAILY_LIMIT`, an editable limit in the admin zone's Controls); a failed daily job is retried 3 times (the email runs aren't: the next run goes on, and the catch-up hour sends what the first hour missed).
- **The global load balancer:**
  - HTTPS with a Google-managed certificate;
  - `/api/<service>/` routes to each API, the MCP endpoint and its OAuth paths at the root (`/mcp`, `/authorize`, `/token`, `/register`, `/revoke` and the `/.well-known/oauth-*` metadata; exact paths, `locals.mcp_paths`) to the assistant, and everything else to the frontend;
  - Cloud CDN for static files;
  - the security headers the local nginx gateway adds (HSTS, nosniff, `X-Frame-Options` on the APIs, `Referrer-Policy`, `Permissions-Policy`); the frontend sets its own Content-Security-Policy, whose `frame-ancestors` lets no site frame a page but a company's own its embedded interview;
  - a Cloud Armor rule that blocks `/api/*/internal/`.
- **Secret Manager** for secrets, and **Artifact Registry** for images: released versions' images (`v*` tags) and each image's 10 newest are kept, and the rest are deleted after 30 days.

Outside Google Cloud: Redis on **Upstash** (rate limits and the current value of each limit edited in the admin zone, which billing writes back within 5 minutes after a flush, the unpaid users' daily AI spend, the LLM limiter, the draft cache, live notifications, and the emergency pause, maintenance mode and the daily generation cap: a flushed or replaced database lifts them, so turn them on again after one), **Firebase Authentication** (same project), **Resend**, **Sentry** and **Paddle**.

## Bootstrap (once)

You need `gcloud`, Docker and Terraform 1.9+ (or `docker run hashicorp/terraform`).

1. **Create the project and link billing.**
   ```bash
   gcloud projects create prepza-prod
   gcloud billing projects link prepza-prod --billing-account=<BILLING_ACCOUNT_ID>
   gcloud config set project prepza-prod
   gcloud auth application-default login
   # The budget API needs a project to bill your own login's calls to.
   gcloud auth application-default set-quota-project prepza-prod
   ```
2. **Add Firebase to the project** in the [Firebase console](https://console.firebase.google.com) ("Add project", then choose `prepza-prod`).
   - **Authentication → Sign-in method:** enable Google.
   - **Authentication → Settings → Authorized domains:** add `prepza.ai`.
   - **Authentication → Settings → User account linking:** keep "Link accounts that use the same email" (the default): the site links GitHub or LinkedIn to an existing account with the same email after the person signs in the way they did before.
   - **GitHub and LinkedIn sign-in (optional):**
     - GitHub: create an OAuth app (GitHub → Settings → Developer settings → OAuth Apps) with the callback URL `https://<authDomain>/__/auth/handler`. Set `github_client_id` and `github_client_secret` in `terraform.tfvars`.
     - LinkedIn: first upgrade the project to Identity Platform (Firebase console → Authentication → Settings; OpenID Connect providers are free for 50 monthly users, then about $0.015 each). Create a LinkedIn app with the product "Sign In with LinkedIn using OpenID Connect" and the same callback URL. Set `linkedin_client_id` and `linkedin_client_secret`.
     - Terraform (`auth.tf`) creates each provider once its client id is set.
   - **Project settings → Your apps:** add a Web app. Note its `apiKey` and `authDomain` for the frontend build; the `apiKey` is also `firebase_web_api_key` in `terraform.tfvars` (the assistant signs AI apps' users in with it, so the plan and the assistant refuse an empty one). In Google Cloud's Credentials, restrict that key to its APIs (Identity Toolkit API and Token Service API) if you restrict it at all, never to websites (HTTP referrers): the assistant calls from the server, with no referrer, and every AI app call would fail.
3. **Create the bucket for Terraform's state.**
   ```bash
   gcloud storage buckets create gs://prepza-prod-terraform --location=europe-west1 --uniform-bucket-level-access
   gcloud storage buckets update gs://prepza-prod-terraform --versioning
   ```
4. **Create Redis on Upstash.** Pick the Google Cloud region `europe-west1` and a paid plan (pay as you go, or a fixed plan once traffic grows): every request reads the pause and its rate limits, so the free plan's monthly command limit runs out in days, and Redis then refuses every command until the month ends. Copy its `rediss://` URL. Services retry a command whose connection dropped, and the Redis alert (below) fires when commands keep failing.
5. **Set your variables.**
   ```bash
   cd infra/terraform
   cp terraform.tfvars.example terraform.tfvars   # fill it in
   terraform init -backend-config="bucket=prepza-prod-terraform"
   ```
   For the live site, set `paddle_environment = "production"` with the production `paddle_prices` (each top-up price's tax set to **Exclusive**, see [docs/features/billing.md](../docs/features/billing.md#setting-up-paddle)) and `paddle_client_token` (sandbox ones take no real payments), and at least one `superadmin_emails`: the emergency pause and maintenance mode are switched only from the admin zone, so Terraform refuses an empty list.

   `alert_email` (and optionally `alert_sms`, a phone number that gets every alert by text message too), `billing_account` and `monthly_budget` set up the alerts in `monitoring*.tf`: an uptime check every minute on the site and each API's `/ready` (which checks the database only, so a Redis outage doesn't fail it), an email when one fails, an email when an event is dead-lettered, waits unhandled for over 15 minutes, or a scheduled job fails, when over 50 generation jobs stay queued for 15 minutes, when a service answers more than 5% of requests with server errors, when Paddle's or Resend's web hook is refused for its signature (a wrong secret, which the server-error alert doesn't see), when the database nears its connection limit, stays busy, runs short of memory (90%) or disk (85%), or a backup fails, when candidates' answers are slow (the interview service's p95 above 2 seconds for 10 minutes), when the analytics funnel's events wait over 15 minutes, when Redis (over 20 errors in 10 minutes) or OpenAI (over 10 in 15 minutes) fails, when all AI calls together cost over `ai_spend_alert_hourly` (default $20) in an hour (the `prepza_ai_spend` metric, from each call's "AI used" log line, by action), when AI stops for many (a limit for everyone used up, OpenAI's account out of money, or unpaid users' AI spend at 80% of its daily cap or reaching it; the `prepza_ai_stopped` metric), every refusal by a limit also counted, by limit, in `prepza_limit_hits`, when more than 2 generations fail in an hour (or are swept as stuck), when more than 3 calls to Paddle fail in 15 minutes (no answer or a 5xx, not a declined card), when a migration or `db-roles` job fails, when over 20% of generation task attempts fail for 30 minutes (Cloud Tasks drops a task after its last), when more emails than `email_bounce_alert_hourly` (default 20) bounce or are marked as spam in an hour (`monitoring_logs.tf`, counted from the services' logs), and budget emails at 50%, 90% and 100% of the month (and when the forecast passes it). What to do when one fires: [docs/runbooks.md](../docs/runbooks.md). Creating the budget needs the Billing Account Costs Manager role on the billing account, which its administrator already has. `monthly_budget` is the Google Cloud bill's budget only; the AI budget the admin zone's AI costs page compares the month's AI spend with is `MONTHLY_BUDGET` in the admin zone's Controls. Usage limits, such as the daily generations of companies that never topped up, aren't Terraform variables: a superadmin sets them in the admin zone's Controls tab ([docs/features/admin-zone.md](../docs/features/admin-zone.md#limits)). `google_site_verification` and `bing_site_verification` (optional) are the tokens from Google Search Console's and Bing Webmaster Tools' meta-tag checks; the frontend adds the tags.
6. **Create the image registry first,** then push the first images. CI pushes them on every push to `main` afterwards.
   - Cloud Run runs `linux/amd64`, so build for it even on an Apple-silicon Mac.
   - Use the same tag as `image_tag` in `terraform.tfvars`.

   ```bash
   terraform apply -target=google_artifact_registry_repository.images
   gcloud auth configure-docker europe-west1-docker.pkg.dev
   REGISTRY=europe-west1-docker.pkg.dev/prepza-prod/prepza
   for service in library generation rounds companies billing notifications ats api assistant; do
     docker build --platform linux/amd64 --target prod -f services/$service/Dockerfile -t $REGISTRY/$service:first . && docker push $REGISTRY/$service:first
   done
   docker build --platform linux/amd64 --target prod -t $REGISTRY/frontend:first \
     --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=<apiKey> \
     --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=prepza-prod.firebaseapp.com \
     --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=prepza-prod frontend && docker push $REGISTRY/frontend:first
   ```

   Run these from the repo root.
7. **Create everything else.**
   ```bash
   terraform apply
   ```
8. **Set the secrets.** They start as `set-me`, and Terraform never overwrites them.
   ```bash
   printf '%s' "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=-
   printf '%s' "rediss://...upstash.io:6379" | gcloud secrets versions add redis-url --data-file=-
   printf '%s' "$RESEND_API_KEY" | gcloud secrets versions add resend-api-key --data-file=-
   printf '%s' "$RESEND_WEBHOOK_SECRET" | gcloud secrets versions add resend-webhook-secret --data-file=-
   # Resend's daily quota isn't a secret: set it in the admin zone's Controls (RESEND_DAILY_LIMIT, default 100,
   # Resend's free plan) to your plan's, as bulk emails stop at 80% of it (RESEND_RESERVE_PERCENT keeps 20% back).
   printf '%s' "$PADDLE_WEBHOOK_SECRET" | gcloud secrets versions add paddle-webhook-secret --data-file=-
   # Its permissions: transactions read and write, subscriptions read and update (docs/features/billing.md).
   printf '%s' "$PADDLE_API_KEY" | gcloud secrets versions add paddle-api-key --data-file=-
   # The ats service's key that encrypts companies' ATS keys (a Fernet key); keep it: a new one makes them reconnect.
   python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode(), end='')" | gcloud secrets versions add ats-encryption-key --data-file=-
   # The api service's key that encrypts web hooks' signing secrets (a Fernet key); keep it: a new one makes companies add their web hooks again.
   python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode(), end='')" | gcloud secrets versions add api-encryption-key --data-file=-
   # Slack: prepza's Slack app (see docs/features/notifications.md#setting-up-slack), and the key that encrypts companies' web hooks; keep it too.
   printf '%s' "$SLACK_CLIENT_ID" | gcloud secrets versions add slack-client-id --data-file=-
   printf '%s' "$SLACK_CLIENT_SECRET" | gcloud secrets versions add slack-client-secret --data-file=-
   python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode(), end='')" | gcloud secrets versions add slack-encryption-key --data-file=-
   # Cloudflare Turnstile, the "I'm not a robot" check (docs/architecture.md): the widget's secret.
   # Set it once the privacy policy and DPA naming Cloudflare apply (2026-10-29); with
   # Terraform's "set-me" Cloudflare rejects it, and the check lets everyone through (logged). Its site key is the GitHub variable
   # NEXT_PUBLIC_TURNSTILE_SITE_KEY, built into the frontend.
   printf '%s' "$TURNSTILE_SECRET_KEY" | gcloud secrets versions add turnstile-secret-key --data-file=-
   ```

   Terraform makes the generated ones itself: each service's secret for internal calls (a service gets the keys of the services it calls, `locals.calls` in `locals.tf`; the assistant's include notifications', ats' and library's, whose internal routes its `get_updates` tool reads, so it needs an `apply` before a deploy that adds such a call), the database passwords, `analytics-salt`, `preview-secret` (signs the frontend's link-preview titles) and `email-link-secret` (signs the unsubscribe links in emails; replacing it breaks the links in emails already sent).

   Services read `latest` when they start, so redeploy (step 9) after setting secrets.

   **Replacing an encryption key** (`ats-encryption-key`, `api-encryption-key`, `slack-encryption-key`, after a leak, say): set the secret to the new key and the old one, comma-separated, new first, and redeploy. New secrets are sealed with the new key, and both read what's stored. Keep the old key in the list: what it sealed stays sealed with it until it's saved again (a reconnected ATS or Slack channel, a new web hook). Removing it makes those unreadable, as a new key alone would.
9. **Run the migrations, then restart the services** so they pick up the secrets. Each migration only adds (the latest: the assistant's `update_checks` table, 0007, and the columns `get_updates` reads: companies' `candidate_invites.undelivered_at`, 0049; ats' `ats_candidates.failed_at`, 0012; library's `question_stats.flag_raised_at` and `question_revisions.fixed`, 0030), so the code running before them keeps working.
   ```bash
   for db in library generation rounds companies billing notifications ats api assistant; do
     gcloud run jobs execute $db-migrate --region=europe-west1 --wait
   done
   # A new revision of each service reads the secrets you just set.
   for service in frontend library generation rounds companies billing notifications notifications-stream ats api assistant generation-worker; do
     gcloud run services update $service --region=europe-west1 --update-labels=restarted=$(date +%s)
   done
   ```
10. **Point the domain at the load balancer.** In GoDaddy's DNS, add an **A record** for `@` with the value of `terraform output site_ip`, and keep GoDaddy's **CNAME** `www` → `@` (add it if it's missing): `www.prepza.ai` redirects to `prepza.ai`. Google then issues both certificates, which can take up to about an hour; each is independent, so the site works even while `www`'s is pending:
    ```bash
    gcloud compute ssl-certificates list --global --format='table(name,managed.status)'
    ```
    Until the certificate is active, the uptime checks fail and their alerts email you; they clear by themselves once the site answers.
11. **Update the services that call back to the site:**
    - **Paddle:** the webhook destination is `https://prepza.ai/api/billing/webhooks/paddle`, for `transaction.completed`, `adjustment.created`, `adjustment.updated`, `subscription.created` and `subscription.canceled`. The adjustments are refunds and chargebacks, which take the credits back; the subscriptions start and end automatic top-ups. Once deployed, send Paddle's test notification to it: it must be accepted (a refused signature means `paddle-webhook-secret` is wrong, and the alert below fires).
    - **Resend:** the `prepza.ai` sending domain is already verified; verify `mail.prepza.ai` too, the optional emails' sender (see [Email deliverability](#email-deliverability)). Add a webhook at `https://prepza.ai/api/notifications/webhooks/resend` for `email.bounced`, `email.complained` and `email.suppressed`; its signing secret is `resend-webhook-secret` in step 8. Once deployed, send a test event from Resend and check it's accepted.
    - **Sentry:** create the organization in Sentry's EU data region (the privacy policy and DPA say error reports stay in the EU), then set `backend_sentry_dsn` in `terraform.tfvars`.

12. **Connect GitHub for deploys.** In the repository's **Settings → Secrets and variables → Actions → Variables**, add:
    - **From Terraform:** everything in `terraform output github_variables`, which gives `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `GCP_CI_SERVICE_ACCOUNT` and `SITE_URL`. Two accounts: CI's image job uses one that can only push images; only the deploy workflow running in the `production` environment (which needs your approval) can use the deploy account, which moves services to new images and runs migrations.
    - **From Firebase:** `NEXT_PUBLIC_FIREBASE_API_KEY` and `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, from the web app in step 2.
    - **Optionally:** `FRONTEND_SENTRY_DSN` for the frontend, and `SENTRY_ORG` and `SENTRY_PROJECT` with, under **Secrets**, `SENTRY_AUTH_TOKEN` (a Sentry auth token that can upload source maps), so frontend stack traces show the original code.

    Apart from `SENTRY_AUTH_TOKEN`, these are variables, not secrets: none of them grants access. GitHub's signed token is what lets the pipeline in, and only for `main` and the `v*` tags of this repository.
13. **Protect the version tags.** A tag deploys, so only you should be able to make one. In **Settings → Rules → Rulesets**, add a **tag ruleset**:
    - **Target tags:** include by pattern `v*`.
    - **Rules:** restrict creations, restrict updates and restrict deletions.
    - **Bypass list:** Repository admin, so you can still create them.
14. **Optionally, require an approval for deploys.** Deploys run in the `production` environment, which GitHub creates on the first deploy. In **Settings → Environments → production**, add yourself under **Required reviewers**; each deploy then waits for your click. Rulesets and required reviewers on a private repository need a paid GitHub plan.
15. **Announce the 2026-11-08 legal version.** The terms, privacy policy and DPA of 2026-11-08 (the licence to reuse generated questions, the question quality patterns, Langfuse as a sub-processor, local-currency prices) need a notice at least 14 days ahead: in the admin zone's Controls, ask for the terms, privacy and DPA notices by 2026-10-25 (see [docs/features/admin-zone.md](../docs/features/admin-zone.md#legal-notices)). From 2026-11-08, add the Langfuse settings (see [Notes](#notes)) and resume `quality-patterns` (see Cloud Scheduler above).

## Email deliverability

Emails go out through Resend in two streams, each from its own domain, so spam complaints about the optional ones can't hurt the reputation of the service ones:

| Stream | Emails | Sender (`terraform.tfvars`) |
| --- | --- | --- |
| Service | candidate invites and reminders, team invites, shared reports, failed automatic top-ups, contact messages | `mail_from = "prepza. <no-reply@prepza.ai>"` |
| Optional | the activity digest and reminders (later product updates and offers) | `mail_from_updates = "prepza. <updates@mail.prepza.ai>"` |

The DNS records below are what Gmail, Yahoo (their 2024 rules for bulk senders) and Outlook check. Add them in GoDaddy's DNS, where a record's name is relative to `prepza.ai` (`send` means `send.prepza.ai`):

1. **Add both domains in Resend, in the EU region.** At resend.com/domains, add `prepza.ai` and `mail.prepza.ai` with the region **Ireland (eu-west-1)**: a domain's region is set when it's added (to change it, delete the domain and add it again). Each domain's page lists its exact records: copy the values from there, as the DKIM key is unique to each domain.
2. **Sending (SPF and the bounce address).** Two CNAME records per domain point the `send` and `rsend` subdomains at Resend, which publishes the SPF record and receives the bounces there, not on `prepza.ai` itself:

   | Type | Name | Value |
   | --- | --- | --- |
   | CNAME | `send` | `send.forge.rmta.net` |
   | CNAME | `rsend` | `rsend-euw1.forge.rmta.net` (the EU region's host) |
   | CNAME | `send.mail` | `send.forge.rmta.net` |
   | CNAME | `rsend.mail` | `rsend-euw1.forge.rmta.net` |

   A name has at most one SPF record. Whatever receives mail for `@prepza.ai` (the mailbox behind `hello@prepza.ai`) adds its own MX and SPF records on `@`, as its provider says.
3. **DKIM.** One TXT record per domain, with the key from Resend's page:

   | Type | Name | Value |
   | --- | --- | --- |
   | TXT | `resend._domainkey` | `p=MIGfMA0GCSqGSIb3DQEB…` (prepza.ai's key) |
   | TXT | `resend._domainkey.mail` | `p=MIGfMA0GCSqGSIb3DQEB…` (mail.prepza.ai's key) |

   Click **Verify** on each domain's page once the records are in; both should show "Verified".
4. **DMARC.** One record on `prepza.ai` covers `mail.prepza.ai` too. Start by only collecting reports, sent to an address you read:

   | Type | Name | Value |
   | --- | --- | --- |
   | TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@prepza.ai; adkim=r; aspf=r` |

   After 2–4 weeks of reports showing every legitimate sender passing (Resend, and the mailbox provider of `hello@prepza.ai`), move to `p=quarantine`, and later to `p=reject`.
5. **Firebase's own emails.** Firebase sends the link that verifies a new user's email (after a GitHub sign-in, say) itself, by default from `noreply@prepza-prod.firebaseapp.com`, which none of the records above cover. In the Firebase console → **Authentication → Templates**, edit **Email address verification**, set the sender name to `prepza.`, and click **Customize domain**: enter `auth.prepza.ai` and add the TXT and CNAME records it lists (its own SPF and DKIM, on a subdomain so `@`'s SPF stays as it is). Once verified, the emails come from `noreply@auth.prepza.ai` and pass DMARC. When Firebase can't send one, the sign-in says so and the next sign-in sends a new link.
6. **Turn tracking off.** On each domain's page in Resend, under **Configuration**, keep **Click tracking** and **Open tracking** off: click tracking rewrites links into redirects through another domain, and the open pixel is an image from elsewhere; both look like spam. Emails link only to `prepza.ai`.
7. **Check it.** Send an invite, a digest and a Firebase verification email to the address mail-tester.com gives you and aim for 10/10; in Gmail, **Show original** should say `PASS` for SPF, DKIM and DMARC. Add `prepza.ai` to [Google Postmaster Tools](https://postmaster.google.com) (verified with one more TXT record) and keep the spam rate under 0.1%, never reaching 0.3%; Outlook's [SNDS](https://sendersupport.olc.protection.outlook.com/snds/) shows the same for Microsoft.

What the emails do themselves: each has a plain-text part next to the HTML, `Auto-Submitted: auto-generated`, and a Reply-To that someone reads (the member who shared a report, the visitor for contact messages, otherwise `CONTACT_EMAIL`). Only emails the recipient may stop (the digest, reminders, a candidate's reminder) carry the one-click `List-Unsubscribe` headers; a spam complaint about the digest or reminders turns them off for that user (see [Notifications and emails](../docs/features/notifications.md#unsubscribing)).

## Deploys

- **Pull requests:** CI runs on every push, and a new push cancels the previous run. It tests and builds only what changed: ruff always; Terraform's format and validation when `infra/terraform` changed; a changed service's unit tests and image; a changed frontend's lint, types, translations check, unit tests and image; and the smoke, integration and page tests on the whole stack when any part, the stack or its tests changed (see [Testing](../docs/testing.md#ci)).
- **Merging to `main`:** the same CI runs again on the merged code, compared with the last commit it passed on, and pushes the 10 production images for `linux/amd64`, tagged with the commit: the changed ones are built, the others are that commit's images with the new tag added. Nothing is deployed.
- **Releasing:** tag a commit on `main` that CI passed on, the last commit of a push, and push the tag. CI on `main` runs one push at a time with one more waiting, so after quick merges a waiting run is replaced by the next push's, which builds both: the replaced commit gets no images and can't be released. Tag the latest commit with a green CI run (`gh run list -w ci.yml -b main -s success -L 1`):
  ```bash
  git tag v1.4.0 && git push origin v1.4.0
  ```
  [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) then checks that the tag is on `main` and CI passed on it, gives that commit's images the version as a tag (nothing is rebuilt), runs the `db-roles` job and then the 9 migration jobs, moves all 12 services to the images, smoke-tests the site and creates a GitHub release with the changes since the last tag.

A failed step stops the deploy. Before the services step, nothing has changed for users. From the services step on, some or all services already run the new images, and nothing rolls back by itself: if the smoke test fails, roll back as below (the failed run says so). The smoke test checks the site, every API's `/ready` and the MCP paths.

- **Rolling back:** in **Actions → Deploy → Run workflow**, enter an earlier version, for example `v1.3.2`, and leave **Run migrations** off. It redeploys that version's images in about a minute, on the newer schema (an older version's migrations would fail on it). So this is safe only while the newer migrations didn't remove anything the older code needs: keep migrations additive. Tick **Run migrations** only to redeploy a version whose migrations haven't run. For one service, you can also move it to an earlier revision in the Cloud Run console.
- **Terraform never touches image tags,** so applying an infrastructure change doesn't roll anything back.
- **Pinned dependencies:** workflow actions are pinned by commit, the Dockerfiles' base images, the `uv` image and the local stack's images by digest, and packages by their lock files; [`.github/dependabot.yml`](../.github/dependabot.yml) opens weekly pull requests that update them (minor and patch versions only), and the dependency audit workflow fails on a known high-severity vulnerability. Merge one once CI passes.

## Restore drill

A backup is only proven by restoring it. Run `scripts/ops/restore-drill.sh prepza-prod` before launch, and then every quarter. It needs `gcloud`, `cloud-sql-proxy` and `psql`, and it:
1. Restores the latest backup into a temporary instance.
2. Reads each service's main tables through the Cloud SQL Auth Proxy.
3. Deletes the temporary instance, even if a step fails.

It costs a few cents: the temporary instance runs for about 15 minutes.

For an actual recovery, Cloud SQL can also restore to any second of the last 7 days (point-in-time recovery), for example to just before a bad deploy:

```bash
gcloud sql instances clone prepza prepza-recovered --point-in-time="2026-10-02T12:00:00Z"
```

The services stay on the main instance (each mounts only its socket), so the clone is a source to copy from. To restore one service's database, say `companies`, without touching the other eight:

1. Turn maintenance mode on in the admin zone, so nothing writes meanwhile.
2. Dump the database from the clone and restore it over the main one, through the Cloud SQL Auth Proxy, as the admin (`database-admin-url`):
   ```bash
   cloud-sql-proxy --port 6544 prepza-prod:europe-west1:prepza-recovered &
   cloud-sql-proxy --port 6543 prepza-prod:europe-west1:prepza &
   pg_dump -h 127.0.0.1 -p 6544 -U prepza -Fc companies > companies.dump
   pg_restore -h 127.0.0.1 -p 6543 -U prepza -d companies --clean --if-exists --no-owner \
     --role=companies companies.dump
   ```
3. Turn maintenance mode off, then delete the clone (`gcloud sql instances delete prepza-recovered`).

To restore everything, restore the instance from a backup instead (`gcloud sql backups restore`), which overwrites all nine databases.

**Recovery targets.** At most a few seconds of data is lost (point-in-time recovery, 7 days back), and a restore takes about an hour (cloning or restoring takes 15–30 minutes, plus the copy). The instance is zonal (`db_high_availability` off): if its zone fails, Cloud SQL brings it back in another zone of the region with its data, after some downtime; `db_high_availability = true` makes that failover automatic, at twice the database cost. If the whole region fails, prepza is down until it returns: restoring elsewhere would mean recreating the infrastructure in another region from a backup (backups are kept in a multi-region location by default), which isn't scripted.

## Notes

- **Service addresses:** services reach each other at their Cloud Run addresses, which are known in advance (`https://<service>-<project number>.europe-west1.run.app`).
- **Who can call what:**
  - Public services take outside traffic only through the load balancer (ingress "internal and Cloud Load Balancing"), so Cloud Armor's rules always apply; their `run.app` addresses refuse the internet. The generation worker takes only Google's calls.
  - Calls between services go out through the private network in `network.tf` (Direct VPC egress, all traffic), so they arrive as internal; the internet (OpenAI, Resend, Paddle, Upstash) is reached through its Cloud NAT, about $1–5 a month at this size. The NAT gives each instance ports as it needs them (64 to 4096), so an instance isn't capped at about 64 connections to one address.
  - Calls between services also carry signed service tokens.
  - Pub/Sub, Cloud Tasks and Scheduler sign as the `prepza-invoker` account, which the services check.
- **Database users:** each service connects as its own Postgres user (named after its database) that owns only that database; other users can't even connect to it. The `prepza` user is the instance's admin and is used only by the `db-roles` job (`db_roles.tf`, `services/library/app/jobs/db_roles.py`), which creates those users and moves ownership to them. The deploy pipeline runs it before migrations; it's safe to repeat. **When first applying this over an existing database,** run it right after `terraform apply`, before any service restarts: `gcloud run jobs execute db-roles --region=europe-west1 --wait`. Until it has run, new instances can't connect, since their URLs already name the new users. Locally, Docker Compose keeps the one `prepza` user.
- **Least privilege:** each service runs as its own account (`prepza-<service>`, see `iam.tf`) that can read only its own secrets and its own database's URL. The frontend has no permissions; only the backend services publish events, and only the generation services queue tasks. The assistant also reads Firebase accounts (`roles/firebaseauth.viewer`) and signs as itself (the custom role `prepzaTokenSigner`, only `iam.serviceAccounts.signBlob`, on its own account, through the `iamcredentials` API), to sign the users of AI apps connected over MCP in with a custom token ([AI apps over MCP](../docs/features/mcp.md#calling-the-services-as-the-user)). Companies signs as itself too (the same role on its own account), to sign in the guest candidate a company's platform sends through the API without a sign-in ([API](../docs/features/api.md)). Migrations run as their service's account.
- **App settings:** Terraform passes the assistant's `SITE_URL` and `FIREBASE_WEB_API_KEY` (from `domain` and `firebase_web_api_key`), but none of the other settings in `.env.example`: the AI models and reasoning efforts (`INTERVIEW_MODEL`, `VERIFY_MODEL`, `HELP_MODEL` and their `*_REASONING_EFFORT`). The services run on their code defaults, which match `.env.example`. Tracing to Langfuse (every AI call of generation, the assistant and rounds, and the votes on the chats' answers) is local only: it stays out of Terraform until the privacy policy and DPA version that lists Langfuse as a sub-processor, 2026-11-08, is in force. It will then need `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` as Secret Manager secrets and `LANGFUSE_HOST` (`https://cloud.langfuse.com`, the EU cloud) on generation (API and worker), assistant and rounds. Usage limits and the values tuned with them (the seconds a question by level, generation's AI calls at once and a second, the multi-answer share, the questions generated per topic, the topics and subtopics a test has, the share of Resend's quota kept from bulk sends, the monthly AI budget) aren't settings: each starts at its default in `prepza_common.limit_list` and is changed in the admin zone's Controls. To change one in production, add it to the service's entry in `env.tf`.
- **Dead-lettered events:** an event a consumer failed on 50 times waits 7 days in the `events-dead-letter` subscription, and an alert emails you while any wait there. After fixing the consumer, replay them to the `events` topic with their attributes (the type), which acknowledges each one republished:

  ```bash
  # One at a time, so each is acknowledged well within the subscription's 10-second deadline.
  while m=$(gcloud pubsub subscriptions pull events-dead-letter --limit=1 --format=json | jq -c '.[0] // empty') && [ -n "$m" ]; do
    attrs=$(jq -r '.message.attributes | with_entries(select(.key | startswith("CloudPubSubDeadLetter") | not)) | to_entries | map("\(.key)=\(.value)") | join(",")' <<<"$m")
    gcloud pubsub topics publish events --message="$(jq -r .message.data <<<"$m" | base64 -d)" --attribute="$attrs" &&
      gcloud pubsub subscriptions ack events-dead-letter --ack-ids="$(jq -r .ackId <<<"$m")"
  done
  ```

  The replay goes to every consumer subscribed to that type, not only the one that failed. `candidate.finished` and `company.deleted` reach notifications, ats and api, and `candidate.removed` reaches notifications and ats, so a replay of those also reaches the consumers that already handled them; each consumer handles a redelivered event safely, so that changes nothing twice (see [Architecture](../docs/architecture.md#events)).
- **Generation jobs:** a job may run up to 25 minutes, under Cloud Tasks' 30-minute limit. The queue tries a task up to 3 times (`jobs.tf`), for a delivery that fails before the job starts, such as a worker restarting; a job first moves its generation from queued to running in one atomic step, so a repeated delivery does nothing. A generation that fails once running is retried by the user.
- **Database connections:** Cloud SQL starts at `db-g1-small` with 200 connections allowed, 20 kept free. Each API process holds up to 10 connections (generation and the worker 14, notifications, ats, api and the assistant 4); the services' `max` instances fit within the rest, and the plan fails if they don't (`database.tf`): today at most 140 of the 180. A deploy moves the services one at a time and runs each one's old instances until their requests end, so the plan also fails if a deploy at the instance limits could pass the 200: the peak, plus the old worker and bell-stream instances (their requests outlast the deploy), plus the largest other service; today 196, only 4 under the 200, so a new service or a higher `max` needs a bigger tier or PgBouncer first. The APIs with a pool of 10 take 40 requests at once per instance, so a busy one scales out rather than queueing on its pool; the worker takes 10 jobs on each of its 2 instances, the queue's 20 at once. Raise `db_tier` (and `db_max_connections`), or add PgBouncer, before allowing more instances or once services often run near their `max`.
- **High availability:** `db_high_availability = true` adds a standby in another zone, at about double the database cost.
- **Not yet tried on a real project:** `terraform validate` passes, but some settings may need a small adjustment on the first `apply`. The ones most likely to need it are the load balancer's backend protocol for Cloud Run, and Cloud Armor on the CDN backend.
