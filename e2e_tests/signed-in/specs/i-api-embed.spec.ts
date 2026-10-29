import type { Browser, Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { API_URL, FRONTEND_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The company's own site, on one of its allowed domains: it embeds the interview with
// the hosted script and hears when the candidate has finished. It calls Prepza.embed before the
// script has loaded (the documented stub queues it) and includes the script twice by mistake.
// The dev server compiles a page on its first request in each browser; a poll waits that long.
const LOADED = { timeout: 60_000 }
const DOMAIN = "acme-embed.com"
const SITE = `http://jobs.${DOMAIN}`

function sitePage(siteUrl: string, inviteUrl: string) {
  return `<!doctype html><html><head><title>Acme careers</title></head><body>
    <h1>Acme careers</h1><div id="interview"></div>
    <script>
      window.events = []
      window.messages = []
      // prepza's messages only: a browser or its dev tools may post others.
      window.addEventListener("message", (event) => {
        if (event.data && event.data.source === "prepza") window.messages.push(event.data)
      })
      window.Prepza = window.Prepza || { q: [], embed: function (o) { this.q.push(o) } }
      Prepza.embed({
        element: "#interview",
        url: ${JSON.stringify(inviteUrl)},
        theme: "dark",
        onReady: () => window.events.push("ready"),
        onStart: () => window.events.push("started"),
        onFinish: ({ candidateId }) => window.events.push("finished:" + candidateId),
        onError: ({ code }) => window.events.push("error:" + code),
      })
    </script>
    <script async src="${siteUrl}/embed/v1.js"></script>
    <script async src="${siteUrl}/embed/v1.js"></script>
    </body></html>`
}

type SiteWindow = { events: string[]; messages: { version?: number }[] }

/** The company's site in a new browser context, embedding `inviteUrl`. */
async function openSite(browser: Browser, baseURL: string, inviteUrl: string) {
  const context = await browser.newContext()
  const site = await context.newPage()
  await site.route(`${SITE}/**`, (route) =>
    route.fulfill({ contentType: "text/html", body: sitePage(baseURL, inviteUrl) })
  )

  return { context, site }
}

function events(site: Page) {
  return site.evaluate(() => (window as unknown as SiteWindow).events)
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
  const framers = async (inviteUrl: string, origin?: string) => {
    const token = new URL(inviteUrl).pathname.split("/").pop()
    const query = origin ? `?origin=${encodeURIComponent(origin)}` : ""
    const page = await owner.request.get(`${FRONTEND_URL}/embedded/${token}${query}`)

    // No policy: the busy dev server answered with an error page; polled again.
    return page.headers()["content-security-policy"]?.match(/frame-ancestors ([^;]+)/)?.[1]
  }

  const candidate = await invite(throwawayEmail("embedded"), false)
  // No site until the company allows its domains (unverified: verification only gives the
  // badge); then only those, and not for a page that says it's elsewhere; an invite by email,
  // no site.
  await expect.poll(() => framers(candidate.invite_url), LOADED).toBe("'none'")
  await api(owner, "PUT", `/companies/companies/${company.id}/allowed-domains`, {
    domains: [`*.${DOMAIN}`],
  })
  // Polled: the page gives up on a slow lookup (3 s) and refuses framing, as it should.
  await expect.poll(() => framers(candidate.invite_url), LOADED).toBe(`*.${DOMAIN}`)
  await expect
    .poll(() => framers(candidate.invite_url, "https://elsewhere.example"), LOADED)
    .toBe("'none'")
  const byEmail = await invite(throwawayEmail("by-email"), true)
  await expect.poll(() => framers(byEmail.invite_url), LOADED).toBe("'none'")

  const { context, site } = await openSite(browser, baseURL!, candidate.invite_url)
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
  // The candidate's pledge, inside the company's site too.
  await frame.getByTestId("start-pledge").filter({ visible: true }).click()
  await expect(start).toBeEnabled()
  expect(await frameHeight()).toBe(settled)
  await start.click()
  await expect(frame.getByTestId("finish-interview").filter({ visible: true })).toBeVisible({
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
  // One frame (the second copy of the script did nothing), each event once, in order; every
  // message names its version.
  await expect(site.locator("iframe")).toHaveCount(1)
  // A dev server compiling the frame can take longer than the 20 s the script allows before
  // its timeout; that one is left out here and tested below.
  const loaded = async () => (await events(site)).filter((name) => name !== "error:timeout")
  await expect.poll(loaded, LOADED).toEqual(["ready", "started", `finished:${candidate.id}`])
  const versions = await site.evaluate(() =>
    (window as unknown as SiteWindow).messages.map((message) => message.version)
  )
  expect(versions.length).toBeGreaterThan(0)
  expect(new Set(versions)).toEqual(new Set([1]))
  await shot(site, "finished")
  await context.close()

  // An invite the company's site may not frame (sent by email): the frame never says it's ready,
  // so the site hears a timeout.
  const refused = await openSite(browser, baseURL!, byEmail.invite_url)
  await refused.site.clock.install()
  await refused.site.goto(`${SITE}/apply`)
  await expect(refused.site.locator("iframe")).toHaveCount(1)
  await refused.site.clock.runFor(21_000)
  await expect.poll(() => events(refused.site), LOADED).toEqual(["error:timeout"])
  await refused.context.close()

  // A link that's gone by the time the frame reads it: the frame tells the site why.
  const gone = await openSite(browser, baseURL!, candidate.invite_url)
  const token = new URL(candidate.invite_url).pathname.split("/").pop()
  await gone.context.route(`**/api/companies/invites/${token}`, (route) =>
    route.fulfill({ status: 404, json: { detail: "Not found" } })
  )
  await gone.site.goto(`${SITE}/apply`)
  await expect.poll(() => events(gone.site), LOADED).toEqual(["ready", "error:invite_unavailable"])
  await gone.context.close()
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
