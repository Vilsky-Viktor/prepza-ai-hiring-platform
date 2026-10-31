import { readFileSync } from "node:fs"

import { expect, test } from "../fixtures"
import { api, createCompany, inviteCandidate } from "../helpers/api"
import { addTopUp, inviteToken, verifyCompany } from "../helpers/db"
import { addAtsConnection, addSlackConnection } from "../helpers/db-integrations"
import { exampleEmail, PEOPLE, takePart } from "../helpers/feature-people"
import {
  miraLoud,
  nameSlack,
  pair,
  roleInterview,
  SHOT_AI_ROLE,
  SHOT_AI_TEMPLATE,
  SHOT_BRAND,
  SHOT_VIEWPORT,
  EMAIL_VIEWPORT,
  shotLogo,
} from "../helpers/feature-shots"
import { openDialog, visit } from "../helpers/navigation"
import { mailHtml, mailsTo } from "../helpers/mailpit"
import { ownerEmail, throwawayEmail } from "../helpers/users"
import { fakeMicrophone, fakeMira, noReadingAloud } from "../helpers/voice"

// A sentence of real speech (the evals' voice message v01): Mira's voice in the voice picture.
const SPEECH = readFileSync(new URL("../media/speech.ogg", import.meta.url))

// The features page's pictures of the real app (helpers/feature-shots.ts): taken only with
// SHOTS=1, at twice the pixels, with made-up people; nothing here checks the product.
test.skip(process.env.SHOTS !== "1", "Pictures for the features page, taken with SHOTS=1 only")
test.use({ deviceScaleFactor: 2, viewport: SHOT_VIEWPORT })

// The company's screens: topics, settings, candidates, a report with integrity signals, notes,
// the invite dialog, integrations, the brand tab and the bias-audit export.
test("features page: the company's screens", async ({ signInAs }) => {
  test.setTimeout(900_000)
  const owner = await signInAs(ownerEmail(), undefined, "Alex Morgan")
  const company = await createCompany(owner, "Northwind Labs")
  await addTopUp(company.id, 20_000, 20_000)

  for (const [theme, colors] of Object.entries(SHOT_BRAND)) {
    await api(owner, "PUT", `/companies/companies/${company.id}/brand-colors/${theme}`, { colors })
  }

  const interviewId = await roleInterview(owner, company.id)
  const base = `/companies/${company.id}/interviews/${interviewId}`

  const signalsId = await takePart(signInAs, owner, interviewId, PEOPLE[0])

  for (const person of PEOPLE.slice(1)) {
    await takePart(signInAs, owner, interviewId, person)
  }

  const pinned = await api<{ id: string }>(owner, "POST", `/companies/interviews/${interviewId}/notes`, {
    text: "Shortlist Maya and Lucas for the system design round on Thursday.",
  })
  await api(owner, "POST", `/companies/interviews/${interviewId}/notes`, {
    text: "Daniel's answer patterns look odd: let's talk through two of the follow-up questions live.",
  })
  await api(owner, "PUT", `/companies/interviews/${interviewId}/notes/${pinned.id}/pinned`, {
    pinned: true,
  })
  await api(owner, "PUT", `/companies/interviews/${interviewId}/link`, { on: true })
  await addAtsConnection(company.id, interviewId, {}, "greenhouse")
  await addSlackConnection(company.id)
  await nameSlack(company.id, "Northwind Labs")

  // The topics picture shows an AI architect's interview.
  const aiId = await roleInterview(owner, company.id, SHOT_AI_ROLE, SHOT_AI_TEMPLATE)
  await visit(owner, `/companies/${company.id}/interviews/${aiId}`)
  await expect(owner.getByTestId("manage-questions").first()).toBeVisible()
  await pair(owner, "topics")

  await visit(owner, `${base}?tab=settings`)
  await expect(owner.getByRole("main").getByTestId("answer-mode").filter({ visible: true })).toBeVisible()
  // The link as the site's real address shows it, not the local one.
  await owner.evaluate((site) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)

    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      node.textContent = node.textContent!.replace(location.origin, site)
    }

    for (const input of document.querySelectorAll("input")) {
      input.value = input.value.replace(location.origin, site)
    }
  }, "https://testee.ai")
  await pair(owner, "settings")

  await visit(owner, `${base}?tab=candidates`)
  await expect(owner.getByText(exampleEmail("Maya Chen")).first()).toBeVisible()
  await pair(owner, "candidates")

  await openDialog(owner, owner.getByTestId("new-candidate").filter({ visible: true }))
  const dialog = owner.getByRole("dialog")
  await dialog.getByRole("tab").first().click()
  await dialog.locator('input[type="email"]').fill(exampleEmail("Nina Patel"))
  await pair(owner, "invite")
  await owner.keyboard.press("Escape")

  await visit(owner, `${base}/candidates/${signalsId}`)
  const patterns = owner.getByTestId("answer-patterns").filter({ visible: true })
  await expect(patterns.locator("[data-signal]").first()).toBeVisible()
  await patterns.scrollIntoViewIfNeeded()
  await pair(owner, "signals")
  await openDialog(owner, owner.getByRole("main").getByRole("button", { name: /share/i }).last())
  await pair(owner, "share")
  await owner.keyboard.press("Escape")

  await visit(owner, `${base}?tab=notes`)
  await expect(owner.getByTestId("note").filter({ visible: true }).first()).toBeVisible()
  await pair(owner, "notes")

  await visit(owner, `/companies/${company.id}/interviews`)
  await expect(owner.getByTestId("pinned-note").filter({ visible: true })).toBeVisible()
  await pair(owner, "interviews")

  await visit(owner, `/companies/${company.id}/integrations`)
  await expect(owner.getByRole("main").getByRole("listitem").first()).toBeVisible()
  await pair(owner, "integrations")

  await visit(owner, `/companies/${company.id}/brand?page=light`)
  await expect(owner.getByTestId("brand-preview").filter({ visible: true })).toBeVisible()
  await pair(owner, "brand")

  await visit(owner, `/companies/${company.id}/actions`)
  await openDialog(owner, owner.getByTestId("bias-audit-export"))
  await pair(owner, "bias-audit")
})

// What a candidate sees in click mode: the start page and a question.
test("features page: a candidate's question", async ({ signInAs }) => {
  test.setTimeout(300_000)
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner, "Lumen Health")
  await verifyCompany(company.id, "lumenhealth.example")
  await shotLogo(owner, company.id)
  const interviewId = await roleInterview(owner, company.id)
  const email = throwawayEmail("shot-click")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email, undefined, "Nina Patel")
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  await expect(candidate.getByTestId("start-pledge").filter({ visible: true })).toBeVisible()
  await expect(candidate.getByRole("img", { name: "Lumen Health" }).first()).toBeVisible()
  await pair(candidate, "start")
  await candidate.getByTestId("start-pledge").filter({ visible: true }).click()
  await candidate.getByRole("main").getByRole("button").last().click()
  await expect(candidate).toHaveURL(/\/sessions\//)
  const option = candidate.getByRole("main").locator("li > button[aria-pressed]").nth(1)
  await option.click()
  await expect(option).toHaveAttribute("aria-pressed", "true")
  await pair(candidate, "question")

  // The invitation as it arrived (the local stack's Mailpit), addressed to her made-up address.
  await expect.poll(async () => (await mailsTo(owner.request, email)).length).toBeGreaterThan(0)
  const [invitation] = await mailsTo(owner.request, email)
  const html = (await mailHtml(owner.request, invitation.ID)).replaceAll(email, exampleEmail("Nina Patel"))
  const mail = await candidate.context().newPage()
  await mail.setViewportSize(EMAIL_VIEWPORT)
  await mail.setContent(html, { waitUntil: "load" })
  await expect(mail.getByRole("img", { name: "Lumen Health" })).toBeVisible()
  // Its link as the site's real address shows it, not the local one.
  await mail.evaluate((site) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)

    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      node.textContent = node.textContent!.replace(/^https?:\/\/[^/]+/, site)
    }
  }, "https://testee.ai")
  await pair(mail, "email")
})

// Voice mode: Mira reading the question aloud, her wave moving. Her clips are mocked, so nothing
// is read aloud by OpenAI; the question's is a sentence of real speech, long enough for both
// pictures.
test("features page: a voice interview", async ({ signInAs }) => {
  test.setTimeout(300_000)
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner, "Orbit Mobility")
  await noReadingAloud(company.id)
  const interviewId = await roleInterview(owner, company.id)
  await api(owner, "PATCH", `/companies/interviews/${interviewId}/settings`, {
    question_seconds: 300,
    voice: true,
  })
  const email = throwawayEmail("shot-voice")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email)
  await fakeMicrophone(candidate)
  await fakeMira(candidate)
  const token = await inviteToken(email)
  await api(candidate, "POST", `/companies/invites/${token}/start`, { pledged: true })
  await candidate.route(/\/voice\/question/, (route) =>
    route.fulfill({ body: SPEECH, contentType: "audio/ogg" }),
  )
  await visit(candidate, `/invite/${token}`)
  await candidate.getByTestId("voice-access").getByRole("button").click()
  await candidate.getByRole("main").getByRole("button").last().click()
  await expect(candidate.locator('[data-testid="talking-dot"][data-talking="true"]')).toBeVisible()
  await pair(candidate, "voice", () => miraLoud(candidate))
})
