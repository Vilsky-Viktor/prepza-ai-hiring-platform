# Secrets you set yourself after the first apply (see README.md); they start as "set-me", and
# Terraform never overwrites what you set.
resource "google_secret_manager_secret" "manual" {
  for_each  = toset(["openai-api-key", "redis-url", "resend-api-key", "resend-webhook-secret", "paddle-webhook-secret", "paddle-api-key", "ats-encryption-key", "slack-client-id", "slack-client-secret", "slack-encryption-key", "api-encryption-key", "turnstile-secret-key"])
  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "manual" {
  for_each    = google_secret_manager_secret.manual
  secret      = each.value.id
  secret_data = "set-me"

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# The GitHub and LinkedIn sign-in apps' client secrets: Terraform makes each secret without a
# value; you add it once (README.md), and auth.tf reads it. Nothing secret goes through tfvars.
resource "google_secret_manager_secret" "sign_in" {
  for_each  = toset(["github-client-secret", "linkedin-client-secret"])
  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Secrets Terraform makes: each service's own key. Tokens calling a service are signed with its
# key and addressed to it, so a leaked key lets someone call one service, not all of them.
locals {
  keyed_services = ["library", "generation", "rounds", "companies", "billing", "notifications", "ats", "api", "assistant", "accounts"]
}

resource "random_password" "service_secret" {
  for_each = toset(local.keyed_services)
  length   = 48
  special  = false
}

resource "google_secret_manager_secret" "service_secret" {
  for_each  = toset(local.keyed_services)
  secret_id = "service-secret-${each.value}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "service_secret" {
  for_each    = toset(local.keyed_services)
  secret      = google_secret_manager_secret.service_secret[each.value].id
  secret_data = random_password.service_secret[each.value].result
}

# Secrets prepza makes itself, 48 random characters each:
# - analytics-salt salts the user ids in funnel events, so the table never holds a real id (see
#   analytics.py and analytics.tf);
# - preview-secret signs the titles the frontend's link-preview pictures draw, so /preview draws
#   only prepza's own;
# - email-link-secret signs the unsubscribe links in emails (notifications), so nobody can make one
#   for someone else;
# - person-hash-key keys the hashes that stand for a person (a candidate's opted-out or suppressed
#   address, a welcome gift's inbox), so nobody with a list of addresses can match them. Replacing
#   it orphans every stored hash (opt-outs would stop working): never rotate it without moving them.
locals {
  generated_secrets = toset(["analytics-salt", "preview-secret", "email-link-secret", "person-hash-key"])
}

resource "random_password" "generated" {
  for_each = local.generated_secrets
  length   = 48
  special  = false
}

resource "google_secret_manager_secret" "generated" {
  for_each  = local.generated_secrets
  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "generated" {
  for_each    = local.generated_secrets
  secret      = google_secret_manager_secret.generated[each.value].id
  secret_data = random_password.generated[each.value].result
}

moved {
  from = random_password.analytics_salt
  to   = random_password.generated["analytics-salt"]
}

moved {
  from = google_secret_manager_secret.analytics_salt
  to   = google_secret_manager_secret.generated["analytics-salt"]
}

moved {
  from = google_secret_manager_secret_version.analytics_salt
  to   = google_secret_manager_secret_version.generated["analytics-salt"]
}

moved {
  from = random_password.preview_secret
  to   = random_password.generated["preview-secret"]
}

moved {
  from = google_secret_manager_secret.preview_secret
  to   = google_secret_manager_secret.generated["preview-secret"]
}

moved {
  from = google_secret_manager_secret_version.preview_secret
  to   = google_secret_manager_secret_version.generated["preview-secret"]
}

moved {
  from = random_password.email_link_secret
  to   = random_password.generated["email-link-secret"]
}

moved {
  from = google_secret_manager_secret.email_link_secret
  to   = google_secret_manager_secret.generated["email-link-secret"]
}

moved {
  from = google_secret_manager_secret_version.email_link_secret
  to   = google_secret_manager_secret_version.generated["email-link-secret"]
}

moved {
  from = random_password.person_hash_key
  to   = random_password.generated["person-hash-key"]
}

moved {
  from = google_secret_manager_secret.person_hash_key
  to   = google_secret_manager_secret.generated["person-hash-key"]
}

moved {
  from = google_secret_manager_secret_version.person_hash_key
  to   = google_secret_manager_secret_version.generated["person-hash-key"]
}

locals {
  secret_ids = merge(
    { for name, secret in google_secret_manager_secret.manual : name => secret.secret_id },
    { for name in local.keyed_services : "service-secret-${name}" => google_secret_manager_secret.service_secret[name].secret_id },
    { for name in local.generated_secrets : name => google_secret_manager_secret.generated[name].secret_id },
  )
}
