resource "google_pubsub_topic" "events" {
  name       = "events"
  depends_on = [google_project_service.apis]
}

# Events a consumer kept failing on; kept 7 days for a look or a replay (the pull subscription
# below; infra/README.md, Notes).
resource "google_pubsub_topic" "dead_letter" {
  name       = "events-dead-letter"
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_subscription" "dead_letter" {
  name                       = "events-dead-letter"
  topic                      = google_pubsub_topic.dead_letter.id
  message_retention_duration = "604800s"

  # Pulled only during a replay: without this, Pub/Sub deletes it after 31 idle days, and dead
  # letters (and their alert) are lost.
  expiration_policy {
    ttl = ""
  }
}

# The event types each consumer handles (the table in its src/<service>/handlers/dispatch.py).
# A consumer that starts handling a new type needs it added here. Changing a filter replaces the
# subscription, dropping the messages it still holds: apply when its backlog is empty. Funnel
# events go only to BigQuery (analytics.tf).
# Pub/Sub caps a filter at 256 bytes (scripts/tests/test_pubsub_filters.py checks each): a type
# adds 24 bytes plus its name. An entry ending in ".*" is a whole family, every type up to its
# first dot, matched on the event's `family` attribute (prepza_common.events.pubsub) in 25 bytes plus the
# family's name: notifications and api take all "candidate." events that way, as listing them one
# by one outgrew the cap, and ignore the ones they don't handle. A family of one type today
# (company, contact, member, report, credits) is taken whole to save bytes; a consumer ignores any
# type of it it doesn't handle. Companies takes `audit.recorded`, members' actions in billing,
# ats, notifications and api, for the company's action log. Notifications and ats take their own
# families too (email, ats): a web hook received is recorded as an event, and its work runs from
# it. A new consumer's subscription is created on apply and gets only the events published after
# that.
locals {
  consumes = {
    library       = ["answer.recorded", "session.scored", "guests.deleted", "question.fixed", "interview.deleted", "company.deleted"]
    rounds        = ["interview.deleted", "company.deleted"]
    companies     = ["generation.completed", "generation.failed", "generation.cancelled", "interview.finished", "audit.recorded"]
    notifications = ["notification.requested", "candidate.*", "member.*", "report.*", "contact.*", "company.*", "email.*"]
    ats           = ["candidate.finished", "candidate.removed", "interview.ready", "interview.deleted", "company.*", "credits.*", "ats.*"]
    api           = ["candidate.*", "interview.ready", "company.deleted"]
    assistant     = ["company.deleted", "candidate.removed", "candidate.interview_deleted"]
    # Every AI call and limit hit, stored for the admin zone's AI costs tab.
    billing = ["ai.used", "limit.hit"]
  }
}

# Each consumer gets its event types pushed to its /internal/events, signed as the invoker.
resource "google_pubsub_subscription" "push" {
  for_each = local.consumes
  name     = "${each.key}-events"
  topic    = google_pubsub_topic.events.id
  filter = join(" OR ", [
    for type in each.value : endswith(type, ".*")
    ? "attributes.family = \"${trimsuffix(type, ".*")}\""
    : "attributes.type = \"${type}\""
  ])

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = "${local.run_url[each.key]}/internal/events"

    oidc_token {
      service_account_email = google_service_account.invoker.email
      audience              = local.run_url[each.key]
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # 50 attempts, backing off up to 10 minutes, ride out several hours of downstream trouble
  # before a message is dead-lettered (monitoring.tf alerts on that).
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 50
  }

  expiration_policy {
    ttl = ""
  }
}

# Pub/Sub moves dead letters itself: it publishes to the dead-letter topic and acknowledges the
# original.
locals {
  pubsub_agent = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dead_letter_publisher" {
  topic  = google_pubsub_topic.dead_letter.id
  role   = "roles/pubsub.publisher"
  member = local.pubsub_agent
}

resource "google_pubsub_subscription_iam_member" "dead_letter_subscriber" {
  for_each     = google_pubsub_subscription.push
  subscription = each.value.id
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_agent
}
