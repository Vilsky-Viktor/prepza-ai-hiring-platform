import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, deleteOwnCompanies, templatesBySize } from "../helpers/api"
import { openTab, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

type Detail = {
  topics: { id: string; question_count: number; question_limit: number }[]
  question_seconds: number
  total_questions: number
  max_questions: number
  total_minutes: number
}

const SECONDS = 30

async function detail(page: Page, interviewId: string) {
  return api<Detail>(page, "GET", `/companies/interviews/${interviewId}`)
}

/** The estimate's three numbers as the page shows them, the total against the cap. */
async function expectEstimate(page: Page, found: Detail) {
  const estimate = page.getByTestId("interview-estimate")
  await expect(estimate.getByTestId("total-questions")).toContainText(String(found.total_questions))
  await expect(estimate.getByTestId("total-questions")).toContainText(String(found.max_questions))
  await expect(estimate.getByTestId("question-seconds")).toContainText(
    String(found.question_seconds)
  )
  await expect(estimate.getByTestId("total-minutes")).toContainText(String(found.total_minutes))
}

// The topics tab adds up what each candidate gets: the total questions, the time per question
// and the whole interview's time, as the API counts them. A topic's number changed on the tab,
// to 0 too, changes them; the candidates and settings tabs don't show them.
test("the topics tab shows what the interview adds up to and follows each topic's number", async ({
  signInAs,
}) => {
  test.setTimeout(180_000)
  const owner = await signInAs(throwawayEmail("interview-estimate"))
  const company = await createCompany(owner)
  const template = (await templatesBySize(owner)).find((found) => found.topic_count >= 2)
  test.skip(!template, "No local template with two topics")

  try {
    const { id } = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template!.id }
    )
    await api(owner, "PATCH", `/companies/interviews/${id}/settings`, {
      question_seconds: SECONDS,
    })
    const url = `/companies/${company.id}/interviews/${id}`
    const before = await detail(owner, id)
    expect(before.question_seconds).toBe(SECONDS)
    expect(before.total_minutes).toBe(Math.ceil((before.total_questions * SECONDS) / 60))

    await visit(owner, url)
    await expectEstimate(owner, before)
    await shot(owner, "interview-estimate")

    // The first topic down to 1 question.
    const first = owner.getByRole("main").getByRole("spinbutton").first()
    await first.fill("1")
    await first.press("Enter")
    const one = before.total_questions - before.topics[0].question_limit + 1
    await expect(owner.getByTestId("total-questions")).toContainText(String(one))
    const afterOne = await detail(owner, id)
    expect(afterOne.total_questions).toBe(one)
    await expectEstimate(owner, afterOne)

    // Then to 0: the topic is left out, and its questions with it.
    await first.fill("0")
    await first.press("Enter")
    await expect(owner.getByTestId("total-questions")).toContainText(String(one - 1))
    const afterZero = await detail(owner, id)
    expect(afterZero.topics[0].question_limit).toBe(0)
    await expectEstimate(owner, afterZero)
    await shot(owner, "interview-estimate-zero")

    // Not on the other tabs.
    await openTab(owner, "?tab=candidates")
    await expect(owner.getByTestId("interview-estimate")).toHaveCount(0)
    await openTab(owner, "?tab=settings")
    await expect(owner.getByTestId("interview-estimate")).toHaveCount(0)
  } finally {
    await deleteOwnCompanies(owner)
  }
})

// Every topic at 0 would leave candidates nothing: the last one is refused, with the reason.
test("the last topic with questions can't be set to 0", async ({ signInAs }) => {
  test.setTimeout(180_000)
  const owner = await signInAs(throwawayEmail("interview-last-topic"))
  const company = await createCompany(owner)
  const template = (await templatesBySize(owner)).find((found) => found.topic_count >= 2)
  test.skip(!template, "No local template with two topics")

  try {
    const { id } = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template!.id }
    )
    const { topics } = await detail(owner, id)

    for (const topic of topics.slice(1)) {
      await api(owner, "PUT", `/companies/interviews/${id}/topics/${topic.id}/limit`, { limit: 0 })
    }

    await visit(owner, `/companies/${company.id}/interviews/${id}`)
    const first = owner.getByRole("main").getByRole("spinbutton").first()
    await first.fill("0")
    await first.press("Enter")

    const refused = owner.locator('[data-sonner-toast][data-type="error"]')
    await expect(refused).toContainText("An interview needs at least one topic with questions.")
    await expect(first).toHaveValue(String(topics[0].question_limit))
    expect((await detail(owner, id)).topics[0].question_limit).toBe(topics[0].question_limit)
  } finally {
    await deleteOwnCompanies(owner)
  }
})

// A candidate gets at most max_questions over all topics: with the interview full, raising a
// topic is refused with the reason, and nothing changes.
test("a topic can't take the interview over the cap", async ({ signInAs }) => {
  test.setTimeout(180_000)
  const owner = await signInAs(throwawayEmail("interview-cap"))
  const company = await createCompany(owner)
  const template = (await templatesBySize(owner)).at(-1)

  try {
    const { id } = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template!.id }
    )
    const { topics, max_questions } = await detail(owner, id)
    const last = topics.at(-1)!
    const others = topics.slice(0, -1)
    const room = others.reduce((sum, topic) => sum + topic.question_count, 0)
    test.skip(room < max_questions, "No local template with enough questions to fill the cap")
    const limitPath = (topicId: string) => `/companies/interviews/${id}/topics/${topicId}/limit`

    // Every topic but the first out, then filled up to the cap without the last one.
    for (const topic of topics.slice(1).reverse()) {
      await api(owner, "PUT", limitPath(topic.id), { limit: 0 })
    }

    let filled = 0

    for (const topic of others) {
      const limit = Math.min(topic.question_count, max_questions - filled)
      await api(owner, "PUT", limitPath(topic.id), { limit })
      filled += limit
    }

    const full = await detail(owner, id)
    expect(full.total_questions).toBe(max_questions)

    await visit(owner, `/companies/${company.id}/interviews/${id}`)
    await expectEstimate(owner, full)
    const lastField = owner.getByRole("main").getByRole("spinbutton").last()
    await lastField.fill("1")
    await lastField.press("Enter")

    const refused = owner.locator('[data-sonner-toast][data-type="error"]')
    await expect(refused).toContainText(`At most ${max_questions} questions per candidate; 0 left.`)
    await expect(lastField).toHaveValue("0")
    await shot(owner, "interview-cap-refused")
    const after = await detail(owner, id)
    expect(after.total_questions).toBe(max_questions)
    expect(after.topics.at(-1)!.question_limit).toBe(0)
    expect(last.id).toBe(after.topics.at(-1)!.id)
  } finally {
    await deleteOwnCompanies(owner)
  }
})
