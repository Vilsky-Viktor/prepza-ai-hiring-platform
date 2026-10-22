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
  description = "The repository (owner/name), for links to its files such as the runbooks."
  type        = string
  default     = "Vilsky-Viktor/prepza-ai-hiring-platform"
}

# Google trusts GitHub's tokens by these numbers, not by the names, which can be registered again
# by someone else after a rename or a deletion: gh api repos/<owner>/<name> --jq '.id, .owner.id'.
variable "github_repository_id" {
  description = "The numeric id of the repository whose main branch and version tags may reach Google Cloud."
  type        = number
  default     = 1397666435
}

variable "github_repository_owner_id" {
  description = "The numeric id of that repository's owner."
  type        = number
  default     = 28306769
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
  description = "sandbox or production: the Paddle account billing's key and client token must belong to."
  type        = string
  default     = "sandbox"

  validation {
    condition     = contains(["sandbox", "production"], var.paddle_environment)
    error_message = "paddle_environment is sandbox or production."
  }
}

variable "paddle_client_token" {
  description = "Paddle.js's client-side token; public by design."
  type        = string
  default     = ""
}

variable "paddle_product_candidates" {
  description = "The Paddle product every top-up is sold under (docs/features/billing.md); empty: nothing is sold."
  type        = string
  default     = ""
}

variable "paddle_prices" {
  description = "Paddle price ids by name: auto_top_up, the $0 monthly price whose checkout saves the card (docs/features/billing.md)."
  type        = map(string)
  default     = {}
}

variable "alert_email" {
  description = "Where outage and budget alerts go."
  type        = string
}

variable "alert_sms" {
  description = "A phone number in international format (+372...) that also gets every page (a CRITICAL alert) by text message, as a backup to the app. Empty: no text messages."
  type        = string
  default     = ""
}

variable "alert_app_channel" {
  description = "The Cloud Monitoring app's notification channel (projects/<project>/notificationChannels/<id>), which the app makes when you sign in to it on your phone; pages go to it. Empty: pages by email and SMS only."
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

variable "linkedin_client_id" {
  description = "Client id of the LinkedIn app (Sign In with LinkedIn using OpenID Connect); empty leaves it off."
  type        = string
  default     = ""
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

variable "ai_spend_alert_daily" {
  description = "Alert (a ticket) when all AI calls' OpenAI spend over a day is above this, in USD: about twice a day's share of the admin zone's MONTHLY_BUDGET."
  type        = number
  default     = 20
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
