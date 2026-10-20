# Cost: a monthly budget on the billing account, scoped to this project. Emails at 50%, 90% and
# 100% of it, and when the month's forecast passes it. It only alerts; nothing is stopped.
resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account
  display_name    = "prepza monthly"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      units = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.9
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = local.alert_channels
    disable_default_iam_recipients   = false
  }

  depends_on = [google_project_service.apis]
}
