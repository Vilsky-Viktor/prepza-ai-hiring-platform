# GitHub Actions reach Google Cloud without a stored key: GitHub's signed token for main or a
# version tag of this repository (checked by its numeric id) is exchanged for an account's (Workload
# Identity Federation): the deploy account only for the deploy workflow in the production
# environment (which needs the founder's approval), and an account that can only push images for
# every other job (CI).

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
    # "production" only for deploy.yml running in the production environment; "ci" otherwise.
    "attribute.deployer" = "('environment' in assertion && assertion.environment == 'production' && assertion.workflow_ref.startsWith(assertion.repository + '/.github/workflows/deploy.yml@')) ? 'production' : 'ci'"
  }

  # Only this repository's main branch (CI pushes images, a manual run rolls back) and its version
  # tags (deploys). Version tags are protected by a ruleset, so only admins can make them. The
  # repository and its owner are checked by their numeric ids, which a rename doesn't change and
  # nobody else can take over.
  attribute_condition = "assertion.repository_id == '${var.github_repository_id}' && assertion.repository_owner_id == '${var.github_repository_owner_id}' && (assertion.ref == 'refs/heads/main' || assertion.ref.startsWith('refs/tags/v'))"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# What the pipeline acts as: it pushes images, runs migrations and moves services to new images,
# and nothing else; infrastructure changes go through Terraform.
resource "google_service_account" "deploy" {
  account_id   = "prepza-deploy"
  display_name = "GitHub Actions deploys"
}

resource "google_service_account_iam_member" "github_is_deploy" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.deployer/production"
}

# What CI acts as: it pushes the images it built, and can't deploy them.
resource "google_service_account" "ci" {
  account_id   = "prepza-ci"
  display_name = "GitHub Actions CI (pushes images)"
}

resource "google_service_account_iam_member" "github_is_ci" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.deployer/ci"
}

resource "google_artifact_registry_repository_iam_member" "ci_pushes" {
  repository = google_artifact_registry_repository.images.name
  location   = var.region
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.ci.email}"
}

resource "google_project_iam_member" "deploy" {
  for_each = toset(["roles/run.developer"])
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_artifact_registry_repository_iam_member" "deploy_pushes" {
  repository = google_artifact_registry_repository.images.name
  location   = var.region
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.deploy.email}"
}

# Each service runs as its own account; deploying one (and running its migrations) means acting
# as it.
resource "google_service_account_iam_member" "deploy_acts_as_service" {
  for_each           = local.services
  service_account_id = google_service_account.service[each.key].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}
