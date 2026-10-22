import { expect, test } from "@playwright/test";

// The footer's developer docs open the reference, read from the API itself, in five tabs: the
// API (how to get a key, every route with what it returns), its web hooks, the SDK that embeds
// the interview, the MCP server and the objects. Names the API defines (routes, events, headers, fields) are
// its data, so they're matched; the page's own wording isn't. One test per tab, each opening its
// own pages, so none runs out of time behind another's.
test("the developer docs show the API with its routes", async ({ page }) => {
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
  await page.screenshot({ path: test.info().outputPath("api.png"), fullPage: true });

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
  await page.screenshot({ path: test.info().outputPath("webhooks.png"), fullPage: true });
});

// The script and how to embed the interview.
test("the developer docs show the SDK", async ({ page }) => {
  await page.goto("/api-docs?tab=sdk");
  await expect(page.locator("main pre").first()).toContainText("Prepza.embed(");
});

test("the developer docs show the objects", async ({ page }) => {
  await page.goto("/api-docs?tab=objects#Candidate");
  await expect(page.locator("#Candidate")).toContainText("results_url");
  await page.screenshot({ path: test.info().outputPath("objects.png"), fullPage: true });
});

// The MCP tab: the server's address on this site, the example agents in Python and TypeScript
// (one language menu switches every example), and the tools exactly as the server lists them.
test("the MCP tab shows the server, the example agents and the server's tools", async ({ page }) => {
  await page.goto("/api-docs?tab=mcp");
  // The server's own list, read the way the page reads it (the browser reaches the site).
  const { tools } = (await page.evaluate(() =>
    fetch("/api/assistant/mcp/tools").then((response) => response.json()),
  )) as { tools: { name: string; key_permission: string | null }[] };
  await expect(page.locator('main nav a[aria-current="page"]:visible')).toHaveAttribute("href", "/api-docs?tab=mcp");
  await expect(page.getByRole("main").getByRole("textbox").first()).toHaveValue(`${new URL(page.url()).origin}/mcp`);

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

  // Its sections are tabs: the chosen one controls the panel shown, which it names (WAI-ARIA tabs).
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
  await page.screenshot({ path: test.info().outputPath("mcp.png"), fullPage: true });
});
