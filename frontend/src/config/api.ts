// The public API's reference on the site.
export const API_DOCS_PATH = "/api-docs"
// The longest key name and web hook address the API takes.
export const MAX_KEY_NAME = 80
export const MAX_WEBHOOK_URL = 500
// Public pages' data, the same for every visitor (prices, FAQ, legal texts, role tests): how
// long the site keeps a copy, in seconds, and how long it waits for a service, in milliseconds.
export const PUBLIC_REVALIDATE_SECONDS = 300
export const PUBLIC_TIMEOUT_MS = 5000
// A signed-in page's calls give up after this long, so a service that hangs fails the page (or
// leaves out what it adds) in seconds rather than holding it for a minute.
export const SERVER_TIMEOUT_MS = 10000
