# Database alerts, by email like the others (monitoring.tf).

# Database connections: open connections past 80% of max_connections (database.tf), the sign to
# raise db_tier before a deploy at peak runs out of them.
resource "google_monitoring_alert_policy" "database_connections" {
  display_name = "prepza database connections high"
  combiner     = "OR"

  conditions {
    display_name = "Postgres connections above 80% of the limit"

    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\" AND resource.type=\"cloudsql_database\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = floor(local.db_max_connections * 0.8)

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_MAX"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.database_id"]
      }
    }
  }

  documentation {
    content   = "The database is near its connection limit. Raise db_tier (and db_max_connections) as infra/README.md describes, or lower services' max instances."
    mime_type = "text/markdown"
  }

  notification_channels = local.alert_channels
}

# Database CPU: busy above 80% for fifteen minutes.
resource "google_monitoring_alert_policy" "database_cpu" {
  display_name = "prepza database CPU high"
  combiner     = "OR"

  conditions {
    display_name = "Cloud SQL CPU above 80%"

    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\" AND resource.type=\"cloudsql_database\""
      duration        = "900s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  documentation {
    content   = "The database has been busy for a while. Check slow queries in Cloud SQL Query Insights, or raise db_tier."
    mime_type = "text/markdown"
  }

  notification_channels = local.alert_channels
}

# Database memory: above 90% for fifteen minutes, before Postgres starts failing queries.
resource "google_monitoring_alert_policy" "database_memory" {
  display_name = "prepza database memory high"
  combiner     = "OR"

  conditions {
    display_name = "Postgres memory above 90%"

    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/memory/utilization\" AND resource.type=\"cloudsql_database\""
      duration        = "900s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  documentation {
    content   = "The database is short of memory. Raise db_tier (infra/README.md) or look for heavy queries in Query Insights."
    mime_type = "text/markdown"
  }

  notification_channels = local.alert_channels
}

# Database disk: above 85% full. Storage grows by itself, but a fast fill means something writes too much.
resource "google_monitoring_alert_policy" "database_disk" {
  display_name = "prepza database disk filling"
  combiner     = "OR"

  conditions {
    display_name = "Postgres disk above 85% full"

    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/disk/utilization\" AND resource.type=\"cloudsql_database\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  documentation {
    content   = "The database disk is over 85% full. Check which tables grew (Query Insights) and the retention jobs; storage grows automatically, within its limit."
    mime_type = "text/markdown"
  }

  notification_channels = local.alert_channels
}

# Backups: a Cloud SQL backup run that failed, from its own error logs. The drill
# (scripts/ops/restore-drill.sh) proves the ones that succeed restore.
resource "google_monitoring_alert_policy" "database_backup_failed" {
  display_name = "prepza database backup failed"
  combiner     = "OR"

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
    content   = "A database backup failed. Check the instance's backups in Cloud SQL and start one by hand (gcloud sql backups create --instance=prepza). Google keeps a backup made by hand until someone deletes it: once the automated backups work again, delete it (gcloud sql backups delete <id> --instance=prepza), at most 14 days later, so backups last no longer than the privacy policy says."
    mime_type = "text/markdown"
  }

  notification_channels = local.alert_channels
}
