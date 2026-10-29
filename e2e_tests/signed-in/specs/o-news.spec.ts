import type { Page } from "@playwright/test";

import { expect, test } from "../fixtures";
import { api } from "../helpers/api";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { randomId, throwawayEmail } from "../helpers/users";

type Post = { id: string; title: string };

type Campaign = {
  id: string;
  kind: string;
  link: string | null;
  texts: { en: { subject: string; text: string } };
};

/** The bell's entry opening the post, once it's there (the notification comes through Pub/Sub). */
async function bellEntry(page: Page, postId: string) {
  const entry = page.getByRole("menu").locator(`a[href="/news#${postId}"]`);

  await expect(async () => {
    await page.reload();
    await page.getByTestId("notifications").click();
    await expect(entry).toBeVisible({ timeout: 5_000 });
  }).toPass({ timeout: 60_000 });

  return entry;
}

// A superadmin writes a news post in the admin zone's news tab: the text's limit is counted down
// and enforced by the API, the post shows on the news page with its date and in a user's bell,
// it's turned into a product update campaign from its row, and it's edited and deleted from its
// row, leaving the bell. Posts and campaigns left by a failed run are deleted at the end. A post
// reaches every user's bell, so the test is tagged @global: it runs alone, after the other tests
// (signed-in.sh).
test("superadmin writes, edits and deletes a news post", { tag: "@global" }, async ({
  signInAs,
  signInSuperadmin,
}) => {
  // A user whose account is older than the post: its bell gets it.
  const reader = await signInAs(throwawayEmail("reader"));
  const superadmin = await signInSuperadmin();
  const title = `E2E news ${randomId()}`;
  const edited = `${title} edited`;

  try {
    await visit(superadmin, "/superadmin/news");

    await superadmin.getByTestId("new-post").click();
    const dialog = superadmin.getByRole("dialog");
    // The title, then the text (the date field between them isn't a textbox), its characters
    // left counted under it, and Save.
    const titleField = dialog.getByRole("textbox").first();
    const text = dialog.getByRole("textbox").last();
    const left = dialog.locator("[aria-live=polite]");
    const save = dialog.locator("button[type=submit]");
    await expect(left).toContainText("500");
    await titleField.fill(title);
    // The field stops at 500 characters; past it, the API refuses with its own message.
    await text.evaluate((field) => field.removeAttribute("maxlength"));
    await text.fill("x".repeat(501));
    await save.click();
    await expect(superadmin.getByText(/at most 500 characters/)).toBeVisible();
    await expect(dialog).toBeVisible();

    await text.fill("First line.\nSecond line.");
    await expect(left).toContainText("476");
    await shot(superadmin, "news-dialog");
    await save.click();
    await expect(dialog).toBeHidden();
    const row = superadmin.locator("li", { hasText: title });
    await expect(row).toBeVisible();
    await shot(superadmin, "news-tab");

    const today = new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    await visit(superadmin, "/news");
    const post = superadmin.locator("article", { hasText: title });
    await expect(post.getByRole("heading", { level: 2 })).toHaveText(
      `${title}.`,
    );
    await expect(
      post.getByRole("heading").locator("span.text-primary"),
    ).toHaveText(".");
    await expect(post.locator("time")).toHaveText(today);
    await expect(post.getByText("First line.")).toBeVisible();
    await shot(superadmin, "news-page");

    const [{ id: postId }] = (
      await api<Post[]>(superadmin, "GET", "/site/superadmin/news?limit=100")
    ).filter((item) => item.title === title);

    // In the user's bell, named by its title, opening the post.
    await visit(reader, "/companies");
    await expect(await bellEntry(reader, postId)).toContainText(title);
    await shot(reader, "news-bell");

    // The row's buttons: send as a campaign, edit, then delete. The campaign is a product
    // update with the post's title, text and a button to it, opened to check and send.
    await visit(superadmin, "/superadmin/news");
    await superadmin
      .locator("li", { hasText: title })
      .getByRole("button")
      .first()
      .click();
    // The dev server may compile the campaign's page first.
    await expect(superadmin).toHaveURL(
      /\/superadmin\/campaigns\/[0-9a-f-]{36}$/,
      { timeout: 90_000 },
    );
    const campaignId = superadmin.url().split("/").pop() ?? "";
    const campaign = await api<Campaign>(
      superadmin,
      "GET",
      `/notifications/superadmin/campaigns/${campaignId}`,
    );
    expect([
      campaign.kind,
      campaign.link,
      campaign.texts.en.subject,
      campaign.texts.en.text,
    ]).toEqual([
      "updates",
      `/news#${postId}`,
      title,
      "First line.\nSecond line.",
    ]);
    await api(
      superadmin,
      "DELETE",
      `/notifications/superadmin/campaigns/${campaignId}`,
    );

    await visit(superadmin, "/superadmin/news");
    await superadmin
      .locator("li", { hasText: title })
      .getByRole("button")
      .nth(1)
      .click();
    await expect(titleField).toHaveValue(title);
    await titleField.fill(edited);
    await save.click();
    await expect(dialog).toBeHidden();
    await expect(superadmin.locator("li", { hasText: edited })).toBeVisible();

    await superadmin
      .locator("li", { hasText: edited })
      .getByRole("button")
      .last()
      .click();
    const confirm = superadmin.getByRole("dialog");
    await expect(confirm).toBeVisible();
    await shot(superadmin, "news-delete");
    await confirm.getByRole("button").last().click();
    await expect(superadmin.locator("li", { hasText: edited })).toHaveCount(0);
    await visit(superadmin, "/news");
    await expect(superadmin.locator("article", { hasText: title })).toHaveCount(
      0,
    );

    // Gone from the bell with the post, once the bell has asked again.
    const fed = reader.waitForResponse((response) =>
      /\/notifications\/me(\?|$)/.test(response.url()),
    );
    await reader.reload();
    await fed;
    await reader.getByTestId("notifications").click();
    await expect(reader.getByRole("menu")).toBeVisible();
    await expect(
      reader.getByRole("menu").locator(`a[href="/news#${postId}"]`),
    ).toHaveCount(0);
  } finally {
    const posts = await api<Post[]>(
      superadmin,
      "GET",
      "/site/superadmin/news?limit=100",
    );

    for (const left of posts.filter((item) => item.title.startsWith(title))) {
      await api(superadmin, "DELETE", `/site/superadmin/news/${left.id}`);
    }
  }
});
