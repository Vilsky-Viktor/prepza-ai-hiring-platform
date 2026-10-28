// The ATSs a company can connect, each with its own page at /integrations/<id>: its square logo
// for the app, and its full logo (wordmark) for the landing page, in white on the dark theme
// where its colors are too dark to see.
export const ATS_PROVIDERS = [
  {
    id: "workable",
    name: "Workable",
    logo: "/ats/workable.svg",
    wordmark: "/ats/logos/workable.svg",
    darkWhite: true,
  },
  {
    id: "greenhouse",
    name: "Greenhouse",
    logo: "/ats/greenhouse.png",
    wordmark: "/ats/logos/greenhouse.svg",
    darkWhite: false,
  },
  {
    id: "teamtailor",
    name: "Teamtailor",
    logo: "/ats/teamtailor.png",
    wordmark: "/ats/logos/teamtailor.svg",
    darkWhite: false,
  },
  {
    id: "recruitee",
    name: "Recruitee",
    logo: "/ats/recruitee.png",
    wordmark: "/ats/logos/recruitee.png",
    darkWhite: true,
  },
  {
    id: "breezy",
    name: "Breezy HR",
    logo: "/ats/breezy.png",
    wordmark: "/ats/logos/breezy.png",
    darkWhite: false,
  },
] as const

export type AtsProvider = (typeof ATS_PROVIDERS)[number]

// Where a Workable admin makes the API access token prepza needs, as Workable's menus name it,
// and the scopes it needs: reading jobs and candidates, and writing results to candidates.
export const WORKABLE_TOKEN_PATH = [
  "Settings",
  "Integrations",
  "Apps",
  "API access tokens",
]
export const WORKABLE_SCOPES = ["r_jobs", "r_candidates", "w_candidates"]

// Where a Greenhouse admin makes the API credential, its type, and what it may do: read jobs,
// their posts and stages, and write notes on candidates.
export const GREENHOUSE_CREDENTIAL_PATH = [
  "Configure",
  "Dev Center",
  "API Credential Management",
]
export const GREENHOUSE_CREDENTIAL_TYPE = "Harvest V3 (OAuth)"
export const GREENHOUSE_PERMISSIONS = [
  "Jobs",
  "Job Posts",
  "Job Interview Stages",
  "Notes",
]
// Where the web hook is set up, and the event it sends.
export const GREENHOUSE_WEBHOOK_PATH = ["Configure", "Dev Center", "Web Hooks"]
export const GREENHOUSE_WEBHOOK_EVENT = "Candidate or Prospect Stage Change"

// Where a Teamtailor admin makes the API key, and what it needs: Admin permission, Read/Write.
export const TEAMTAILOR_KEY_PATH = ["Settings", "Integrations", "API keys"]
export const TEAMTAILOR_KEY_ACCESS = ["Admin", "Read/Write"]
// Where the web hook is set up (an add-on Teamtailor turns on), and the event it sends.
export const TEAMTAILOR_WEBHOOK_PATH = ["Settings", "Integrations", "Webhooks"]
export const TEAMTAILOR_WEBHOOK_EVENT = "job_application.update"

// Where a Recruitee user makes the personal API token, and where the web hook is set up, with
// the event it sends.
export const RECRUITEE_TOKEN_PATH = [
  "Settings",
  "Apps and plugins",
  "Personal API tokens",
]
export const RECRUITEE_WEBHOOK_PATH = [
  "Settings",
  "Apps and plugins",
  "Webhooks",
]
export const RECRUITEE_WEBHOOK_EVENT = "candidate_moved"

// Where a Breezy HR user makes the API key: from their name in the bottom left corner.
export const BREEZY_KEY_PATH = ["My Settings", "API Keys"]

// The ATSs whose web hook the company sets up itself, with where and which event; Teamtailor
// and Recruitee make the web hook's secret key (each by its own name), which the company pastes
// back; Greenhouse takes ours.
export const WEBHOOKS = {
  greenhouse: {
    path: GREENHOUSE_WEBHOOK_PATH,
    event: GREENHOUSE_WEBHOOK_EVENT,
    pastesKey: false,
    note: null,
    keyName: null,
    pasteText: null,
  },
  teamtailor: {
    path: TEAMTAILOR_WEBHOOK_PATH,
    event: TEAMTAILOR_WEBHOOK_EVENT,
    pastesKey: true,
    note: "ttWebhookAddon",
    keyName: "signatureKey",
    pasteText: "webhookPasteKey",
  },
  recruitee: {
    path: RECRUITEE_WEBHOOK_PATH,
    event: RECRUITEE_WEBHOOK_EVENT,
    pastesKey: true,
    note: null,
    keyName: "webhookSecretName",
    pasteText: "webhookPasteSecret",
  },
} as const
