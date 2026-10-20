import { expect, test } from "../fixtures"
import { API_URL, FRONTEND_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { verifyCompany } from "../helpers/db"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The company's own site, at an address of its verified website's domain: it embeds the interview with
// the hosted script and hears when the candidate has finished.
const DOMAIN = "acme-embed.com"
const SITE = `http://jobs.${DOMAIN}`

function sitePage(siteUrl: string, inviteUrl: string) {
  return `<!doctype html><html><head><title>Acme careers</title></head><body>
    <h1>Acme careers</h1><div id="interview"></div>
    <script src="${siteUrl}/embed/v1.js"></script>
    <script>
      window.events = []
      Prepza.embed({
        element: "#interview",
        url: ${JSON.stringify(inviteUrl)},
        theme: "dark",
        onReady: () => window.events.push("ready"),
        onStart: () => window.events.push("started"),
        onFinish: ({ candidateId }) => window.events.push("finished:" + candidateId),
      })
    </script></body></html>`
}

test("a company's own site embeds a candidate's interview and hears it finish", async ({
  browser,
  baseURL,
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const { key } = await api<{ key: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    { name: "Careers site", expiry: "1", permissions: ["candidates:invite"] }
  )
  const invite = async (email: string, signIn: boolean) => {
    const response = await owner.request.post(
      `${API_URL}/v1/interviews/${interviewId}/candidates`,
      { headers: { Authorization: `Bearer ${key}` }, data: { email, sign_in: signIn } }
    )
    expect(response.status()).toBe(201)

    return (await response.json()) as { id: string; invite_url: string }
  }
  const framers = async (inviteUrl: string) => {
    const token = new URL(inviteUrl).pathname.split("/").pop()
    const page = await owner.request.get(`${FRONTEND_URL}/embedded/${token}`)

    return page.headers()["content-security-policy"].match(/frame-ancestors ([^;]+)/)?.[1]
  }

  const candidate = await invite(throwawayEmail("embedded"), false)
  // Not before the company is verified; then only its own site; an invite by email, no site.
  await api(owner, "PUT", `/companies/companies/${company.id}/website`, { website: DOMAIN })
  expect(await framers(candidate.invite_url)).toBe("'none'")
  await verifyCompany(company.id, DOMAIN)
  expect(await framers(candidate.invite_url)).toBe(`${DOMAIN} *.${DOMAIN}`)
  const byEmail = await invite(throwawayEmail("by-email"), true)
  expect(await framers(byEmail.invite_url)).toBe("'none'")

  const context = await browser.newContext()
  const site = await context.newPage()
  await site.route(`${SITE}/**`, (route) =>
    route.fulfill({ contentType: "text/html", body: sitePage(baseURL!, candidate.invite_url) })
  )
  await site.goto(`${SITE}/apply`)
  const frame = site.frameLocator("iframe")

  // No sign-in, no prepza header or footer: the invitation, then the questions in place.
  // The invitation's one button starts it.
  const start = frame.getByRole("main").getByRole("button")
  await expect(start).toBeVisible()
  await expect(frame.locator("header, footer")).toHaveCount(0)
  // The SDK asked for the dark theme: prepza's dark colors, as the company has none of its own.
  await expect(frame.locator("html")).toHaveCSS("--background", "#0a0a0a")
  await shot(site, "invitation")
  // The frame fits its content and stops: a page sized by the screen (the frame's own height)
  // would grow it without end.
  const frameHeight = () =>
    site.locator("iframe").evaluate((element) => element.getBoundingClientRect().height)
  await expect.poll(frameHeight).toBeLessThan(1600)
  const settled = await frameHeight()
  await expect(start).toBeEnabled()
  expect(await frameHeight()).toBe(settled)
  await start.click()
  await expect(frame.getByTestId("finish-interview")).toBeVisible({
    timeout: 60_000,
  })
  await expect(frame.locator("header, footer")).toHaveCount(0)
  await shot(site, "question")
  await frame.getByTestId("finish-interview").click()
  // The confirmation is the dialog's last button.
  await frame.getByRole("dialog").getByRole("button").last().click()
  // Finished: the interview's title, and no way back anywhere (the site goes on itself).
  await expect(frame.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(frame.getByTestId("finish-interview")).toHaveCount(0)
  await expect(frame.getByRole("main").locator("a")).toHaveCount(0)
  await expect
    .poll(() => site.evaluate(() => (window as unknown as { events: string[] }).events))
    .toEqual(["ready", "started", `finished:${candidate.id}`])
  await shot(site, "finished")
  await context.close()
})

test("the hosted script is served as it is, cached briefly and loadable cross-origin", async ({
  request,
}) => {
  const script = await request.get(`${FRONTEND_URL}/embed/v1.js`)

  expect(script.status()).toBe(200)
  const headers = script.headers()
  expect(headers["cache-control"]).toBe("public, max-age=300, stale-while-revalidate=86400")
  expect(headers["access-control-allow-origin"]).toBe("*")
  // Not a page: the proxy (CSP, maintenance) leaves it alone.
  expect(headers["content-security-policy"]).toBeUndefined()
})
