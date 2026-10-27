import { expect, type Page, test } from "@playwright/test"

import { API_URL, HUMAN_CHECK_TOKEN, MIN_QUESTION_SECONDS } from "../constants"
import { inviteToken } from "./db"
import { tokenOf } from "./sign-in"
import { randomId } from "./users"

type Template = { id: string; title: string; topic_count: number }

/** Calls the API as the user signed in on `page`; the response's JSON, if any. The test process
 * isn't the browser, so it reaches the gateway by its name on the stack's network. */
export async function api<T>(page: Page, method: string, path: string, body?: unknown) {
  const response = await page.request.fetch(`${API_URL}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${await tokenOf(page)}`,
      // The "I'm not a robot" check: Cloudflare's dummy token, which its test keys (the local
      // ones) always pass.
      "X-Human-Check": HUMAN_CHECK_TOKEN,
    },
    data: body,
  })
  expect(response.ok(), `${method} ${path} -> ${response.status()}`).toBe(true)
  const text = await response.text()

  return (text ? JSON.parse(text) : null) as T
}

/** A throwaway company; names are unique across prepza, so each gets a random part. */
export async function createCompany(page: Page, name = `E2E ${randomId()}`) {
  const company = await api<{ id: string }>(page, "POST", "/companies/companies", { name })
  // The bell keeps a user's companies for a minute; the site's create dialog has it read them
  // again (COMPANIES_CHANGED), so its notices show at once. Made here, the test does the same.
  await api(page, "GET", "/notifications/me?fresh=true")

  return { id: company.id, name }
}

/** The local English templates a company can use, fewest topics first, or a skip when there's
 * none: interviews are made from templates here, since generating one needs OpenAI. */
export async function templatesBySize(page: Page): Promise<Template[]> {
  const templates = await api<Template[]>(
    page,
    "GET",
    "/library/templates/copyable?language=en&limit=50"
  )
  test.skip(
    templates.length === 0,
    "No usable templates locally: an interview can't be made without a real (OpenAI) generation"
  )

  return templates.sort((a, b) => a.topic_count - b.topic_count)
}

/** An interview made from the smallest template a company can use, with the shortest time per
 * question. */
export async function createInterview(page: Page, companyId: string) {
  const [template] = await templatesBySize(page)
  const interview = await api<{ id: string }>(
    page,
    "POST",
    `/companies/interviews/from-template?company_id=${companyId}`,
    { template_id: template.id }
  )
  await api(page, "PATCH", `/companies/interviews/${interview.id}/settings`, {
    question_seconds: MIN_QUESTION_SECONDS,
  })

  return interview.id
}

/** The invited candidate, signed in on `candidate`, starts their invite, answers one question and
 * finishes, as the app's player does. */
export async function finishOneAnswer(candidate: Page, email: string) {
  const { sessions } = await api<{ sessions: { id: string }[] }>(
    candidate,
    "POST",
    `/companies/invites/${await inviteToken(email)}/start`,
    { pledged: true }
  )
  const step = await api<{ session: { id: string }; question: { question_id: string } }>(
    candidate,
    "POST",
    `/rounds/sessions/${sessions[0].id}/step`
  )
  await api(candidate, "POST", `/rounds/sessions/${step.session.id}/answers`, {
    question_id: step.question.question_id,
    option_index: 0,
  })
  await api(candidate, "POST", `/rounds/sessions/${sessions[0].id}/finish-interview`)
}

/** Invites one candidate to the interview. */
export async function inviteCandidate(page: Page, interviewId: string, email: string) {
  await api(page, "POST", `/companies/interviews/${interviewId}/candidates`, { email })
}

/** Deletes the companies the signed-in throwaway user owns: only ever the tests' own. */
export async function deleteOwnCompanies(page: Page) {
  const companies = await api<{ id: string; role: string }[]>(
    page,
    "GET",
    "/companies/companies?limit=100"
  )

  for (const company of companies.filter((item) => item.role === "owner")) {
    await api(page, "DELETE", `/companies/companies/${company.id}`)
  }
}
