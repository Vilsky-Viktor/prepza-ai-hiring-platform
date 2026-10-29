import { expect, type Page, test } from "@playwright/test";

import { shot } from "./helpers/screenshots";

// The footer's developer docs open the reference, read from the API itself, in five tabs: the
// API (how to get a key, every route with what it returns), its web hooks, the SDK that embeds
// the interview, the MCP server (with pages of its own) and the objects. Names the API defines (routes, events, headers, fields) are
// its data, so they're matched; the page's own wording isn't. One test per tab, each opening its
// own pages, so none runs out of time behind another's.
test("the developer docs show the API with its routes", async ({ page }) => {
  // Every route's examples make the page long: its full-page picture on a phone takes a while.
  test.setTimeout(120_000);
  await page.goto("/");
  // The footer's link leads to the page; opened directly, so a click before the page is ready
  // can't miss it.
  await expect(page.locator('footer a[href="/api-docs"]')).toHaveCount(1);
  await page.goto("/api-docs");
  await expect(page.getByRole("heading", { level: 1 })).not.toBeEmpty();
  // The menu's pages, in its order: once each, from the side menu and the phone's tabs.
  const hrefs = await page
    .locator("main nav a")
    .evaluateAll((links) => [...new Set(links.map((link) => link.getAttribute("href")))]);
  expect(hrefs).toEqual([
    "/api-docs",
    "/api-docs?tab=webhooks",
    "/api-docs?tab=sdk",
    "/api-docs?tab=mcp",
    "/api-docs?tab=objects",
  ]);
  await expect(page.locator('main nav a[aria-current="page"]:visible')).toHaveAttribute("href", "/api-docs");

  // The steps to a key, as a numbered list.
  expect(await page.locator("main ol").first().locator("li").count()).toBeGreaterThan(1);
  // The base URL to copy and the routes, each with its method.
  await expect(page.getByRole("main").getByRole("textbox").first()).toHaveValue(/\/api\/v1$/);
  const routes = page.locator("main article").filter({ has: page.getByText(/^(GET|POST|PATCH|DELETE)$/) });
  // Every operation the public API defines, in its order: the spec is the source of truth.
  const spec = (await page.evaluate(() =>
    fetch("/api/v1/openapi.json").then((response) => response.json()),
  )) as { paths: Record<string, Record<string, unknown>> };
  const operations = Object.entries(spec.paths).flatMap(([path, methods]) =>
    Object.keys(methods).map((method) => `${method.toUpperCase()} ${path}`),
  );
  expect(operations.length).toBeGreaterThan(0);
  await expect(routes).toHaveCount(operations.length);
  const shown = await routes.evaluateAll((articles) =>
    articles.map((article) => {
      const method = [...article.querySelectorAll("header *")].find((part) =>
        /^(GET|POST|PATCH|DELETE)$/.test(part.textContent?.trim() ?? ""),
      );

      return `${method?.textContent?.trim()} ${article.querySelector("header code")?.textContent?.trim()}`;
    }),
  );
  expect(shown).toEqual(operations);
  await expect(
    routes.locator("header code").filter({ hasText: /^\/interviews\/\{interview_id\}\/candidates$/ }).first(),
  ).toBeVisible();
  await shot(page, "api", true);

  // Links are checked, then opened directly (in the tests below), so a click before the page is
  // ready can't miss: a mention of the web hook, in the API's text, opens its tab, and a type
  // its object on the objects tab.
  await expect(page.locator('main div[lang] a[href="/api-docs?tab=webhooks"]').first()).toBeVisible();
  await expect(page.locator('main a[href="/api-docs?tab=objects#Candidate"]').first()).toBeVisible();
});

// How to check a request, and the events.
test("the developer docs show the web hooks and their events", async ({ page }) => {
  await page.goto("/api-docs?tab=webhooks");
  await expect(page.locator('main nav a[aria-current="page"]:visible')).toHaveAttribute(
    "href",
    "/api-docs?tab=webhooks",
  );
  const code = page.locator("main code");
  await expect(code.filter({ hasText: /^Prepza-Signature$/ }).first()).toBeVisible();
  await expect(code.filter({ hasText: /^candidate\.finished$/ }).first()).toBeVisible();
  // A finished candidate's results never change, so nothing is sent after it.
  await expect(code.filter({ hasText: /^candidate\.rescored$/ })).toHaveCount(0);
  // Each event's body is shown as it's sent: its id, type and time around the data.
  await expect(page.locator("main").getByText("occurred_at", { exact: true }).first()).toBeVisible();
  await shot(page, "webhooks", true);
});

// The script and how to embed the interview.
test("the developer docs show the SDK", async ({ page }) => {
  await page.goto("/api-docs?tab=sdk");
  await expect(page.locator("main pre").first()).toContainText("Prepza.embed(");
});

test("the developer docs show the objects", async ({ page }) => {
  await page.goto("/api-docs?tab=objects#Candidate");
  await expect(page.locator("#Candidate")).toContainText("results_url");
  await shot(page, "objects", true);
});

// The MCP tab's own pages, in the docs' side menu (in the page on a phone too, where it's hidden):
// the overview, each AI app's, the tools and the example agents.
const MCP_PAGES = [
  "/api-docs?tab=mcp",
  ...["claude", "chatgpt", "gemini-cli", "cursor", "vs-code", "le-chat", "tools", "frameworks"].map(
    (id) => `/api-docs?tab=mcp&page=${id}`,
  ),
];

// The docs' side menu: the only menu that lists the objects tab on an MCP page.
function sideMenu(page: Page) {
  return page.locator('main nav:has(a[href="/api-docs?tab=objects"])');
}

/** The MCP pages in the side menu, in its order, and the one marked open. */
async function expectMcpMenu(page: Page, open: string) {
  const hrefs = await sideMenu(page)
    .locator('a[href^="/api-docs?tab=mcp"]')
    .evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  expect(hrefs).toEqual(["/api-docs?tab=mcp", ...MCP_PAGES]);
  await expect(sideMenu(page).locator('a[aria-current="page"]')).toHaveAttribute("href", open);
}

// The MCP tab opens on its overview: the server's address on this site and the rules with the
// server's own limits; the tools and the examples are pages of their own. An unknown page lands
// on the overview too.
test("the MCP tab opens on its overview with its own pages in the menu", async ({ page }) => {
  for (const address of ["/api-docs?tab=mcp", "/api-docs?tab=mcp&page=unknown"]) {
    await page.goto(address);
    await expectMcpMenu(page, "/api-docs?tab=mcp");
  }
  const { limits } = (await page.evaluate(() =>
    fetch("/api/assistant/mcp/tools").then((response) => response.json()),
  )) as { limits: { calls_per_minute: number; writes_per_hour: number } };
  await expect(page.getByRole("main").getByRole("textbox").first()).toHaveValue(`${new URL(page.url()).origin}/mcp`);
  const rules = page.locator("main div[lang]");
  await expect(rules).toContainText(String(limits.calls_per_minute));
  await expect(rules).toContainText(String(limits.writes_per_hour));
  await expect(page.getByTestId("mcp-tool")).toHaveCount(0);
  await expect(page.locator("main pre")).toHaveCount(0);
  await shot(page, "mcp", true);
});

// On a wide screen the menu's pages open from it, each at its own address.
test("the MCP tab's pages open from the side menu", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp");
  for (const href of [MCP_PAGES[3], MCP_PAGES[7], MCP_PAGES[0]]) {
    // The last link to it: the overview's address is the MCP tab's too.
    await sideMenu(page).locator(`a[href="${href}"]`).last().click();
    await expect(page).toHaveURL(href);
    await expectMcpMenu(page, href);
  }
});

// An AI app's page: the server's address, then its steps, with this site's address in its file.
test("an AI app's MCP page shows its setup", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp&page=cursor");
  await expectMcpMenu(page, "/api-docs?tab=mcp&page=cursor");
  const origin = new URL(page.url()).origin;
  await expect(page.getByRole("main").getByRole("textbox").first()).toHaveValue(`${origin}/mcp`);
  await expect(page.locator("main pre")).toContainText(`${origin}/mcp`);
  await page.goto("/api-docs?tab=mcp&page=claude");
  expect(await page.locator("main div[lang] ol li").count()).toBeGreaterThan(1);
});

// The tools exactly as the server lists them.
test("the MCP tools page lists the server's tools", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp&page=tools");
  await expectMcpMenu(page, "/api-docs?tab=mcp&page=tools");
  // The server's own list, read the way the page reads it (the browser reaches the site).
  const { tools } = (await page.evaluate(() =>
    fetch("/api/assistant/mcp/tools").then((response) => response.json()),
  )) as { tools: { name: string; key_permission: string | null }[] };

  // Every tool, in the server's order, with the API key permission it needs where it has one.
  const rows = page.getByTestId("mcp-tool");
  await expect(rows).toHaveCount(tools.length);
  await expect(rows.locator("code:first-child")).toHaveText(tools.map((tool) => tool.name));
  const withKey = tools.findIndex((tool) => tool.key_permission);
  await expect(rows.nth(withKey)).toContainText(tools[withKey].key_permission!);
  // What's new since the app's last check: a key needs candidates:read for it.
  const updates = tools.findIndex((tool) => tool.name === "get_updates");
  expect(tools[updates]?.key_permission).toBe("candidates:read");
  await expect(rows.nth(updates)).toContainText("candidates:read");
});

// The example agents in Python and TypeScript (one language menu switches every example), each
// framework a tab.
test("the MCP agent frameworks page shows the example agents", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp&page=frameworks");
  await expectMcpMenu(page, "/api-docs?tab=mcp&page=frameworks");

  // The frameworks are tabs: the chosen one controls the panel shown, which it names (WAI-ARIA tabs).
  const selected = page.getByRole("main").getByRole("tab", { selected: true }).first();
  const panel = page.getByRole("tabpanel").first();
  await expect(selected).toHaveAttribute("aria-controls", (await panel.getAttribute("id"))!);
  await expect(panel).toHaveAccessibleName((await selected.innerText()).trim());

  // The examples start in Python; picking TypeScript in one editor switches them all (the docs'
  // own menus, not the page menu's "…" on a phone).
  const menus = page.locator('main div[lang] [aria-haspopup="menu"]');
  const editors = page.locator("main pre");
  await expect(menus.first()).toHaveText("python");
  await expect(editors.first()).toContainText("from mcp");
  await menus.first().click();
  await page.getByRole("menu").getByRole("menuitemradio").nth(1).click();
  await expect(menus.first()).toHaveText("typescript");
  await expect(editors.first()).toContainText("@modelcontextprotocol/sdk");
  const languages = await menus.evaluateAll((items) => items.map((item) => item.textContent?.trim()));
  expect(new Set(languages)).toEqual(new Set(["typescript"]));
  await shot(page, "mcp-frameworks", true);
});

// Code that scrolls sideways is reached from the keyboard: Tab from the editor's copy button
// lands on the code, a named region, so the arrow keys can scroll it.
test("a code box takes keyboard focus after its copy button", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp&page=frameworks");
  const code = page.getByRole("main").getByRole("region").first();
  await expect(code).toHaveAccessibleName(/.+/);
  await code.locator("xpath=preceding-sibling::div[1]//button").last().focus();
  await page.keyboard.press("Tab");
  await expect(code).toBeFocused();
});
