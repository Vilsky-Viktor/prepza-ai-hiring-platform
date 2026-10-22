# One global address and HTTPS certificate for the domain. Google's edge ends connections close
# to each user and carries requests to the region on its own network.
resource "google_compute_global_address" "site" {
  name       = "prepza"
  depends_on = [google_project_service.apis]
}

resource "google_compute_managed_ssl_certificate" "site" {
  name = "prepza"

  managed {
    domains = [var.domain]
  }
}

# www. only redirects to the domain (the URL map below), with a certificate of its own: one
# certificate for both would stay inactive, the domain's included, until www's DNS points here.
resource "google_compute_managed_ssl_certificate" "www" {
  name = "prepza-www"

  managed {
    domains = ["www.${var.domain}"]
  }
}

locals {
  public_services = { for name, service in local.services : name => service if service.public }
}

resource "google_compute_region_network_endpoint_group" "service" {
  for_each              = local.public_services
  name                  = each.key
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = google_cloud_run_v2_service.service[each.key].name
  }
}

resource "google_compute_backend_service" "service" {
  for_each              = local.public_services
  name                  = each.key
  load_balancing_scheme = "EXTERNAL_MANAGED"
  protocol              = "HTTPS"
  security_policy       = google_compute_security_policy.edge.id
  # The frontend's static files (scripts, styles, fonts) are cached at Google's edge, and its
  # responses are compressed there, with Brotli for browsers that take it (the frontend itself
  # sends them uncompressed: next.config.ts `compress`).
  enable_cdn       = each.key == "frontend"
  compression_mode = each.key == "frontend" ? "AUTOMATIC" : null

  dynamic "cdn_policy" {
    for_each = each.key == "frontend" ? [1] : []

    content {
      cache_mode = "USE_ORIGIN_HEADERS"
    }
  }

  # The security headers the nginx gateway adds locally (gateway/nginx.conf); the frontend adds
  # its own Content-Security-Policy, whose frame-ancestors says who may frame a page (no one, but
  # a company's own site its embedded interview), so it gets no X-Frame-Options.
  # HSTS covers the subdomains too: any subdomain added later must serve HTTPS.
  custom_response_headers = concat(
    [
      "Strict-Transport-Security: max-age=31536000; includeSubDomains",
      "X-Content-Type-Options: nosniff",
      "Referrer-Policy: strict-origin-when-cross-origin",
      "Permissions-Policy: camera=(), microphone=(self), geolocation=()",
      "Cross-Origin-Opener-Policy: same-origin-allow-popups",
    ],
    each.key == "frontend" ? [] : ["X-Frame-Options: DENY"],
  )

  # The visitor's country (a two-letter code), which prices follow where no currency is saved;
  # it replaces any header of that name the visitor sent. gateway/nginx.conf has a stand-in
  # locally.
  custom_request_headers = ["X-Client-Country: {client_region}"]

  backend {
    group = google_compute_region_network_endpoint_group.service[each.key].id
  }
}

# /api/<path>/... goes to that service without the prefix, as the nginx gateway does locally;
# the bell's live stream to notifications-stream (locals.tf); AI apps' MCP endpoint and its
# OAuth paths at the root to the assistant; everything else to the frontend.
resource "google_compute_url_map" "site" {
  name            = "prepza"
  default_service = google_compute_backend_service.service["frontend"].id

  host_rule {
    hosts        = ["www.${var.domain}"]
    path_matcher = "www"
  }

  host_rule {
    hosts        = ["*"]
    path_matcher = "routes"
  }

  path_matcher {
    name = "www"

    default_url_redirect {
      host_redirect          = var.domain
      https_redirect         = true
      strip_query            = false
      redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    }
  }

  path_matcher {
    name            = "routes"
    default_service = google_compute_backend_service.service["frontend"].id

    # Before notifications' own prefix below.
    route_rules {
      priority = 1
      service  = google_compute_backend_service.service["notifications-stream"].id

      match_rules {
        prefix_match = "/api/notifications/me/stream"
      }

      route_action {
        url_rewrite {
          path_prefix_rewrite = "/me/stream"
        }
      }
    }

    # AI apps (Claude, ChatGPT, ...): the assistant's MCP endpoint and its OAuth authorization
    # server, at the root, as they are. Exact paths only, so no frontend page is taken
    # (gateway/nginx.conf has the same list).
    route_rules {
      priority = 100
      service  = google_compute_backend_service.service["assistant"].id

      dynamic "match_rules" {
        for_each = local.mcp_paths

        content {
          full_path_match = match_rules.value
        }
      }
    }

    dynamic "route_rules" {
      for_each = { for name, service in local.public_services : name => service if service.path != null }

      content {
        priority = index(keys(local.public_services), route_rules.key) + 2
        service  = google_compute_backend_service.service[route_rules.key].id

        match_rules {
          prefix_match = "/api/${route_rules.value.path}/"
        }

        route_action {
          url_rewrite {
            path_prefix_rewrite = "/"
          }
        }
      }
    }
  }
}

# TLS 1.2 or later with modern ciphers only: without a policy Google's default profile still
# offers TLS 1.0 and 1.1.
resource "google_compute_ssl_policy" "modern" {
  name            = "prepza-modern-tls"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}

resource "google_compute_target_https_proxy" "site" {
  name             = "prepza"
  url_map          = google_compute_url_map.site.id
  ssl_certificates = [google_compute_managed_ssl_certificate.site.id, google_compute_managed_ssl_certificate.www.id]
  ssl_policy       = google_compute_ssl_policy.modern.id
}

resource "google_compute_global_forwarding_rule" "https" {
  name                  = "prepza-https"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.site.id
  port_range            = "443"
  target                = google_compute_target_https_proxy.site.id
}

# Plain HTTP redirects to HTTPS.
resource "google_compute_url_map" "redirect" {
  name = "prepza-redirect"

  default_url_redirect {
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

resource "google_compute_target_http_proxy" "redirect" {
  name    = "prepza-redirect"
  url_map = google_compute_url_map.redirect.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "prepza-http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.site.id
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
}
