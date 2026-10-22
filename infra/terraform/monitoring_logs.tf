# Alerts counted from the services' own logs (log-based metrics), by email to var.alert_email:
# Redis or OpenAI failing, AI spend running high, AI stopped for many, generation tasks failing, and
# emails not delivered.

resource "google_logging_metric" "redis_errors" {
  name   = "prepza_redis_errors"
  filter = "resource.type=\"cloud_run_revision\" AND severity>=WARNING AND (jsonPayload.exc:\"redis.exceptions\" OR textPayload:\"redis.exceptions\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "openai_errors" {
  name = "prepza_openai_errors"
  # A traceback naming openai, or a message that does (the assistant logs only the error's type).
  filter = "resource.type=\"cloud_run_revision\" AND severity>=ERROR AND (jsonPayload.exc:\"openai.\" OR jsonPayload.message:\"openai.\" OR textPayload:\"openai.\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# Every AI call logs what it cost ("AI used: action=... cost=$0.001234"), by action.
resource "google_logging_metric" "ai_spend" {
  name            = "prepza_ai_spend"
  filter          = "resource.type=\"cloud_run_revision\" AND jsonPayload.message:\"AI used: \""
  value_extractor = "REGEXP_EXTRACT(jsonPayload.message, \"cost=\\\\$([0-9.]+)\")"
  label_extractors = {
    action = "REGEXP_EXTRACT(jsonPayload.message, \"action=(\\\\S+)\")"
  }

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    unit        = "USD"

    labels {
      key        = "action"
      value_type = "STRING"
    }
  }

  bucket_options {
    exponential_buckets {
      num_finite_buckets = 20
      growth_factor      = 2
      scale              = 0.0001
    }
  }
}

# Every refusal by a limit, ours or a provider's ("Limit hit: limit=NAME ..."), by limit.
resource "google_logging_metric" "limit_hits" {
  name   = "prepza_limit_hits"
  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.message:\"Limit hit: \""
  label_extractors = {
    limit = "REGEXP_EXTRACT(jsonPayload.message, \"limit=(\\\\S+)\")"
  }

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"

    labels {
      key        = "limit"
      value_type = "STRING"
    }
  }
}

# What stops AI for many at once: a shared limit used up (for everyone), OpenAI's account out of
# money, and the unpaid users' daily AI spend cap near (80%) or reached.
resource "google_logging_metric" "ai_stopped" {
  name   = "prepza_ai_stopped"
  filter = "resource.type=\"cloud_run_revision\" AND (jsonPayload.message:\"Shared limit used up\" OR jsonPayload.message:\"OpenAI quota exhausted\" OR jsonPayload.message:\"Unpaid AI spend\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# notifications logs each email Resend reports bounced, suppressed, failed or marked as spam.
resource "google_logging_metric" "emails_undelivered" {
  name   = "prepza_emails_undelivered"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"notifications\" AND jsonPayload.message:\"Email not delivered\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# Generations that failed: a run that errored (its task still succeeds, so the task alert below
# never sees it), and the sweep marking stuck ones as failed.
resource "google_logging_metric" "generations_failed" {
  name   = "prepza_generations_failed"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=(\"generation\" OR \"generation-worker\") AND severity>=WARNING AND (jsonPayload.message=~\"^Generation \\S+ failed$\" OR jsonPayload.message:\"stuck generations as failed\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# billing logs "Paddle unavailable" when Paddle's API doesn't answer or answers with a 5xx (not a
# refusal such as a declined card).
resource "google_logging_metric" "paddle_unavailable" {
  name   = "prepza_paddle_unavailable"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"billing\" AND jsonPayload.message:\"Paddle unavailable\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

locals {
  # Each: its metric (a log-based one, or Cloud Run's), the threshold over the window, the
  # window, and what to do.
  log_alerts = {
    redis = {
      name      = "prepza Redis failing"
      condition = "Over 20 Redis errors in 10 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.redis_errors.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 20
      window    = "600s"
      text      = "Services can't reach Redis (Upstash): rate limits, live updates and the pause and maintenance switches fail open or error. Check Upstash's status and the redis-url secret."
    }
    openai = {
      name      = "prepza OpenAI failing"
      condition = "Over 10 OpenAI errors in 15 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.openai_errors.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 10
      window    = "900s"
      text      = "Calls to OpenAI fail: generation, the help chat and the assistant are affected. Check OpenAI's status page, the account's limits and credit, and the openai-api-key secret."
    }
    spend = {
      name      = "prepza AI spend high"
      condition = "AI calls cost over var.ai_spend_alert_hourly USD in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ai_spend.name}\" AND resource.type=\"cloud_run_revision\""
      # The sum of the logged amounts, a distribution's values.
      aligner   = "ALIGN_SUM"
      threshold = var.ai_spend_alert_hourly
      window    = "3600s"
      text      = "OpenAI spend in the last hour is above the alert level. The admin zone's AI costs tab shows which action, company or user it was; each call logs \"AI used\" with its cost. Look for a loop or abuse, and the limits in Controls."
    }
    ai_stopped = {
      name      = "prepza AI stopped for many"
      condition = "A shared limit used up, OpenAI out of credit, or unpaid AI spend at 80% of its daily cap"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ai_stopped.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 0
      window    = "300s"
      text      = "Check the logs for the line: \"Shared limit used up\" (a limit for everyone was reached: raise it in Controls if it's real use), \"OpenAI quota exhausted\" (top up the OpenAI account: every AI call fails), \"Unpaid AI spend near the daily cap\" (raise AI_SPEND_UNPAID_DAY in Controls before unpaid users are refused) or \"reached the daily cap\" (they are refused until midnight UTC)."
    }
    generations = {
      name      = "prepza generations failing"
      condition = "Over 2 generations failed in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.generations_failed.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 2
      window    = "3600s"
      text      = "Generations fail: companies see \"Generation failed\" and must press Retry. Check generation-worker's logs and Sentry for the error, and OpenAI. See docs/runbooks.md (A stuck generation, OpenAI down)."
    }
    paddle = {
      name      = "prepza Paddle failing"
      condition = "Over 3 calls to Paddle failed in 15 minutes"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.paddle_unavailable.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = 3
      window    = "900s"
      text      = "Paddle's API doesn't answer, or refuses billing's key (expired, wrong or short of a permission): checkouts don't open, automatic top-ups and invoices fail. Check Paddle's status page and the paddle-api-key secret's expiry and permissions. See docs/runbooks.md (Paddle down)."
    }
    migrations = {
      name      = "prepza migration failed"
      condition = "A database migration or roles job failed"
      filter    = "metric.type=\"run.googleapis.com/job/completed_execution_count\" AND resource.type=\"cloud_run_job\" AND metric.label.result=\"failed\""
      aligner   = "ALIGN_DELTA"
      threshold = 0
      window    = "300s"
      text      = "A deploy's migration (or db-roles) job failed, and the deploy stopped before moving any service. See docs/runbooks.md (A failed migration during a deploy)."
    }
    bounces = {
      name      = "prepza emails bouncing"
      condition = "Over var.email_bounce_alert_hourly emails not delivered in an hour"
      filter    = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.emails_undelivered.name}\" AND resource.type=\"cloud_run_revision\""
      aligner   = "ALIGN_DELTA"
      threshold = var.email_bounce_alert_hourly
      window    = "3600s"
      text      = "Many emails bounce or are marked as spam: Resend may suspend sending. Check Resend's dashboard for the cause (bad addresses from one company, DNS, a spam complaint wave)."
    }
  }
}

resource "google_monitoring_alert_policy" "logs" {
  for_each     = local.log_alerts
  display_name = each.value.name
  combiner     = "OR"

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
  }

  notification_channels = local.alert_channels
}

# Generation tasks: a task's attempt that fails is retried, and dropped after its last; many
# failing attempts mean runs are being lost.
resource "google_monitoring_alert_policy" "tasks_failing" {
  display_name = "prepza generation tasks failing"
  combiner     = "OR"

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
  }

  notification_channels = local.alert_channels
}
