// Where the load goes and how much of it. Every value can be set from the environment
// (e2e_tests/load.sh passes them through); the defaults are modest, for a laptop's Docker VM.

export const BASE_URL = __ENV.BASE_URL || "http://gateway:8081"
export const API_URL = `${BASE_URL}/api`
// The Firebase Auth emulator: users are made and signed in here, never in a real project.
export const AUTH_URL = __ENV.AUTH_URL || "http://firebase-auth:9199"
export const PROJECT_ID = __ENV.FIREBASE_PROJECT_ID

export const VUS = Number(__ENV.VUS || 5)
export const DURATION = __ENV.DURATION || "1m"
// Seconds a user waits between two actions (reading a question, looking at a page).
export const THINK_SECONDS = Number(__ENV.THINK_SECONDS || 1)
// Candidates each VU takes the interview as, one after the other.
export const ITERATIONS = Number(__ENV.ITERATIONS || 1)
// Candidates starting a minute, whatever the stack's speed (an open model, for capacity: a slow
// stack can't slow the arrivals down, as it does with VUS taking turns); 0 keeps the VUs' turns.
export const RATE = Number(__ENV.RATE || 0)
// A test made from this local template; else the smallest one that can be used.
export const TEMPLATE_ID = __ENV.TEMPLATE_ID || ""

// A company's welcome credits pay for this many candidates; a throwaway owner (and company) is
// made for every this many.
export const CANDIDATES_PER_COMPANY = 3
// The dashboard's companies, each with this many finished candidates.
export const DASHBOARD_COMPANIES = Number(__ENV.COMPANIES || 3)

export const PASSWORD = "load-test-secret"
// Cloudflare Turnstile's dummy token, which the local test secret passes (testee_common
// human_check): sent as the browser sends its token, so a first company and a link start work.
export const HUMAN_CHECK_TOKEN = "XXXX.DUMMY.TOKEN.XXXX"
// Every throwaway account's email carries this, with the run's own id after it.
export const EMAIL_TAG = "load-"

// Fail the run when exceeded. For the local stack (one container per service on a laptop);
// production and staging targets are in e2e_tests/load/README.md.
export const API_P95 = "p(95)<500"
export const PAGE_P95 = "p(95)<2000"
export const ERROR_RATE = "rate<0.01"
