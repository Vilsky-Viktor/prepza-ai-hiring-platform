# Generation jobs: one task runs one generation on the worker. A delivery that fails before the
# job starts (a worker restarting) is tried again; a started generation is claimed once, so a
# repeated delivery does nothing (services/generation/app/services/jobs.py).
resource "google_cloud_tasks_queue" "generation" {
  name     = "generation"
  location = var.region

  rate_limits {
    # The worker's one instance takes 10 jobs at once (locals.tf).
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 5
  }

  retry_config {
    max_attempts  = 3
    min_backoff   = "10s"
    max_backoff   = "120s"
    max_doublings = 3
  }

  depends_on = [google_project_service.apis]
}

# Periodic work, as scripts/local/crontab does locally (UTC).
locals {
  schedules = {
    sweep                = { service = "generation-worker", path = "/internal/schedules/sweep", cron = "*/5 * * * *" }
    key-check-batches    = { service = "generation-worker", path = "/internal/schedules/key-check-batches", cron = "*/10 * * * *" }
    generation-retention = { service = "generation-worker", path = "/internal/schedules/retention", cron = "0 3 * * *" }
    # Weekly, Monday morning: last week's flagged and replaced questions turned into proposed
    # general rules for the admin zone's patterns tab. Created paused (paused_schedules).
    quality-patterns    = { service = "generation-worker", path = "/internal/schedules/patterns", cron = "0 5 * * 1" }
    candidate-retention = { service = "companies", path = "/internal/schedules/retention", cron = "15 3 * * *" }
    invite-expiry       = { service = "companies", path = "/internal/schedules/invite-expiry", cron = "30 3 * * *" }
    # Candidates erased in the last 14 days, erased again if a restore brought them back.
    candidate-removals = { service = "companies", path = "/internal/schedules/removals", cron = "15 5 * * *" }
    # In the morning (UTC), not the night: a reminder candidates see.
    invite-reminders = { service = "companies", path = "/internal/schedules/invite-reminders", cron = "0 9 * * *" }
    bank-stages      = { service = "library", path = "/internal/schedules/bank", cron = "45 3 * * *" }
    # The last 14 days' account deletions run again (and older ones forgotten), so a database
    # restored from a backup brings nobody back; run it by hand right after a restore too.
    erasures = { service = "library", path = "/internal/schedules/erasures", cron = "0 5 * * *" }
    # Assistant conversations nobody added to for its retention period (90 days), AI apps'
    # connections whose refresh token expired, and apps with no connection for 30 days.
    assistant-retention = { service = "assistant", path = "/internal/schedules/retention", cron = "0 4 * * *" }
    # Emails to company members, in the morning (UTC): every minute for an hour, each run
    # going on where the last stopped (none is sent twice): the activity digest from 7:00,
    # reminders from 8:00; each again three hours later, catching up on what the first missed.
    member-digest    = { service = "notifications", path = "/internal/schedules/digest", cron = "* 7,10 * * *" }
    member-reminders = { service = "notifications", path = "/internal/schedules/reminders", cron = "* 8,11 * * *" }
    # Emails to many users (legal notices, campaigns): every minute from 8:00 to 18:59 UTC, each
    # run sending the next pending recipients for 40 seconds.
    bulk-emails = { service = "notifications", path = "/internal/schedules/bulk", cron = "* 8-18 * * *" }
    # ATS candidates still waiting or whose invite stalled, results kept while a connection was
    # broken or the ATS failed, and candidates past their retention.
    ats-recover = { service = "ats", path = "/internal/schedules/recover", cron = "*/10 * * * *" }
    # Events companies' web hooks didn't take, sent again with backoff.
    webhook-retries = { service = "api", path = "/internal/schedules/webhook-retries", cron = "*/5 * * * *" }
    # Events not published right after their change (the outbox).
    library-outbox       = { service = "library", path = "/internal/schedules/outbox", cron = "* * * * *" }
    companies-outbox     = { service = "companies", path = "/internal/schedules/outbox", cron = "* * * * *" }
    rounds-outbox        = { service = "rounds", path = "/internal/schedules/outbox", cron = "* * * * *" }
    generation-outbox    = { service = "generation-worker", path = "/internal/schedules/outbox", cron = "* * * * *" }
    ats-outbox           = { service = "ats", path = "/internal/schedules/outbox", cron = "* * * * *" }
    billing-outbox       = { service = "billing", path = "/internal/schedules/outbox", cron = "* * * * *" }
    notifications-outbox = { service = "notifications", path = "/internal/schedules/outbox", cron = "* * * * *" }
    api-outbox           = { service = "api", path = "/internal/schedules/outbox", cron = "* * * * *" }
    # The edited limits written to Redis again, so a Redis wipe heals itself; AI usage and limit
    # hits past 13 months, and limit changes past 24.
    billing-limits    = { service = "billing", path = "/internal/schedules/limits", cron = "*/5 * * * *" }
    billing-retention = { service = "billing", path = "/internal/schedules/retention", cron = "30 4 * * *" }
    # What Paddle's web hooks of the last week should have done, done again from Paddle's own
    # records: a payment's credits or a refund a web hook never delivered.
    billing-reconcile = { service = "billing", path = "/internal/schedules/reconcile", cron = "15 5 * * *" }
    # A new price for an automatic top-up, announced to its company 30 days before it applies.
    billing-auto-top-up-prices = { service = "billing", path = "/internal/schedules/auto-top-up-prices", cron = "45 5 * * *" }
    # Interviews whose time ran out after the candidate left.
    interview-expiry = { service = "rounds", path = "/internal/schedules/expire-interviews", cron = "* * * * *" }
  }
}

# Jobs created paused, to be resumed by removing them here. quality-patterns reads every company's
# flagged questions to write general rules: it may run on real data only once the terms and
# privacy version that says so (internal_docs/plans/quality-patterns.md) is in force.
locals {
  paused_schedules = ["quality-patterns"]
}

resource "google_cloud_scheduler_job" "schedule" {
  for_each  = local.schedules
  name      = each.key
  region    = var.region
  schedule  = each.value.cron
  time_zone = "Etc/UTC"
  # As long as the service lets the request run (Scheduler allows 15s to 30 minutes): waiting
  # longer only delays the retry. A retry may still overlap a run Cloud Run cut off, so each job
  # is safe to run twice at once (invite expiry re-checks before holding credits again).
  attempt_deadline = "${max(15, min(local.services[each.value.service].timeout, 1800))}s"
  paused           = contains(local.paused_schedules, each.key)

  # The daily jobs retry a failed run; the frequent ones (cron starting with "*") just run again
  # soon.
  dynamic "retry_config" {
    for_each = startswith(each.value.cron, "*") ? [] : [1]

    content {
      retry_count          = 3
      min_backoff_duration = "60s"
      max_backoff_duration = "600s"
    }
  }

  http_target {
    http_method = "POST"
    uri         = "${local.run_url[each.value.service]}${each.value.path}"

    oidc_token {
      service_account_email = google_service_account.invoker.email
      audience              = local.run_url[each.value.service]
    }
  }

  depends_on = [google_project_service.apis]
}
