locals {
  registry = "${var.region}-docker.pkg.dev/${var.project_id}/prepza"

  # Cloud Run's deterministic address of a service, known before it exists, so services can
  # point at each other without a cycle.
  run_url = { for name in keys(local.services) : name => "https://${name}-${data.google_project.this.number}.${var.region}.run.app" }

  # Every service. `public` ones are reached through the load balancer at /api/<path>/ (or / for
  # the frontend); the others only by Google (Cloud Tasks, Scheduler, Pub/Sub) as the invoker.
  # `connections` is what one instance may open to Postgres: a pool of 2 plus 1 extra
  # (prepza_common's DB_POOL_SIZE and DB_MAX_OVERFLOW); 1 plus 1 for notifications, ats, api,
  # the assistant and generation, which with its worker keeps 2 more for LangGraph's checkpoints
  # (CHECKPOINTER_POOL_SIZE); 1 alone for accounts and site, whose requests mostly wait on other
  # services or read files. `max` instances keep the total within the database's budget, even
  # while a deploy runs old and new instances side by side (see database.tf): db-g1-small's 50
  # connections, so most services run on one instance and rounds and companies on two. The APIs
  # take 40 requests at once per instance (the others 80) and queue briefly on their small pool;
  # a larger tier comes before larger pools or more instances. notifications-stream runs
  # notifications' image only for the bell's live stream (load_balancer.tf routes it there),
  # where each open tab holds one request for up to an hour, so those tabs never take the
  # capacity Pub/Sub's pushes need. The worker runs 10 generation jobs at once on its one
  # instance: the 10 Cloud Tasks dispatches at once (jobs.tf). Services that pages ask on most
  # visits (frontend, rounds, companies, library, billing, generation) keep one warm instance,
  # so no visitor waits for a 3-6 s cold start; an idle one costs about $10 a month.
  services = {
    frontend             = { image = "frontend", public = true, path = null, port = 3000, min = 1, max = 10, connections = 0, cpu = "1", memory = "1Gi", timeout = 60, concurrency = 80, database = null, command = null }
    library              = { image = "library", public = true, path = "library", port = 8000, min = 1, max = 1, connections = 3, cpu = "1", memory = "512Mi", timeout = 150, concurrency = 40, database = "library", command = null }
    generation           = { image = "generation", public = true, path = "generate", port = 8000, min = 1, max = 1, connections = 4, cpu = "1", memory = "1Gi", timeout = 150, concurrency = 40, database = "generation", command = null }
    rounds               = { image = "rounds", public = true, path = "rounds", port = 8000, min = 1, max = 2, connections = 3, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 40, database = "rounds", command = null }
    companies            = { image = "companies", public = true, path = "companies", port = 8000, min = 1, max = 2, connections = 3, cpu = "1", memory = "512Mi", timeout = 150, concurrency = 40, database = "companies", command = null }
    billing              = { image = "billing", public = true, path = "billing", port = 8000, min = 1, max = 1, connections = 3, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 40, database = "billing", command = null }
    notifications        = { image = "notifications", public = true, path = "notifications", port = 8000, min = 0, max = 1, connections = 2, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "notifications", command = null }
    notifications-stream = { image = "notifications", public = true, path = null, port = 8000, min = 0, max = 1, connections = 2, cpu = "1", memory = "512Mi", timeout = 3600, concurrency = 500, database = "notifications", command = null }
    ats                  = { image = "ats", public = true, path = "ats", port = 8000, min = 0, max = 1, connections = 2, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "ats", command = null }
    # The public API at /api/v1/ (path "v1").
    api = { image = "api", public = true, path = "v1", port = 8000, min = 0, max = 1, connections = 2, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "api", command = null }
    # The in-app assistant: a turn streams up to 90 s while its tools call the other services. It
    # also serves AI apps over MCP at the site's root (mcp_paths below) and the help chat for
    # visitors, which streams within the same TURNS_AT_ONCE.
    assistant = { image = "assistant", public = true, path = "assistant", port = 8000, min = 0, max = 1, connections = 2, cpu = "1", memory = "512Mi", timeout = 300, concurrency = 80, database = "assistant", command = null }
    # Users' accounts: the account page's data, email settings, accepted terms, and deleting or
    # downloading an account across every service (each call up to a minute, two at a time). Pages
    # ask it in the background (the user menu), so it starts cold.
    accounts = { image = "accounts", public = true, path = "accounts", port = 8000, min = 0, max = 1, connections = 1, cpu = "1", memory = "512Mi", timeout = 150, concurrency = 80, database = "accounts", command = null }
    # The site's content: the FAQ, page guides, guide articles, legal texts, the contact form and
    # news. Mostly files baked into its image; its database holds only news and its events, so one
    # connection does.
    site              = { image = "site", public = true, path = "site", port = 8000, min = 0, max = 1, connections = 1, cpu = "1", memory = "512Mi", timeout = 60, concurrency = 80, database = "site", command = null }
    generation-worker = { image = "generation", public = false, path = null, port = 8000, min = 0, max = 1, connections = 4, cpu = "1", memory = "2Gi", timeout = 1800, concurrency = 10, database = "generation", command = ["uvicorn", "generation.worker_main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--timeout-graceful-shutdown", "8"] }
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

  # A company's payments, under /api/companies/companies/{id}/: billing's routes, which check the
  # member themselves, kept at companies' addresses (load_balancer.tf; gateway/nginx.conf has
  # the same list).
  company_billing_paths = [
    "billing/catalog",
    "billing/currency",
    "billing/checkout",
    "billing/invoice",
    "billing/payment-failure",
    "auto-top-up",
    "auto-top-up/card",
  ]

  # Users' accounts under /api/library/: accounts' routes, kept at the addresses library had
  # (load_balancer.tf; gateway/nginx.conf has the same list). Each is a path prefix: "me" takes
  # /me and everything under it (no other library route starts so).
  account_paths = [
    "me",
    "superadmin/emails/",
    "superadmin/stats",
  ]

  # The site's content under /api/<service>/: site's routes, kept at the addresses rounds and
  # library had (load_balancer.tf; gateway/nginx.conf has the same list). Each path is a prefix:
  # "help/guide" takes the platform guide and the guide articles, "news" only /news (no other
  # library route starts so); site serves each at the same path.
  site_paths = [
    { from = "rounds", path = "help/faq" },
    { from = "rounds", path = "help/guide" },
    { from = "rounds", path = "help/pages/" },
    { from = "rounds", path = "help/legal/" },
    { from = "rounds", path = "help/contact" },
    { from = "library", path = "news" },
    { from = "library", path = "superadmin/news" },
  ]

  databases = ["library", "generation", "rounds", "companies", "billing", "notifications", "ats", "api", "assistant", "accounts", "site"]

  # Which services each one calls; it gets their keys, to sign tokens for them.
  calls = {
    frontend = []
    library  = ["generation"]
    # site: the news posts it translates.
    generation        = ["library", "notifications", "site"]
    generation-worker = ["library", "notifications", "site"]
    rounds            = ["library"]
    companies         = ["generation", "library", "rounds", "billing", "accounts"]
    # companies' names and accounts' emails, for the AI costs tab.
    billing = ["companies", "accounts"]
    # rounds: a campaign's candidates and learners; site, the news the bell names (library, which
    # had them, for one release while the version before still asks it).
    notifications        = ["companies", "library", "billing", "generation", "rounds", "accounts", "site"]
    notifications-stream = ["companies", "library", "accounts", "site"]
    ats                  = ["companies"]
    api                  = ["companies"]
    # Its X-Assistant header, so companies audits reads made through it as such; billing, whether
    # a company ever paid (its limits); api, checking an AI agent's API key at the MCP server;
    # notifications, ats and library, what get_updates reads (the bell, ATS candidates not
    # invited, questions flagged or fixed); rounds, a user's practice rounds; site, what the help
    # chat answers from and the FAQ, guides and news its tools read.
    assistant = ["companies", "billing", "api", "notifications", "ats", "library", "rounds", "accounts", "site"]
    # Every service holding part of a user's data, for deleting and downloading an account;
    # billing also sets a new account's currency.
    accounts = ["companies", "rounds", "generation", "billing", "notifications", "ats", "api", "assistant", "library", "site"]
    # generation: translating news posts.
    site = ["generation"]
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
    accounts             = "accounts"
    site                 = "site"
  }

  # Secrets each service reads (Secret Manager name => environment variable).
  base_secrets = {
    frontend             = { preview-secret = "PREVIEW_SECRET" }
    library              = { redis-url = "REDIS_URL" }
    generation           = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY" }
    generation-worker    = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY" }
    rounds               = { redis-url = "REDIS_URL" }
    companies            = { redis-url = "REDIS_URL", person-hash-key = "PERSON_HASH_KEY", turnstile-secret-key = "TURNSTILE_SECRET_KEY" }
    billing              = { redis-url = "REDIS_URL", person-hash-key = "PERSON_HASH_KEY", paddle-webhook-secret = "PADDLE_WEBHOOK_SECRET", paddle-api-key = "PADDLE_API_KEY" }
    notifications        = { redis-url = "REDIS_URL", email-link-secret = "EMAIL_LINK_SECRET", person-hash-key = "PERSON_HASH_KEY", resend-api-key = "RESEND_API_KEY", resend-webhook-secret = "RESEND_WEBHOOK_SECRET", slack-client-id = "SLACK_CLIENT_ID", slack-client-secret = "SLACK_CLIENT_SECRET", slack-encryption-key = "SLACK_ENCRYPTION_KEY" }
    notifications-stream = { redis-url = "REDIS_URL", email-link-secret = "EMAIL_LINK_SECRET", person-hash-key = "PERSON_HASH_KEY" }
    ats                  = { redis-url = "REDIS_URL", ats-encryption-key = "ATS_ENCRYPTION_KEY" }
    api                  = { redis-url = "REDIS_URL", api-encryption-key = "API_ENCRYPTION_KEY" }
    accounts             = { redis-url = "REDIS_URL" }
    site                 = { redis-url = "REDIS_URL", turnstile-secret-key = "TURNSTILE_SECRET_KEY" }
    assistant            = { redis-url = "REDIS_URL", openai-api-key = "OPENAI_API_KEY", turnstile-secret-key = "TURNSTILE_SECRET_KEY" }
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
