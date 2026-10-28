# The job that gives each service its own Postgres user owning only its own database. The deploy
# pipeline runs it before migrations; it's safe to repeat. Its account, alone, reads the admin's
# and every service's database URL.
resource "google_service_account" "db_admin" {
  account_id   = "prepza-db-admin"
  display_name = "prepza database users"
}

resource "google_project_iam_member" "db_admin" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.db_admin.email}"
}

resource "google_secret_manager_secret_iam_member" "db_admin" {
  for_each = merge(
    { admin = google_secret_manager_secret.database_admin_url.secret_id },
    { for name in local.databases : name => google_secret_manager_secret.database_url[name].secret_id },
  )
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.db_admin.email}"
}

resource "google_service_account_iam_member" "deploy_acts_as_db_admin" {
  service_account_id = google_service_account.db_admin.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_cloud_run_v2_job" "db_roles" {
  name                = "db-roles"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.db_admin.email
      max_retries     = 0

      volumes {
        name = "cloudsql"

        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }

      containers {
        image   = "${local.registry}/library:${var.image_tag}"
        command = ["python", "-m", "library.jobs.db_roles"]

        env {
          name = "ADMIN_DATABASE_URL"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_admin_url.secret_id
              version = "latest"
            }
          }
        }

        dynamic "env" {
          for_each = toset(local.databases)

          content {
            name = "DATABASE_URL_${upper(env.value)}"

            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.database_url[env.value].secret_id
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [
    google_project_iam_member.db_admin,
    google_secret_manager_secret_iam_member.db_admin,
    google_secret_manager_secret_version.database_admin_url,
    google_secret_manager_secret_version.database_url,
  ]
}
