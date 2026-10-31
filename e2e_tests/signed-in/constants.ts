// The site's address as the browser has it (signed-in.sh maps it to the gateway's test port).
export const SITE_URL = process.env.SITE_URL ?? "http://localhost:8090";
// The token cookie the frontend writes once signed in (frontend/src/config/auth.ts).
export const TOKEN_COOKIE = "testee_token";
// The interface's language, which the frontend writes from the account's (frontend/src/config/i18n.ts).
export const LOCALE_COOKIE = "testee_locale";
// Screenshots, one folder per spec, in the results folder Playwright empties at the start of a run;
// git ignores it.
export const SCREENSHOTS = "test-results/screenshots";
// The shortest time per question the API allows (services/companies/src/companies/constants/interviews.py).
export const MIN_QUESTION_SECONDS = 10;
// The companies database, for the invite links candidates are emailed (like e2e.py).
export const POSTGRES_HOST = "postgres";
// The API as the test process reaches it: the gateway on the stack's network (signed-in.sh).
export const API_URL = process.env.API_URL ?? "http://gateway:8082/api";
// The site as the test process reaches it: the gateway's test port on the stack's network.
export const FRONTEND_URL = process.env.FRONTEND_URL ?? "http://gateway:8082";

// The web hook secret key of the Greenhouse connection the tests save.
export const GREENHOUSE_E2E_SECRET = "e2e-webhook-secret";
// Cloudflare Turnstile's dummy token: the local test secret passes it (testee_common human_check).
export const HUMAN_CHECK_TOKEN = "XXXX.DUMMY.TOKEN.XXXX";
// Billing as the test process reaches it on the stack's network, for its scheduled jobs.
export const BILLING_URL = process.env.BILLING_URL ?? "http://billing:8000";
// The Firebase Auth emulator as the test process reaches it on the stack's network.
export const AUTH_URL = process.env.AUTH_URL ?? "http://firebase-auth:9199";
