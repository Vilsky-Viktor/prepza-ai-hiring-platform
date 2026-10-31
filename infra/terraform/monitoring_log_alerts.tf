# Alerts counted from the services' own logs (monitoring_logs.tf's metrics) and Cloud Tasks, with
# the channels and severities monitoring.tf describes: Redis or OpenAI failing, AI spend running
# high (an hour's spike pages, the day's total is a ticket), AI stopped for many, generations and
# their tasks failing, a failed migration, and emails not delivered.

locals {
  # Each: its metric (a log-based one, or Cloud Run's), the threshold over the window, the
  # window, what to do, whether it pages (else it's a ticket) and its runbook section.
  log_alerts = {
    redis = {
      name      = "testee Redis failing"
      condition = "Over 20 Redis errors in 10 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.redis_errors.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 20
      window    = "600s"
      text      = "Services can't reach Redis (Upstash): rate limits, live updates and the pause and maintenance switches fail open or error. Check Upstash's status and the redis-url secret."
      page      = true
      runbook   = "providers.md#redis-down"
    }
    openai = {
      name      = "testee OpenAI failing"
      condition = "Over 10 OpenAI errors in 15 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.openai_errors.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 10
      window    = "900s"
      text      = "Calls to OpenAI fail: generation, the help chat and the assistant are affected. Check OpenAI's status page, the account's limits and credit, and the openai-api-key secret."
      page      = true
      runbook   = "providers.md#openai-down"
    }
    spend = {
      name      = "testee AI spend high"
      condition = "AI calls cost over var.ai_spend_alert_hourly USD in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ai_spend.name}\" AND resource.type=\"cloud_run_revision\""
      # The sum of the logged amounts, a distribution's values.
      aligner   = "ALIGN_SUM"
      threshold = var.ai_spend_alert_hourly
      window    = "3600s"
      text      = "OpenAI spend in the last hour is above the alert level. The admin zone's AI costs tab shows which action, company or user it was; each call logs \"AI used\" with its cost. Look for a loop or abuse, and the limits in Controls."
      page      = true
      runbook   = "providers.md#ai-spend-high-or-ai-stopped"
    }
    spend_daily = {
      name      = "testee AI spend high today"
      condition = "AI calls cost over var.ai_spend_alert_daily USD in a day"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ai_spend.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_SUM"
      threshold = var.ai_spend_alert_daily
      window    = "86400s"
      text      = "OpenAI spend over the last 24 hours is above the daily alert level, though no hour spiked. The admin zone's AI costs tab shows which action, company or user it was. If it's real use, raise the level; otherwise find the loop or abuse and the limits in Controls."
      page      = false
      runbook   = "providers.md#ai-spend-high-or-ai-stopped"
    }
    ai_stopped = {
      name      = "testee AI stopped for many"
      condition = "A shared limit used up, OpenAI out of credit, or unpaid AI spend at 80% of its daily cap"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ai_stopped.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 0
      window    = "300s"
      text      = "Check the logs for the line: \"Shared limit used up\" (a limit for everyone was reached: raise it in Controls if it's real use), \"OpenAI quota exhausted\" (top up the OpenAI account: every AI call fails), \"Unpaid AI spend near the daily cap\" (raise AI_SPEND_UNPAID_DAY in Controls before unpaid users are refused) or \"reached the daily cap\" (they are refused until midnight UTC)."
      page      = true
      runbook   = "providers.md#ai-spend-high-or-ai-stopped"
    }
    generations = {
      name      = "testee generations failing"
      condition = "Over 2 generations failed in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.generations_failed.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 2
      window    = "3600s"
      text      = "Generations fail: companies see \"Generation failed\" and must press Retry. Check generation-worker's logs and Sentry for the error, and OpenAI."
      page      = true
      runbook   = "platform.md#a-stuck-generation"
    }
    paddle = {
      name      = "testee Paddle failing"
      condition = "Over 3 calls to Paddle failed in 15 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.paddle_unavailable.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 3
      window    = "900s"
      text      = "Paddle's API doesn't answer, or refuses billing's key (expired, wrong or short of a permission): checkouts don't open, automatic top-ups and invoices fail. Check Paddle's status page and the paddle-api-key secret's expiry and permissions."
      page      = true
      runbook   = "providers.md#paddle-down"
    }
    migrations = {
      name      = "testee migration failed"
      condition = "A database migration or roles job failed"
      filter    = "metric.type=\"run.googleapis.com/job/completed_execution_count\" AND resource.type=\"cloud_run_job\" AND metric.label.result=\"failed\""
      aligner   = "ALIGN_DELTA"
      threshold = 0
      window    = "300s"
      text      = "A deploy's migration (or db-roles) job failed, and the deploy stopped before moving any service."
      page      = true
      runbook   = "platform.md#a-failed-migration-during-a-deploy"
    }
    bounces = {
      name      = "testee emails bouncing"
      condition = "Over var.email_bounce_alert_hourly emails not delivered in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.emails_undelivered.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = var.email_bounce_alert_hourly
      window    = "3600s"
      text      = "Many emails bounce or are marked as spam: Resend may suspend sending. Check Resend's dashboard for the cause (bad addresses from one company, DNS, a spam complaint wave)."
      page      = true
      runbook   = "platform.md#emails-bouncing"
    }
  }
}

resource "google_monitoring_alert_policy" "logs" {
  for_each     = local.log_alerts
  display_name = each.value.name
  combiner     = "OR"
  severity     = each.value.page ? "CRITICAL" : "WARNING"

  conditions {
    display_name = each.value.condition

    condition_threshold {
      filter          = each.value.filter
      comparison      = "COMPARISON_GT"
      threshold_value = each.value.threshold
      duration        = "0s"

      aggregations {
        alignment_period     = each.value.window
        per_series_aligner   = each.value.aligner
        cross_series_reducer = "REDUCE_SUM"
      }

      trigger {
        count = 1
      }
    }
  }

  alert_strategy {
    auto_close = "86400s"
  }

  documentation {
    content   = each.value.text
    mime_type = "text/markdown"

    links {
      display_name = "Runbook"
      url          = "${local.runbooks}/${each.value.runbook}"
    }
  }

  notification_channels = each.value.page ? local.page_channels : local.ticket_channels
}

# Generation tasks: a task's attempt that fails is retried, and dropped after its last; many
# failing attempts mean runs are being lost.
resource "google_monitoring_alert_policy" "tasks_failing" {
  display_name = "testee generation tasks failing"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = "Over 20% of generation task attempts failed for 30 minutes"

    condition_threshold {
      filter             = "metric.type=\"cloudtasks.googleapis.com/queue/task_attempt_count\" AND resource.type=\"cloud_tasks_queue\" AND metric.label.response_code!=\"OK\""
      denominator_filter = "metric.type=\"cloudtasks.googleapis.com/queue/task_attempt_count\" AND resource.type=\"cloud_tasks_queue\""
      comparison         = "COMPARISON_GT"
      threshold_value    = 0.2
      duration           = "1800s"

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
      }

      denominator_aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "86400s"
  }

  documentation {
    content   = "Many generation task attempts fail; after their last attempt Cloud Tasks drops them and the interviews stay ungenerated. Check generation-worker's Cloud Run logs and Sentry, and the generation queue in Cloud Tasks."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: a stuck generation"
      url          = "${local.runbooks}/platform.md#a-stuck-generation"
    }
  }

  notification_channels = local.page_channels
}
