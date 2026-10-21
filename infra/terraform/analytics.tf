# The business funnel (internal_docs/business/measurement.md): services publish funnel.* events to the events
# topic, and a BigQuery subscription writes them into a table, without code of ours.
resource "google_bigquery_dataset" "analytics" {
  dataset_id = "analytics"
  location   = var.region

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_table" "funnel_events" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "funnel_events"

  # A day per partition, each kept 25 months (761 days, never more, as the privacy policy says):
  # enough to compare a year with the one before.
  time_partitioning {
    type          = "DAY"
    field         = "publish_time"
    expiration_ms = 761 * 24 * 60 * 60 * 1000
  }

  # The columns a BigQuery subscription writes with its metadata; `data` is the event's JSON
  # and `attributes.type` its name.
  schema = jsonencode([
    { name = "subscription_name", type = "STRING" },
    { name = "message_id", type = "STRING" },
    { name = "publish_time", type = "TIMESTAMP" },
    { name = "data", type = "JSON" },
    { name = "attributes", type = "JSON" },
  ])
}

resource "google_bigquery_dataset_iam_member" "pubsub_writer" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pubsub_agent
}

resource "google_pubsub_subscription" "funnel" {
  name   = "funnel-to-bigquery"
  topic  = google_pubsub_topic.events.id
  filter = "hasPrefix(attributes.type, \"${local.funnel_prefix}\")"

  bigquery_config {
    table          = "${var.project_id}.${google_bigquery_dataset.analytics.dataset_id}.${google_bigquery_table.funnel_events.table_id}"
    write_metadata = true
  }

  expiration_policy {
    ttl = ""
  }

  depends_on = [google_bigquery_dataset_iam_member.pubsub_writer]
}

# Salts the user ids in funnel events, so the table never holds a real id (see analytics.py).
resource "random_password" "analytics_salt" {
  length  = 48
  special = false
}

resource "google_secret_manager_secret" "analytics_salt" {
  secret_id = "analytics-salt"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "analytics_salt" {
  secret      = google_secret_manager_secret.analytics_salt.id
  secret_data = random_password.analytics_salt.result
}

locals {
  # Matches FUNNEL_PREFIX in prepza_common.constants.
  funnel_prefix = "funnel."
}
