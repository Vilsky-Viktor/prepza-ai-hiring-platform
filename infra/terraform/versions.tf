terraform {
  # Terraform 1.x from 1.9 on; CI runs the version pinned in .github/workflows/ci.yml.
  required_version = "~> 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # The state lives in a Cloud Storage bucket created during bootstrap (see README.md):
  # terraform init -backend-config="bucket=<project>-terraform"
  backend "gcs" {
    prefix = "prepza"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "this" {}
