locals {
  # Every service gets these.
  common_env = {
    GOOGLE_CLOUD_PROJECT    = var.project_id
    FIREBASE_PROJECT_ID     = var.project_id
    BACKEND_SENTRY_DSN      = var.backend_sentry_dsn
    SUPERADMIN_EMAILS       = join(",", var.superadmin_emails)
    ENVIRONMENT             = "production"
    INVOKER_SERVICE_ACCOUNT = google_service_account.invoker.email
    LIBRARY_URL             = local.run_url["library"]
    GENERATION_URL          = local.run_url["generation"]
    ROUNDS_URL              = local.run_url["rounds"]
    COMPANIES_URL           = local.run_url["companies"]
    BILLING_URL             = local.run_url["billing"]
    NOTIFICATIONS_URL       = local.run_url["notifications"]
    ATS_URL                 = local.run_url["ats"]
    ACCOUNTS_URL            = local.run_url["accounts"]
  }

  # And each service its own; INVOKER_AUDIENCE is the service's address, which Google's signed
  # tokens are issued for.
  service_env = {
    frontend = {
      API_URL                  = "https://${var.domain}"
      SITE_URL                 = "https://${var.domain}"
      GOOGLE_SITE_VERIFICATION = var.google_site_verification
      BING_SITE_VERIFICATION   = var.bing_site_verification
    }
    library = {
      INVOKER_AUDIENCE = local.run_url["library"]
      # The api service (not common: the frontend's API_URL is the site itself).
      API_URL       = local.run_url["api"]
      ASSISTANT_URL = local.run_url["assistant"]
    }
    generation = {
      INVOKER_AUDIENCE = local.run_url["generation"]
      WORKER_URL       = local.run_url["generation-worker"]
      TASKS_QUEUE      = google_cloud_tasks_queue.generation.id
    }
    generation-worker = {
      INVOKER_AUDIENCE = local.run_url["generation-worker"]
      WORKER_URL       = local.run_url["generation-worker"]
      TASKS_QUEUE      = google_cloud_tasks_queue.generation.id
    }
    rounds = {
      INVOKER_AUDIENCE = local.run_url["rounds"]
    }
    companies = {
      INVOKER_AUDIENCE = local.run_url["companies"]
    }
    billing = merge(
      {
        INVOKER_AUDIENCE          = local.run_url["billing"]
        PADDLE_ENVIRONMENT        = var.paddle_environment
        PADDLE_CLIENT_TOKEN       = var.paddle_client_token
        PADDLE_PRODUCT_CANDIDATES = var.paddle_product_candidates
      },
      { for key, price in var.paddle_prices : "PADDLE_PRICE_${upper(key)}" => price },
    )
    notifications = {
      INVOKER_AUDIENCE     = local.run_url["notifications"]
      SITE_URL             = "https://${var.domain}"
      MAIL_FROM            = var.mail_from
      MAIL_FROM_UPDATES    = var.mail_from_updates
      MAIL_FROM_CANDIDATES = var.mail_from_candidates
    }
    notifications-stream = {
      INVOKER_AUDIENCE = local.run_url["notifications-stream"]
      SITE_URL         = "https://${var.domain}"
    }
    ats = {
      INVOKER_AUDIENCE = local.run_url["ats"]
      SITE_URL         = "https://${var.domain}"
    }
    api = {
      INVOKER_AUDIENCE = local.run_url["api"]
      SITE_URL         = "https://${var.domain}"
    }
    accounts = {
      INVOKER_AUDIENCE = local.run_url["accounts"]
    }
    assistant = {
      INVOKER_AUDIENCE = local.run_url["assistant"]
      # Its tools read the api service's settings page too.
      API_URL = local.run_url["api"]
      # AI apps connect to <SITE_URL>/mcp; their calls sign the user in with Firebase's public
      # web key.
      SITE_URL             = "https://${var.domain}"
      FIREBASE_WEB_API_KEY = var.firebase_web_api_key
    }
  }
}
