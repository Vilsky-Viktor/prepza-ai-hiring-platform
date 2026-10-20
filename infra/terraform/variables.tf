variable "project_id" {
  description = "The Google Cloud project, for example prepza-prod. Firebase uses the same project."
  type        = string
}

variable "region" {
  description = "Everything runs here: the EU, for data residency; the global load balancer keeps US latency low."
  type        = string
  default     = "europe-west1"
}

variable "domain" {
  description = "The site's domain; its A record points at the load balancer's address."
  type        = string
  default     = "prepza.ai"
}

variable "image_tag" {
  description = "The images' tag on the first apply; afterwards the deploy pipeline sets them."
  type        = string
  default     = "first"
}

variable "github_repository" {
  description = "The repository whose main branch may deploy (owner/name)."
  type        = string
  default     = "Vilsky-Viktor/ai-interview-prep-platform"
}

variable "db_tier" {
  description = "Cloud SQL machine type; db-g1-small to start, a dedicated one (db-custom-2-7680) as it grows."
  type        = string
  default     = "db-g1-small"
}

variable "db_high_availability" {
  description = "A standby in another zone that takes over on failure; doubles the database cost."
  type        = bool
  default     = false
}

variable "mail_from" {
  description = "Sender of service emails (invites, reports, billing), on a domain verified in Resend."
  type        = string
  default     = "prepza. <no-reply@prepza.ai>"
}

variable "mail_from_updates" {
  description = "Sender of the emails users may turn off (the activity digest, reminders), on a subdomain verified in Resend on its own, so their spam complaints can't hurt the service emails."
  type        = string
  default     = "prepza. <updates@mail.prepza.ai>"
}

variable "backend_sentry_dsn" {
  description = "Backend Sentry DSN; empty sends nothing. Not secret: it only allows sending events."
  type        = string
  default     = ""
}

variable "firebase_web_api_key" {
  description = "The Firebase web app's apiKey (the frontend's NEXT_PUBLIC_FIREBASE_API_KEY); public by design. The assistant signs AI apps' users in with it, from the server: restrict the key to its APIs (Identity Toolkit, Token Service), never to websites (HTTP referrers), which would refuse the server's calls."
  type        = string

  validation {
    condition     = length(var.firebase_web_api_key) > 0
    error_message = "firebase_web_api_key is required: without it every AI app call fails."
  }
}

variable "paddle_environment" {
  description = "sandbox or production."
  type        = string
  default     = "sandbox"
}

variable "paddle_client_token" {
  description = "Paddle.js's client-side token; public by design."
  type        = string
  default     = ""
}

variable "paddle_product_candidates" {
  description = "The Paddle product a top-up of any number of candidates is sold under (docs/features/billing.md); empty: not sold."
  type        = string
  default     = ""
}

variable "paddle_prices" {
  description = "Paddle price id of each product (services/billing/app/constants/products.py)."
  type        = map(string)
  default     = {}
}

variable "alert_email" {
  description = "Where outage and budget alerts go."
  type        = string
}

variable "alert_sms" {
  description = "A phone number in international format (+372...) that also gets every alert by text message. Empty: email only."
  type        = string
  default     = ""
}

variable "billing_account" {
  description = "The billing account the project uses (XXXXXX-XXXXXX-XXXXXX), for the monthly budget."
  type        = string
}

variable "monthly_budget" {
  description = "Monthly Google Cloud budget, in the billing account's currency; alerts only, nothing stops."
  type        = number
  default     = 300
}

variable "superadmin_emails" {
  description = "Superadmins, prepza's own team (templates, the question bank, the emergency pause and maintenance mode): verified Google emails."
  type        = list(string)

  # Without one, nobody can pause invites or turn maintenance mode on in an emergency.
  validation {
    condition     = length(var.superadmin_emails) > 0
    error_message = "Set at least one superadmin email: the emergency pause and maintenance mode are switched only from the admin zone."
  }
}

variable "github_client_id" {
  description = "Client id of the GitHub OAuth app for signing in; empty leaves GitHub sign-in off."
  type        = string
  default     = ""
}

variable "github_client_secret" {
  description = "Client secret of the GitHub OAuth app (kept in the Terraform state)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "linkedin_client_id" {
  description = "Client id of the LinkedIn app (Sign In with LinkedIn using OpenID Connect); empty leaves it off."
  type        = string
  default     = ""
}

variable "linkedin_client_secret" {
  description = "Client secret of the LinkedIn app (kept in the Terraform state)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_site_verification" {
  description = "The token from Google Search Console's HTML-tag check for the domain; empty skips it."
  type        = string
  default     = ""
}

variable "bing_site_verification" {
  description = "The token from Bing Webmaster Tools' meta-tag check for the domain; empty skips it."
  type        = string
  default     = ""
}

variable "ai_spend_alert_hourly" {
  description = "Alert when all AI calls' OpenAI spend in one hour is above this, in USD."
  type        = number
  default     = 20
}

variable "email_bounce_alert_hourly" {
  description = "Alert when more emails than this bounce or are marked as spam in one hour."
  type        = number
  default     = 20
}
