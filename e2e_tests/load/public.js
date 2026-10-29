// Signed-out visitors: the public pages, rendered by the frontend, and the public API they read
// (prices, practice tests, FAQ). PAGES=0 leaves the pages out and loads only the API: the local
// frontend is Next's dev server, which renders slowly and can run out of memory under load.
import { sleep } from "k6"
import http from "k6/http"

import {
  API_P95,
  API_URL,
  BASE_URL,
  DURATION,
  ERROR_RATE,
  PAGE_P95,
  THINK_SECONDS,
  VUS,
} from "./lib/config.js"
import { visit } from "./lib/http.js"

const PAGES =
  __ENV.PAGES === "0"
    ? {}
    : {
        home: "/",
        pricing: "/pricing",
        faq: "/faq",
        documents: "/documents",
        practice: "/practice",
      }
const API = {
  catalog: "/billing/catalog",
  templates: "/library/templates?language=en",
  help_faq: "/site/help/faq",
}

export const options = {
  scenarios: { visitors: { executor: "constant-vus", vus: VUS, duration: DURATION } },
  thresholds: {
    ...Object.fromEntries(
      Object.keys(PAGES).map((name) => [`http_req_duration{endpoint:${name}}`, [PAGE_P95]])
    ),
    ...Object.fromEntries(
      Object.keys(API).map((name) => [`http_req_duration{endpoint:${name}}`, [API_P95]])
    ),
    "http_req_failed{phase:load}": [ERROR_RATE],
  },
}

/** The dev server compiles a page the first time it's asked for: done here, not measured. */
export function setup() {
  for (const path of Object.values(PAGES)) {
    http.get(BASE_URL + path, { timeout: "120s", tags: { phase: "setup" } })
  }
}

export default function () {
  for (const [name, path] of Object.entries(PAGES)) {
    visit(BASE_URL + path, name)
    sleep(THINK_SECONDS)
  }

  for (const [name, path] of Object.entries(API)) {
    visit(API_URL + path, name)
  }

  sleep(THINK_SECONDS)
}
