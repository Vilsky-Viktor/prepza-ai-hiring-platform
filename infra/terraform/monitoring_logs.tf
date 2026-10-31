# Log-based metrics: what the services' own log lines count, for the alerts in
# monitoring_log_alerts.tf (testee_limit_hits is only counted, by limit).

resource "google_logging_metric" "redis_errors" {
  name   = "testee_redis_errors"
  filter = "resource.type=\"cloud_run_revision\" AND severity>=WARNING AND (jsonPayload.exc:\"redis.exceptions\" OR textPayload:\"redis.exceptions\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "openai_errors" {
  name = "testee_openai_errors"
  # A traceback naming openai, or a message that does (the assistant logs only the error's type).
  filter = "resource.type=\"cloud_run_revision\" AND severity>=ERROR AND (jsonPayload.exc:\"openai.\" OR jsonPayload.message:\"openai.\" OR textPayload:\"openai.\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# Every AI call logs what it cost ("AI used: action=... cost=$0.001234"), by action.
resource "google_logging_metric" "ai_spend" {
  name            = "testee_ai_spend"
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
  name   = "testee_limit_hits"
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
  name   = "testee_ai_stopped"
  filter = "resource.type=\"cloud_run_revision\" AND (jsonPayload.message:\"Shared limit used up\" OR jsonPayload.message:\"OpenAI quota exhausted\" OR jsonPayload.message:\"Unpaid AI spend\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# notifications logs each email Resend reports bounced, suppressed, failed or marked as spam.
resource "google_logging_metric" "emails_undelivered" {
  name   = "testee_emails_undelivered"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"notifications\" AND jsonPayload.message:\"Email not delivered\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# Generations that failed: a run that errored (its task still succeeds, so the task alert below
# never sees it), and the sweep marking stuck ones as failed.
resource "google_logging_metric" "generations_failed" {
  name   = "testee_generations_failed"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=(\"generation\" OR \"generation-worker\") AND severity>=WARNING AND (jsonPayload.message=~\"^Generation \\S+ failed$\" OR jsonPayload.message:\"stuck generations as failed\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# billing logs "Paddle unavailable" when Paddle's API doesn't answer or answers with a 5xx (not a
# refusal such as a declined card).
resource "google_logging_metric" "paddle_unavailable" {
  name   = "testee_paddle_unavailable"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"billing\" AND jsonPayload.message:\"Paddle unavailable\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}
