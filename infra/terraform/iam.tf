# Each service runs as its own account, with only what it uses: its own secrets, its own
# database, publishing events, and (generation only) queuing tasks. The frontend has none. So a
# flaw in one service can't read another's keys or the payment and AI keys.
resource "google_service_account" "service" {
  for_each     = local.services
  account_id   = "testee-${each.key}"
  display_name = "testee ${each.key}"
}

# What Google signs as when it calls our services: Pub/Sub pushes, Cloud Tasks, Cloud Scheduler.
# Services admit only its tokens on /internal/events, /internal/jobs and /internal/schedules.
resource "google_service_account" "invoker" {
  account_id   = "testee-invoker"
  display_name = "Pub/Sub, Cloud Tasks and Scheduler calling testee"
}

locals {
  # Project roles each service needs: Cloud SQL for those with a database, Pub/Sub for the
  # backend services (the outbox and funnel events), Cloud Tasks for the generation services.
  service_roles = merge([
    for name, service in local.services : merge(
      service.database == null ? {} : { "${name}/cloudsql.client" = { service = name, role = "roles/cloudsql.client" } },
      contains(keys(local.own_key), name) ? { "${name}/pubsub.publisher" = { service = name, role = "roles/pubsub.publisher" } } : {},
      contains(local.task_services, name) ? { "${name}/cloudtasks.enqueuer" = { service = name, role = "roles/cloudtasks.enqueuer" } } : {},
    )
  ]...)

  # The services that queue generation jobs and verifier checks.
  task_services = ["generation", "generation-worker"]

  # Each secret a service reads, granted on that secret alone: its keys, and its database's URL.
  secret_grants = merge([
    for name, service in local.services : merge(
      { for secret in keys(local.secrets[name]) : "${name}/${secret}" => { service = name, secret = local.secret_ids[secret] } },
      service.database == null ? {} : {
        "${name}/database-url" = { service = name, secret = google_secret_manager_secret.database_url[service.database].secret_id }
      },
    )
  ]...)
}

resource "google_project_iam_member" "service" {
  for_each = local.service_roles
  project  = var.project_id
  role     = each.value.role
  member   = "serviceAccount:${google_service_account.service[each.value.service].email}"
}

resource "google_secret_manager_secret_iam_member" "service" {
  for_each  = local.secret_grants
  secret_id = each.value.secret
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.service[each.value.service].email}"
}

# Creating a Cloud Task that carries the invoker's token requires acting as the invoker; only the
# services that queue tasks may.
resource "google_service_account_iam_member" "queues_as_invoker" {
  for_each           = toset(local.task_services)
  service_account_id = google_service_account.invoker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.service[each.value].email}"
}

# Pub/Sub signs push requests as the invoker.
resource "google_service_account_iam_member" "pubsub_signs_as_invoker" {
  service_account_id = google_service_account.invoker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# AI apps connected over MCP call the other services as the user: the assistant reads the
# Firebase account (refusing deleted or disabled ones) and signs a custom token for it, which
# Firebase exchanges for the user's ID token. Signing a custom token without a key file is IAM's
# signBlob on its own account (the iamcredentials API, apis.tf).
resource "google_project_iam_member" "assistant_reads_accounts" {
  project = var.project_id
  role    = "roles/firebaseauth.viewer"
  member  = "serviceAccount:${google_service_account.service["assistant"].email}"
}

# Accounts manages users' sign-ins: sets their language, looks them up for other services and
# the admin zone, counts them for the stats, and deletes them with their account or guest invite.
resource "google_project_iam_member" "accounts_manages_sign_ins" {
  project = var.project_id
  role    = "roles/firebaseauth.admin"
  member  = "serviceAccount:${google_service_account.service["accounts"].email}"
}

# Only signBlob, which signing a custom token needs: roles/iam.serviceAccountTokenCreator would
# also let the account mint access and ID tokens as itself.
resource "google_project_iam_custom_role" "token_signer" {
  project     = var.project_id
  role_id     = "testeeTokenSigner"
  title       = "testee token signer"
  description = "Signs Firebase custom tokens with the service account's own key (signBlob only)."
  permissions = ["iam.serviceAccounts.signBlob"]
}

resource "google_service_account_iam_member" "assistant_signs_custom_tokens" {
  service_account_id = google_service_account.service["assistant"].name
  role               = google_project_iam_custom_role.token_signer.id
  member             = "serviceAccount:${google_service_account.service["assistant"].email}"
}

# A candidate a company's own platform sends through the API without a sign-in opens the
# interview from its link alone: companies signs a custom token for the invite's guest (signBlob
# on its own account), and Firebase makes the guest's account on its first sign-in.
resource "google_service_account_iam_member" "companies_signs_guest_tokens" {
  service_account_id = google_service_account.service["companies"].name
  role               = google_project_iam_custom_role.token_signer.id
  member             = "serviceAccount:${google_service_account.service["companies"].email}"
}
