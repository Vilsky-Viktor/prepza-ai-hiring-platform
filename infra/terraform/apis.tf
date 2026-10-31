resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "billingbudgets.googleapis.com",
    "bigquery.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudtasks.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "identitytoolkit.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Released versions (v* tags) are kept, so a rollback always finds its images, and so are each
# image's 10 newest, which CI tags the unchanged ones from; the rest go after 30 days. Tags stay
# mutable: Artifact Registry can't delete images with immutable tags, and every image has its
# commit's tag. A version tag doesn't move, as deploy.yml only adds it and git protects v* tags.
resource "google_artifact_registry_repository" "images" {
  repository_id = "testee"
  format        = "DOCKER"
  location      = var.region

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"

    condition {
      tag_state  = "ANY"
      older_than = "2592000s"
    }
  }

  cleanup_policies {
    id     = "keep-versions"
    action = "KEEP"

    condition {
      tag_state    = "TAGGED"
      tag_prefixes = ["v"]
    }
  }

  cleanup_policies {
    id     = "keep-newest"
    action = "KEEP"

    most_recent_versions {
      keep_count = 10
    }
  }

  depends_on = [google_project_service.apis]
}
