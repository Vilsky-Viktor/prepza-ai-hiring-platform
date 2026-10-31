# Cloud Armor at the edge: blocks service-to-service routes, as the nginx gateway does locally (the
# services check those callers' tokens as well), and limits requests per IP.
resource "google_compute_security_policy" "edge" {
  name = "testee-edge"

  rule {
    action      = "deny(404)"
    priority    = 1000
    description = "No /internal routes from the internet"

    match {
      expr {
        # Decoded and lowercased, so /api/x/%69nternal/ or doubled slashes don't slip past.
        expression = "request.path.urlDecode().lower().matches('^/+api/+[^/]+/+internal(/|$)')"
      }
    }
  }

  # The help chat (the assistant's) is open to visitors; each IP gets 20 questions per 10
  # minutes, so one visitor can't run up its model costs. The service also caps accounts and the
  # daily total.
  rule {
    action      = "throttle"
    priority    = 1100
    description = "Help chat questions per visitor"

    match {
      expr {
        expression = "request.path.urlDecode().lower().matches('^/+api/+assistant/+help/+chat/*$')"
      }
    }

    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"

      rate_limit_threshold {
        count        = 20
        interval_sec = 600
      }
    }
  }

  # The frontend's server-side calls to the API come from the NAT's address for every visitor at
  # once, so the per-IP limit below leaves them out; the browsers' own calls are counted.
  rule {
    action      = "allow"
    priority    = 1150
    description = "The frontend's server-side calls"

    match {
      versioned_expr = "SRC_IPS_V1"

      config {
        src_ip_ranges = ["${google_compute_address.nat.address}/32"]
      }
    }
  }

  # A general limit per IP: 600 requests a minute, far above what a person (or an office behind
  # one address) sends, so only floods and scripts meet it. Static files (scripts, styles, fonts,
  # images) outside /api don't count; most are served by the CDN before Cloud Armor anyway.
  # gateway/nginx.conf does the same locally.
  rule {
    action      = "throttle"
    priority    = 1200
    description = "Requests per IP"

    match {
      expr {
        # Counted: every API call, and every other request but static files.
        expression = "request.path.urlDecode().lower().matches('^/+api/') || !request.path.urlDecode().lower().matches('^/+_next/+(static|image)/|[.](css|js|map|png|jpe?g|gif|svg|webp|avif|ico|woff2?|mp4|webm|pdf)$')"
      }
    }

    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"

      rate_limit_threshold {
        count        = 600
        interval_sec = 60
      }
    }
  }

  rule {
    action   = "allow"
    priority = 2147483647

    match {
      versioned_expr = "SRC_IPS_V1"

      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}
