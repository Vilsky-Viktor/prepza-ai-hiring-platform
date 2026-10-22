# Payments not credited: billing refused to credit a paid transaction (logged "refund it", or a
# transaction with no valid owner), or the daily reconciliation had to apply what a web hook
# missed or failed to. Each one is money a company paid without its credits, or a refund it
# owes, so a single line alerts.
resource "google_monitoring_alert_policy" "payments_not_credited" {
  display_name = "prepza payment not credited"
  combiner     = "OR"
  severity     = "CRITICAL"

  conditions {
    display_name = "billing refused a payment or reconciliation repaired one"

    condition_matched_log {
      filter = join(" AND ", [
        "resource.type=\"cloud_run_revision\"",
        "resource.labels.service_name=\"billing\"",
        "(jsonPayload.message:\"refund it\" OR jsonPayload.message:\"has no valid owner\" OR jsonPayload.message:\"Reconciliation credited\" OR jsonPayload.message:\"Reconciliation counted\" OR jsonPayload.message:\"Reconciling\")",
      ])
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }

    auto_close = "86400s"
  }

  documentation {
    content   = "billing refused to credit a paid transaction (\"refund it\", \"has no valid owner\"), or the daily reconciliation applied a payment or refund its web hook missed (\"Reconciliation credited\", \"Reconciliation counted\") or failed to (\"Reconciling … failed\"). See the runbook below."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: a payment not credited"
      url          = "${local.runbooks}/providers.md#a-payment-not-credited"
    }
  }

  notification_channels = local.page_channels
}
