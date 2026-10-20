import { check } from "k6"
import http from "k6/http"

import { API_URL, HUMAN_CHECK_TOKEN } from "./config.js"

// A call the run measures carries its endpoint's name, which the thresholds and the summary go
// by; setup, sign-ins and clean-up carry none and count towards no threshold.
function params(token, endpoint) {
  const headers = { "Content-Type": "application/json", "X-Human-Check": HUMAN_CHECK_TOKEN }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return { headers, tags: endpoint ? { endpoint, phase: "load" } : { phase: "setup" } }
}

/** Calls the API; its JSON (null when empty), or undefined when it failed. */
export function api(method, path, token, body, endpoint) {
  const response = http.request(
    method,
    API_URL + path,
    body === undefined ? null : JSON.stringify(body),
    params(token, endpoint)
  )
  const ok = response.status < 400

  if (endpoint) {
    check(response, { [`${endpoint} ok`]: () => ok })
  }

  if (!ok) {
    console.warn(`${method} ${path} -> ${response.status} ${String(response.body).slice(0, 200)}`)

    return undefined
  }

  return response.body ? response.json() : null
}

/** The same, for setup: a failure stops the run instead of skewing it. */
export function must(method, path, token, body) {
  const result = api(method, path, token, body)

  if (result === undefined) {
    throw new Error(`setup failed: ${method} ${path}`)
  }

  return result
}

/** A page or public JSON, as a signed-out visitor gets it. */
export function visit(url, endpoint) {
  const response = http.get(url, { tags: { endpoint, phase: "load" } })
  check(response, { [`${endpoint} ok`]: (r) => r.status === 200 })

  return response
}
