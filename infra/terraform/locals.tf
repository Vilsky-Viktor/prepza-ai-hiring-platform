locals {
  registry = "${var.region}-docker.pkg.dev/${var.project_id}/prepza"

  # Cloud Run's deterministic address of a service, known before it exists, so services can
  # point at each other without a cycle.
  run_url = { for name in keys(local.services) : name => "https://${name}-${data.google_project.this.number}.${var.region}.run.app" }

  # Every service. `public` ones are reached through the load balancer at /api/<path>/ (or / for
  # the frontend); the others only by Google (Cloud Tasks, Scheduler, Pub/Sub) as the invoker.
  # `connections` is what one instance may open to Postgres (a pool of 5 plus 5 extra; generation
  # and the worker 4 more for LangGraph's checkpoints; notifications, ats, api and assistant 2 plus
  # 2), and `max` instances keep their total within the database's budget, even while a deploy
  # runs old and new instances side by side (see database.tf). The APIs with a pool of 10 take 40 requests at once per
  # instance, so a busy one scales out instead of queueing on its pool; the others 80, except
  # notifications-stream: it runs notifications' image only for the
  # bell's live stream (load_balancer.tf routes it there), where each open tab holds one request
  # for up to an hour, so those tabs never take the capacity Pub/Sub's pushes need. The worker
  # runs 10 generation jobs at once on each of its 2 instances: the 20 Cloud Tasks dispatches at
  # once (jobs.tf).
  services = {
    frontend             = { image = "frontend", public = true, path = null, port = 3000, min = 1, max = 10, connections = 0, cpu = "1", memory = "1Gi", timeout = 60, concurrency = 80, database = null, command = null }
    library              = { image = "library", public = true, path = "library", port = 8000, min = 0, max = 2, connections = 10, cpu = "1", memory = "512Mi", timeout = 150, concurrency = 40, database = "library", command = null }
    generation           = { image = "generation", public = true, path = "generate", port = 8000, min = 0, max = 1, connections = 14, cpu = "1", memory = "1Gi", timeout = 150, concurrency = 40, database = "generation", command = null }
    rounds               = { image = "rounds", public = true, path = "rounds", port = 8000, min = 1, max = 2, connections = 10, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 40, database = "rounds", command = null }
    companies            = { image = "companies", public = true, path = "companies", port = 8000, min = 0, max = 2, connections = 10, cpu = "1", memory = "512Mi", timeout = 150, concurrency = 40, database = "companies", command = null }
    billing              = { image = "billing", public = true, path = "billing", port = 8000, min = 0, max = 1, connections = 10, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 40, database = "billing", command = null }
    notifications        = { image = "notifications", public = true, path = "notifications", port = 8000, min = 0, max = 1, connections = 4, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "notifications", command = null }
    notifications-stream = { image = "notifications", public = true, path = null, port = 8000, min = 0, max = 2, connections = 4, cpu = "1", memory = "512Mi", timeout = 3600, concurrency = 500, database = "notifications", command = null }
    ats                  = { image = "ats", public = true, path = "ats", port = 8000, min = 0, max = 1, connections = 4, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "ats", command = null }
    # The public API at /api/v1/ (path "v1").
    api = { image = "api", public = true, path = "v1", port = 8000, min = 0, max = 1, connections = 4, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "api", command = null }
    # The in-app assistant: a turn streams up to 90 s while its tools call the other services. It
    # also serves AI apps over MCP at the site's root (mcp_paths below).
    assistant         = { image = "assistant", public = true, path = "assistant", port = 8000, min = 0, max = 2, connections = 4, cpu = "1", memory = "512Mi", timeout = 300, concurrency = 80, database = "assistant", command = null }
    generation-worker = { image = "generation", public = false, path = null, port = 8000, min = 0, max = 2, connections = 14, cpu = "1", memory = "2Gi", timeout = 1800, concurrency = 10, database = "generation", command = ["uvicorn", "app.worker_main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "8"] }
  }

  # AI apps' MCP endpoint and its OAuth authorization server, at the site's root; the load
  # balancer sends exactly these paths to the assistant (gateway/nginx.conf has the same list).
  mcp_paths = [
    "/mcp",
    "/authorize",
    "/token",
    "/register",
    "/revoke",
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/oauth-protected-resource/mcp",
  ]

  databases = ["library", "generation", "rounds", "companies", "billing", "notifications", "ats", "api", "assistant"]

  # Which services each one calls; it gets their keys, to sign tokens for them.
  calls = {
    frontend          = []
    library           = ["rounds", "generation", "companies", "billing", "notifications", "ats", "api", "assistant"]
    generation        = ["library", "notifications"]
    generation-worker = ["library", "notifications"]
    rounds            = ["library"]
    companies         = ["generation", "library", "rounds", "billing"]
    # companies' names and accounts' emails, for the AI costs tab.
    billing              = ["companies", "library"]
    notifications        = ["companies", "library", "billing", "generation"]
    notifications-stream = ["companies", "library"]
    ats                  = ["companies"]
    api                  = ["companies"]
    # Its X-Assistant header, so companies audits reads made through it as such; billing, whether
    # a company ever paid (its limits); api, checking an AI agent's API key at the MCP server;
    # notifications, ats and library, what get_updates reads (the bell, ATS candidates not
    # invited, questions flagged or fixed).
    assistant = ["companies", "billing", "api", "notifications", "ats", "library"]
  }

  # Each service's own key checks calls to it. The worker and the stream share generation's and
  # notifications' settings, so they get those keys too, though nothing calls them with it.
  own_key = {
    library              = "library"
    generation           = "generation"
    generation-worker    = "generation"
    rounds               = "rounds"
    companies            = "companies"
    billing              = "billing"
    notifications        = "notifications"
    notifications-stream = "notifications"
    ats                  = "ats"
    api                  = "api"
    assistant            = "assistant"
  }

  # Secrets each service reads (Secret Manager name => environment variable).
  base_secrets = {
    frontend             = { preview-secret = "PREVIEW_SECRET" }
    library              = { redis-url = "REDIS_URL" }
    generation           = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY" }
    generation-worker    = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY" }
    rounds               = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY", turnstile-secret-key = "TURNSTILE_SECRET_KEY" }
    companies            = { redis-url = "REDIS_URL", turnstile-secret-key = "TURNSTILE_SECRET_KEY" }
    billing              = { redis-url = "REDIS_URL", paddle-webhook-secret = "PADDLE_WEBHOOK_SECRET", paddle-api-key = "PADDLE_API_KEY" }
    notifications        = { redis-url = "REDIS_URL", email-link-secret = "EMAIL_LINK_SECRET", resend-api-key = "RESEND_API_KEY", resend-webhook-secret = "RESEND_WEBHOOK_SECRET", slack-client-id = "SLACK_CLIENT_ID", slack-client-secret = "SLACK_CLIENT_SECRET", slack-encryption-key = "SLACK_ENCRYPTION_KEY" }
    notifications-stream = { redis-url = "REDIS_URL", email-link-secret = "EMAIL_LINK_SECRET" }
    ats                  = { redis-url = "REDIS_URL", ats-encryption-key = "ATS_ENCRYPTION_KEY" }
    api                  = { redis-url = "REDIS_URL", api-encryption-key = "API_ENCRYPTION_KEY" }
    assistant            = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY" }
  }

  secrets = {
    for name, base in local.base_secrets : name => merge(
      base,
      { for callee in local.calls[name] : "service-secret-${callee}" => "${upper(callee)}_SERVICE_SECRET" },
      contains(keys(local.own_key), name) ? { "service-secret-${local.own_key[name]}" = "SERVICE_SECRET" } : {},
      # The backend services record funnel events.
      contains(keys(local.own_key), name) ? { analytics-salt = "ANALYTICS_SALT" } : {},
    )
  }
}
