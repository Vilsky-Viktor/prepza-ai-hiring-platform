# Database alerts (monitoring.tf has the channels): causes, so tickets, by email only. What users
# feel (slow or failing requests) pages through the SLOs (monitoring_slo.tf) and the uptime checks.
locals {
  # Each: the Cloud SQL metric, how long it stays past the threshold, how it's aligned, and what
  # to do.
  database_alerts = {
    connections = {
      # Open connections past 80% of max_connections (database.tf), the sign to raise db_tier
      # before a deploy at peak runs out of them.
      name      = "testee database connections high"
      condition = "Postgres connections above 80% of the limit"
      metric    = "cloudsql.googleapis.com/database/postgresql/num_backends"
      duration  = "300s"
      threshold = floor(local.db_max_connections * 0.8)
      period    = "60s"
      aligner   = "ALIGN_MAX"
      sum       = true
      text      = "The database is near its connection limit. Raise db_tier (and db_max_connections) as infra/README.md describes, or lower services' max instances."
    }
    cpu = {
      name      = "testee database CPU high"
      condition = "Cloud SQL CPU above 80%"
      metric    = "cloudsql.googleapis.com/database/cpu/utilization"
      duration  = "900s"
      threshold = 0.8
      period    = "300s"
      aligner   = "ALIGN_MEAN"
      sum       = false
      text      = "The database has been busy for a while. Check slow queries in Cloud SQL Query Insights, or raise db_tier."
    }
    memory = {
      # Above 90% for fifteen minutes, before Postgres starts failing queries.
      name      = "testee database memory high"
      condition = "Postgres memory above 90%"
      metric    = "cloudsql.googleapis.com/database/memory/utilization"
      duration  = "900s"
      threshold = 0.9
      period    = "300s"
      aligner   = "ALIGN_MAX"
      sum       = false
      text      = "The database is short of memory. Raise db_tier (infra/README.md) or look for heavy queries in Query Insights."
    }
    disk = {
      # Storage grows by itself, but a fast fill means something writes too much.
      name      = "testee database disk filling"
      condition = "Postgres disk above 85% full"
      metric    = "cloudsql.googleapis.com/database/disk/utilization"
      duration  = "0s"
      threshold = 0.85
      period    = "300s"
      aligner   = "ALIGN_MAX"
      sum       = false
      text      = "The database disk is over 85% full. Check which tables grew (Query Insights) and the retention jobs; storage grows automatically, within its limit."
    }
  }
}

resource "google_monitoring_alert_policy" "database" {
  for_each     = local.database_alerts
  display_name = each.value.name
  combiner     = "OR"
  severity     = "WARNING"

  conditions {
    display_name = each.value.condition

    condition_threshold {
      filter          = "metric.type=\"${each.value.metric}\" AND resource.type=\"cloudsql_database\""
      duration        = each.value.duration
      comparison      = "COMPARISON_GT"
      threshold_value = each.value.threshold

      aggregations {
        alignment_period     = each.value.period
        per_series_aligner   = each.value.aligner
        cross_series_reducer = each.value.sum ? "REDUCE_SUM" : null
        group_by_fields      = each.value.sum ? ["resource.label.database_id"] : null
      }
    }
  }

  documentation {
    content   = each.value.text
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: the database under strain"
      url          = "${local.runbooks}/platform.md#the-database-under-strain"
    }
  }

  notification_channels = local.ticket_channels
}

moved {
  from = google_monitoring_alert_policy.database_connections
  to   = google_monitoring_alert_policy.database["connections"]
}

moved {
  from = google_monitoring_alert_policy.database_cpu
  to   = google_monitoring_alert_policy.database["cpu"]
}

moved {
  from = google_monitoring_alert_policy.database_memory
  to   = google_monitoring_alert_policy.database["memory"]
}

moved {
  from = google_monitoring_alert_policy.database_disk
  to   = google_monitoring_alert_policy.database["disk"]
}

# Backups: a Cloud SQL backup run that failed, from its own error logs. The drill
# (scripts/ops/restore-drill.sh) proves the ones that succeed restore.
resource "google_monitoring_alert_policy" "database_backup_failed" {
  display_name = "testee database backup failed"
  combiner     = "OR"
  severity     = "WARNING"

  conditions {
    display_name = "Cloud SQL logged a failed backup"

    condition_matched_log {
      filter = "resource.type=\"cloudsql_database\" AND severity>=ERROR AND (protoPayload.methodName:\"backup\" OR textPayload:\"backup\")"
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }

    auto_close = "86400s"
  }

  documentation {
    content   = "A database backup failed. Check the instance's backups in Cloud SQL and start one by hand (gcloud sql backups create --instance=testee). Google keeps a backup made by hand until someone deletes it: once the automated backups work again, delete it (gcloud sql backups delete <id> --instance=testee), at most 14 days later, so backups last no longer than the privacy policy says."
    mime_type = "text/markdown"

    links {
      display_name = "Runbook: a failed backup"
      url          = "${local.runbooks}/platform.md#a-failed-backup"
    }
  }

  notification_channels = local.ticket_channels
}
