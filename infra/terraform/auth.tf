# Ways to sign in besides Google (which Firebase has on by default): GitHub, and LinkedIn through
# OpenID Connect. Each is created only once its client id is set, from the apps you register
# (see README.md). LinkedIn needs the project upgraded to Identity Platform first. One account
# per email stays Firebase's default, so the frontend links a new way to an existing account.
# Their client secrets live in Secret Manager (secrets.tf: you add each value once), read here:
# Identity Platform takes the value itself, so it still lands in the encrypted Terraform state.
data "google_secret_manager_secret_version" "github_client_secret" {
  count  = var.github_client_id == "" ? 0 : 1
  secret = google_secret_manager_secret.sign_in["github-client-secret"].id
}

data "google_secret_manager_secret_version" "linkedin_client_secret" {
  count  = var.linkedin_client_id == "" ? 0 : 1
  secret = google_secret_manager_secret.sign_in["linkedin-client-secret"].id
}

resource "google_identity_platform_default_supported_idp_config" "github" {
  count         = var.github_client_id == "" ? 0 : 1
  project       = var.project_id
  idp_id        = "github.com"
  client_id     = var.github_client_id
  client_secret = data.google_secret_manager_secret_version.github_client_secret[0].secret_data
  enabled       = true

  depends_on = [google_project_service.apis]
}

resource "google_identity_platform_oauth_idp_config" "linkedin" {
  count         = var.linkedin_client_id == "" ? 0 : 1
  project       = var.project_id
  name          = "oidc.linkedin"
  display_name  = "LinkedIn"
  issuer        = "https://www.linkedin.com/oauth"
  client_id     = var.linkedin_client_id
  client_secret = data.google_secret_manager_secret_version.linkedin_client_secret[0].secret_data
  enabled       = true

  # LinkedIn signs in with the authorization code flow, which needs the client secret.
  response_type {
    code     = true
    id_token = false
  }

  depends_on = [google_project_service.apis]
}
