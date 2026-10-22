resource "google_cloud_run_v2_service" "service" {
  for_each = local.services
  name     = each.key
  location = var.region
  # Public services only through the load balancer, so Cloud Armor's rules always apply; the
  # worker only from Google (Cloud Tasks). Both still take Pub/Sub, Scheduler and Tasks, and
  # calls from the other services over the private network below.
  ingress             = each.value.public ? "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" : "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = false

  template {
    service_account                  = google_service_account.service[each.key].email
    timeout                          = "${each.value.timeout}s"
    max_instance_request_concurrency = each.value.concurrency

    scaling {
      min_instance_count = each.value.min
      max_instance_count = each.value.max
    }

    # All outgoing traffic goes through the private network: calls to the other services arrive
    # as internal, and the internet (OpenAI, Resend, Paddle, Upstash) through its NAT.
    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.id
        subnetwork = google_compute_subnetwork.run.id
      }
      egress = "ALL_TRAFFIC"
    }

    dynamic "volumes" {
      for_each = each.value.database == null ? [] : [1]

      content {
        name = "cloudsql"

        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }
    }

    containers {
      image   = "${local.registry}/${each.value.image}:${var.image_tag}"
      command = each.value.command

      ports {
        container_port = each.value.port
      }

      resources {
        limits = {
          cpu    = each.value.cpu
          memory = each.value.memory
        }
        # Billed per request: CPU only while a request runs, so idle services cost nothing.
        cpu_idle          = true
        startup_cpu_boost = true
      }

      dynamic "env" {
        for_each = merge(local.common_env, local.service_env[each.key])

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.secrets[each.key]

        content {
          name = env.value

          value_source {
            secret_key_ref {
              secret  = local.secret_ids[env.key]
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = each.value.database == null ? [] : [each.value.database]

        content {
          name = "DATABASE_URL"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url[env.value].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "volume_mounts" {
        for_each = each.value.database == null ? [] : [1]

        content {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      # The APIs answer /ready once their database does; the frontend only needs its port, as
      # its pages call the API through the load balancer. A cold start's first connection to the
      # database takes longer than the probe's default second.
      dynamic "startup_probe" {
        for_each = each.key == "frontend" ? [] : [1]

        content {
          http_get {
            path = "/ready"
          }
          timeout_seconds   = 4
          period_seconds    = 5
          failure_threshold = 24
        }
      }

      # Once started, an API that stops answering /health (the process alone, never the database,
      # or a database outage would restart every instance) for 90 s is restarted. Generous, so a
      # worker busy with generations isn't cut off.
      dynamic "liveness_probe" {
        for_each = each.key == "frontend" ? [] : [1]

        content {
          http_get {
            path = "/health"
          }
          timeout_seconds   = 5
          period_seconds    = 30
          failure_threshold = 3
        }
      }

      dynamic "startup_probe" {
        for_each = each.key == "frontend" ? [1] : []

        content {
          tcp_socket {
            port = each.value.port
          }
          period_seconds    = 5
          failure_threshold = 24
        }
      }
    }
  }

  # The deploy pipeline moves services to new images; Terraform leaves those alone.
  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }

  depends_on = [
    google_project_iam_member.service,
    google_secret_manager_secret_iam_member.service,
    google_compute_router_nat.main,
    google_secret_manager_secret_version.manual,
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_version.service_secret,
    google_secret_manager_secret_version.generated,
  ]
}

# Public services take requests from anyone (through the load balancer) and check users, or
# webhook signatures, themselves; the worker only from Google, as the invoker.
resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = { for name, service in local.services : name => service if service.public }
  name     = google_cloud_run_v2_service.service[each.key].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "invoker" {
  for_each = local.services
  name     = google_cloud_run_v2_service.service[each.key].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker.email}"
}

# Each service's migrations, run by the deploy pipeline before it updates the services.
resource "google_cloud_run_v2_job" "migrate" {
  for_each            = toset(local.databases)
  name                = "${each.value}-migrate"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.service[each.value].email
      max_retries     = 0

      volumes {
        name = "cloudsql"

        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }

      containers {
        image   = "${local.registry}/${each.value}:${var.image_tag}"
        command = ["alembic", "upgrade", "head"]

        # The same settings as the service: migrations load its configuration.
        dynamic "env" {
          for_each = merge(local.common_env, local.service_env[each.value])

          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = local.secrets[each.value]

          content {
            name = env.value

            value_source {
              secret_key_ref {
                secret  = local.secret_ids[env.key]
                version = "latest"
              }
            }
          }
        }

        env {
          name = "DATABASE_URL"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url[each.value].secret_id
              version = "latest"
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
}
