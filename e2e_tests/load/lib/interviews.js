import { sleep } from "k6"

import { signUp, ownerEmail } from "./accounts.js"
import { THINK_SECONDS, TEMPLATE_ID } from "./config.js"
import { api, must } from "./http.js"

// A candidate never needs more steps than this; more means the interview isn't moving on.
const MAX_STEPS = 500

// The template the last test was made from, tried first for the next one (setup runs in one VU).
let usable = TEMPLATE_ID

/** The local English templates to make a test from, smallest first: generating one would need
 * OpenAI. */
function templateIds() {
  if (usable) {
    return [usable]
  }

  const templates = must("GET", "/library/templates?language=en&limit=50")

  return templates.sort((a, b) => a.topic_count - b.topic_count).map((item) => item.id)
}

/** A throwaway owner and company with a test made from a template, its shareable link on. */
export function createCompany(run, index) {
  const owner = signUp(ownerEmail(run, index))
  const company = must("POST", "/companies/companies", owner, { name: `Load ${run} ${index}` })
  const query = `company_id=${company.id}`
  let interview

  // A template with too few questions left can't be used (404); the next one may.
  for (const templateId of templateIds()) {
    interview = api("POST", `/companies/interviews/from-template?${query}`, owner, {
      template_id: templateId,
    })

    if (interview) {
      usable = templateId

      break
    }
  }

  if (!interview) {
    throw new Error("No local template can be used: a test can't be made without OpenAI")
  }

  const link = must("PUT", `/companies/interviews/${interview.id}/link`, owner, { on: true })

  return { owner, company: company.id, interview: interview.id, link: link.link_token }
}

/** A candidate opens the test's link, starts, and answers every question as the interview page
 * does (step, answer, step...) until it's done. Answers are random, so grades differ. True when
 * the interview finished. */
export function takeInterview(token, link, think = THINK_SECONDS) {
  api("GET", `/companies/links/${link}`, token, undefined, "link")
  const started = api("POST", `/companies/links/${link}/start`, token, { pledged: true }, "start")

  if (!started) {
    return false
  }

  const session = started.sessions[0].id
  let step = api("POST", `/rounds/sessions/${session}/step`, token, undefined, "step")

  for (let count = 0; step && !step.done && count < MAX_STEPS; count++) {
    if (step.question) {
      sleep(think)
      api(
        "POST",
        `/rounds/sessions/${step.session.id}/answers`,
        token,
        {
          question_id: step.question.question_id,
          option_index: Math.floor(Math.random() * step.question.options.length),
        },
        "answer"
      )
    }

    step = api("POST", `/rounds/sessions/${session}/step`, token, undefined, "step")
  }

  return Boolean(step && step.done)
}
