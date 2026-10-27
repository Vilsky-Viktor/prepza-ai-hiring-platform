# Outage and error alerts. Two severities: a page (CRITICAL) is a symptom users feel now, sent to
# the phone (the Cloud Monitoring app, SMS as a backup) and by email; a ticket (WARNING) is a cause
# or a slow drift, by email only. Each alert links its runbook section (docs/runbooks/).
#
# Uptime: Google checks the site and each API's /ready through the load balancer every minute,
# from three regions, and that the right page answered; an alert fires when a check fails from
# more than one of them.
locals {
  uptime_paths = merge(
    { site = "/" },
    { for name, service in local.public_services : name => "/api/${service.path}/ready" if service.path != null },
  )
  runbooks = "https://github.com/${var.github_repository}/blob/main/docs/runbooks"
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "prepza alerts"
  type         = "email"
  labels       = { email_address = var.alert_email }

  depends_on = [google_project_service.apis]
}

# A second way to be paged, as an email can sit unread: pages also go by text message to
# alert_sms when it's set, besides the Cloud Monitoring app (alert_app_channel).
resource "google_monitoring_notification_channel" "sms" {
  count        = var.alert_sms == "" ? 0 : 1
  display_name = "prepza alerts (SMS)"
  type         = "sms"
  labels       = { number = var.alert_sms }

  depends_on = [google_project_service.apis]
}

locals {
  ticket_channels = [google_monitoring_notification_channel.email.id]
  page_channels = concat(
    local.ticket_channels,
    google_monitoring_notification_channel.sms[*].id,
    var.alert_app_channel == "" ? [] : [var.alert_app_channel],
  )
}

resource "google_monitoring_uptime_check_config" "check" {
  for_each     = local.uptime_paths
  display_name = "prepza ${each.key}"
  timeout      = "10s"
  period       = "60s"

  selected_regions = ["EUROPE", "USA", "ASIA_PACIFIC"]

  http_check {
    path         = each.value
    port         = 443
    use_ssl      = true
    validate_ssl = true

    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  # The right page answered, not just something: the site's name on the site, an API's ready
  # status on /ready.
  content_matchers {
    content = each.key == "site" ? "prepza" : "\"status\":\"ready\""
    matcher = "CONTAINS_STRING"
  }

  monitored_resource {
    type   = "uptime_url"
    labels = { project_id = var.project_id, host = var.domain }
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_alert_policy" "down" {
  for_each     = google_monitoring_uptime_check_config.check
  display_name = "prepza ${each.key} is down"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = "${each.key} fails its uptime check"

    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${each.value.uptime_check_id}\" AND resource.type=\"uptime_url\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1

      aggregations {
        alignment_period     = "1200s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.*"]
      }
    }
  }

  documentation {
    content   = "https://${var.domain}${local.uptime_paths[each.key]} stopped answering. Check the service's Cloud Run logs and Sentry."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: site or API down"
      url          = "${local.runbooks}/platform.md#site-or-api-down"
    }
  }

  notification_channels = local.page_channels
}

# Dead letters: an event a consumer kept failing on for hours (pubsub.tf). Fires while any wait
# in the dead-letter subscription; replay them as infra/README.md (Notes) shows.
resource "google_monitoring_alert_policy" "dead_letters" {
  display_name = "prepza events dead-lettered"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = "events-dead-letter has messages"

    condition_threshold {
      filter          = "metric.type=\"pubsub.googleapis.com/subscription/num_undelivered_messages\" AND resource.type=\"pubsub_subscription\" AND resource.label.subscription_id=\"${google_pubsub_subscription.dead_letter.name}\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  documentation {
    content   = "Events failed 50 deliveries and wait in the events-dead-letter subscription. Fix the consumer (Cloud Run logs, Sentry), then replay them as infra/README.md (Notes) shows."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: events waiting or dead-lettered"
      url          = "${local.runbooks}/platform.md#events-waiting-or-dead-lettered"
    }
  }

  notification_channels = local.page_channels
}

# Scheduler: a periodic job (jobs.tf) whose run failed, from Cloud Scheduler's own error logs.
resource "google_monitoring_alert_policy" "scheduler_failed" {
  display_name = "prepza scheduled job failed"
  combiner     = "OR"
  severity     = "WARNING"

  conditions {
    display_name = "Cloud Scheduler logged a failed run"

    condition_matched_log {
      filter = "resource.type=\"cloud_scheduler_job\" AND severity>=ERROR"

      label_extractors = {
        job = "EXTRACT(resource.labels.job_id)"
      }
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }

    auto_close = "86400s"
  }

  documentation {
    content   = "A scheduled job failed. Check the job in Cloud Scheduler and its service's Cloud Run logs."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: a scheduled job failed"
      url          = "${local.runbooks}/platform.md#a-scheduled-job-failed"
    }
  }

  notification_channels = local.ticket_channels
}

# Web hooks refused: Paddle's or Resend's signature check failed (WEBHOOK_SIGNATURE_REFUSED in
# prepza_common/config/constants.py). Usually a wrong or unset secret: then every payment and email event
# is refused, as 401s the server-error alert doesn't count.
resource "google_monitoring_alert_policy" "webhook_signature_refused" {
  display_name = "prepza web hook signature refused"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = "A provider's web hook failed its signature check"

    condition_matched_log {
      filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.message:\"web hook signature refused\""

      label_extractors = {
        service = "EXTRACT(resource.labels.service_name)"
      }
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }

    auto_close = "86400s"
  }

  documentation {
    content   = "Paddle's or Resend's web hook was refused for its signature. If it keeps happening, the secret is wrong: compare `paddle-webhook-secret` or `resend-webhook-secret` (Secret Manager) with the provider's dashboard, then resend the failed events from there. Paid top-ups get their credits only once it's fixed."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: a web hook signature refused"
      url          = "${local.runbooks}/platform.md#a-web-hook-signature-refused"
    }
  }

  notification_channels = local.page_channels
}

# Server errors: a Cloud Run service answering more than 5% of its requests with a 5xx for ten
# minutes. A ticket: the API availability SLO (monitoring_slo.tf) pages when users feel it.
resource "google_monitoring_alert_policy" "server_errors" {
  display_name = "prepza server errors"
  combiner     = "OR"
  severity     = "WARNING"

  conditions {
    display_name = "5xx share of requests above 5%"

    condition_threshold {
      filter             = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND metric.label.response_code_class=\"5xx\""
      denominator_filter = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\""
      duration           = "600s"
      comparison         = "COMPARISON_GT"
      threshold_value    = 0.05

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.service_name"]
      }

      denominator_aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.service_name"]
      }
    }
  }

  documentation {
    content   = "A service answers many requests with server errors. Check its Cloud Run logs and Sentry."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: server errors"
      url          = "${local.runbooks}/platform.md#server-errors"
    }
  }

  notification_channels = local.ticket_channels
}
