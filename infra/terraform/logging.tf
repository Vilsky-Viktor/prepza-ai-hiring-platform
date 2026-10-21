# Superadmins' use of the admin zone (prepza_common.superadmin logs every request by account id
# and route, never what it looked up): kept a year in a bucket whose retention is locked, so
# nobody, project owners included, can shorten it or delete the lines sooner. Locking is for
# good: Terraform can't delete or shorten this bucket afterwards. The _Default bucket keeps its
# own copy 30 days, as every log line.
resource "google_logging_project_bucket_config" "admin_access" {
  project        = var.project_id
  location       = "global"
  bucket_id      = "admin-access"
  retention_days = 365
  locked         = true
  description    = "Superadmins' use of the admin zone, kept a year, retention locked"
}

resource "google_logging_project_sink" "admin_access" {
  name                   = "admin-access"
  destination            = "logging.googleapis.com/${google_logging_project_bucket_config.admin_access.id}"
  filter                 = "resource.type=\"cloud_run_revision\" AND jsonPayload.logger=\"prepza_common.superadmin\""
  unique_writer_identity = true
}
