# One Postgres instance holding each service's database. Cloud Run reaches it through the
# built-in Cloud SQL connector (a Unix socket), so it needs no private network.
resource "google_sql_database_instance" "main" {
  name = "testee"
  # The major version local development runs (database/Dockerfile).
  database_version = "POSTGRES_18"
  region           = var.region

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = var.db_high_availability ? "REGIONAL" : "ZONAL"
    # Google Cloud itself refuses to delete the instance (the console and gcloud too, not only
    # Terraform), and its backups outlive it if it's deleted anyway.
    deletion_protection_enabled = true
    retain_backups_on_delete    = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "02:00"
      # Point-in-time recovery reaches back this far; the daily backups, 14 days.
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 14
      }
    }

    # Google's updates restart the instance: Sundays at 03:00 UTC, the quietest time.
    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }

    # Only encrypted connections. The services, jobs and the Cloud SQL Auth Proxy (the restore
    # drill) connect through Google's connector, which is always encrypted, so all of them pass.
    ip_configuration {
      ssl_mode = "ENCRYPTED_ONLY"
    }

    database_flags {
      name  = "max_connections"
      value = tostring(local.db_max_connections)
    }

    insights_config {
      query_insights_enabled = true
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "service" {
  for_each = toset(local.databases)
  name     = each.value
  instance = google_sql_database_instance.main.name
}

resource "random_password" "database" {
  length  = 32
  special = false
}

# The instance's admin. No service uses it: only the db-roles job, which gives each service its
# own user owning only its own database (database/roles/src/db_roles.py).
resource "google_sql_user" "testee" {
  name     = "testee"
  instance = google_sql_database_instance.main.name
  password = random_password.database.result
}

resource "google_secret_manager_secret" "database_admin_url" {
  secret_id = "database-admin-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_admin_url" {
  secret      = google_secret_manager_secret.database_admin_url.id
  secret_data = "postgresql://testee:${random_password.database.result}@/postgres?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
}

# Each service's own Postgres user, named after its database; db-roles creates it.
resource "random_password" "service_database" {
  for_each = toset(local.databases)
  length   = 32
  special  = false
}

# Each service's connection string, as its own user, kept in Secret Manager.
resource "google_secret_manager_secret" "database_url" {
  for_each  = toset(local.databases)
  secret_id = "database-url-${each.value}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  for_each    = toset(local.databases)
  secret      = google_secret_manager_secret.database_url[each.value].id
  secret_data = "postgresql://${each.value}:${random_password.service_database[each.value].result}@/${each.value}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
}

locals {
  # What db-g1-small's memory (1.7 GB) supports, as Cloud SQL sets by default for it; a larger
  # tier comes with its own (and room for more instances).
  db_max_connections = 50
  # Kept free for the migrations and db-roles jobs (one connection each, one job at a time),
  # Cloud SQL's own superuser connections, Query Insights and an admin's session.
  db_reserved_connections = 10
  db_connections_at_peak  = sum([for service in local.services : service.max * service.connections])
  # A deploy (.github/workflows/deploy.yml) moves the services one at a time, after the migrations,
  # and each one's old instances run until their requests end. So on top of the peak: the old
  # instances of the services whose requests may last past the deploy (the worker's jobs, the
  # bell's streams) and of the largest other one.
  db_connections_in_deploy = local.db_connections_at_peak + sum([
    for service in local.services : service.max * service.connections if service.timeout > 300
    ]) + max([
    for service in local.services : service.max * service.connections if service.timeout <= 300
  ]...)
}

# Fails the plan if instance limits could open more connections than Postgres allows, at peak
# within the budget and during a deploy within max_connections; raise db_tier (and
# db_max_connections) or add PgBouncer before raising a service's `max`.
check "database_connections" {
  assert {
    condition     = local.db_connections_at_peak <= local.db_max_connections - local.db_reserved_connections
    error_message = "Services at their instance limits could open ${local.db_connections_at_peak} database connections; the budget is ${local.db_max_connections - local.db_reserved_connections}."
  }

  assert {
    condition     = local.db_connections_in_deploy <= local.db_max_connections
    error_message = "A deploy at the services' instance limits could open ${local.db_connections_in_deploy} database connections; Postgres allows ${local.db_max_connections}."
  }
}
