# Two service level objectives, measured at the load balancer over 28 days, and the alerts on how
# fast each one's error budget (1 - the goal) burns: the public APIs answering without a server
# error, and candidates' answers (rounds) answering within 2 seconds. A fast burn (about 14 times
# the sustainable rate, over the last hour and the last 5 minutes at once) spends 2% of the month's
# budget in an hour and pages; a slow one (the sustainable rate or more, over the last day and the
# last 2 hours) would spend it all by the period's end and is a ticket. When a budget is spent,
# reliability work comes before features (docs/runbooks.md).
locals {
  # Every backend but the site's pages: the APIs under /api/, the bell's stream and the assistant's
  # MCP and OAuth paths.
  api_backends = [for name, _ in local.public_services : "\"${name}\"" if name != "frontend"]

  slos = {
    api = {
      name = "Public APIs answer without a server error"
      goal = 0.995
    }
    answers = {
      name = "Candidates' answers within 2 s"
      goal = 0.95
    }
  }

  slo_alerts = {
    api_fast = {
      slo     = "api"
      name    = "prepza API errors burning the budget fast"
      windows = ["3600s", "300s"]
      rate    = 14.4
      page    = true
      runbook = "platform.md#api-errors-burning-the-budget"
      text    = "The public APIs answer too many requests with a server error: at this rate the month's error budget is gone in about two days. Users see failed pages and requests now."
    }
    api_slow = {
      slo     = "api"
      name    = "prepza API errors burning the budget"
      windows = ["86400s", "7200s"]
      rate    = 1
      page    = false
      runbook = "platform.md#api-errors-burning-the-budget"
      text    = "The public APIs' server errors have spent the error budget at least as fast as it allows for a day: it runs out before the month ends."
    }
    answers_fast = {
      slo     = "answers"
      name    = "prepza candidate answers slow"
      windows = ["3600s", "300s"]
      rate    = 14.4
      page    = true
      runbook = "platform.md#candidate-answers-slow"
      text    = "Many of candidates' requests to the interview service (rounds) take over 2 seconds: they wait at every question now."
    }
    answers_slow = {
      slo     = "answers"
      name    = "prepza candidate answers slowing"
      windows = ["86400s", "7200s"]
      rate    = 1
      page    = false
      runbook = "platform.md#candidate-answers-slow"
      text    = "Candidates' requests to the interview service (rounds) have been over 2 seconds more often than the objective allows for a day."
    }
  }
}

resource "google_monitoring_custom_service" "site" {
  service_id   = "prepza"
  display_name = "prepza"

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_slo" "api" {
  service             = google_monitoring_custom_service.site.service_id
  slo_id              = "api-availability"
  display_name        = local.slos.api.name
  goal                = local.slos.api.goal
  rolling_period_days = 28

  request_based_sli {
    good_total_ratio {
      total_service_filter = "metric.type=\"loadbalancing.googleapis.com/https/request_count\" AND resource.type=\"https_lb_rule\" AND resource.label.backend_target_name=one_of(${join(", ", local.api_backends)})"
      bad_service_filter   = "metric.type=\"loadbalancing.googleapis.com/https/request_count\" AND resource.type=\"https_lb_rule\" AND resource.label.backend_target_name=one_of(${join(", ", local.api_backends)}) AND metric.label.response_code_class=500"
    }
  }
}

resource "google_monitoring_slo" "answers" {
  service             = google_monitoring_custom_service.site.service_id
  slo_id              = "answer-latency"
  display_name        = local.slos.answers.name
  goal                = local.slos.answers.goal
  rolling_period_days = 28

  request_based_sli {
    distribution_cut {
      # Without voice mode's live listening (101, a WebSocket held while the candidate speaks,
      # up to a minute): its latency is how long it was open, not a wait.
      distribution_filter = "metric.type=\"loadbalancing.googleapis.com/https/total_latencies\" AND resource.type=\"https_lb_rule\" AND resource.label.backend_target_name=\"rounds\" AND NOT metric.label.response_code_class=100"

      # Milliseconds.
      range {
        max = 2000
      }
    }
  }
}

resource "google_monitoring_alert_policy" "slo" {
  for_each     = local.slo_alerts
  display_name = each.value.name
  combiner     = "AND"
  severity     = each.value.page ? "CRITICAL" : "WARNING"

  dynamic "conditions" {
    for_each = each.value.windows

    content {
      display_name = "Burn rate over ${conditions.value} above ${each.value.rate}"

      condition_threshold {
        filter          = "select_slo_burn_rate(\"${each.value.slo == "api" ? google_monitoring_slo.api.name : google_monitoring_slo.answers.name}\", \"${conditions.value}\")"
        comparison      = "COMPARISON_GT"
        threshold_value = each.value.rate
        duration        = "0s"
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
