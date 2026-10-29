import { expect, test } from "../fixtures";
import { api, createCompany, createInterview } from "../helpers/api";
import { visit } from "../helpers/navigation";
import { throwawayEmail } from "../helpers/users";

// An editable title needs at least 3 characters: a shorter one isn't saved, and says why. A
// company name needs at least 2 (EY and 3M are companies): one letter is refused under the
// field, and no other company is made. The rules themselves are the API's (test_company_names.py
// and the interview title's schema).
test("a short test title or company name is refused, saying why", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("title-length"));
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);

  await visit(owner, `/companies/${company.id}/interviews/${interviewId}`);
  const heading = owner.getByRole("heading", { level: 1 });
  const before = await heading.innerText();
  // The pencil after the title.
  await heading.getByRole("button").click();
  const input = owner.getByRole("textbox");
  await input.fill("ab");
  await input.press("Enter");

  await expect(owner.getByText("Use at least 3 characters.")).toBeVisible();
  await expect(input).toHaveValue("ab");
  await input.press("Escape");
  await expect(heading).toHaveText(before);
  await owner.reload();
  await expect(heading).toHaveText(before);

  await visit(owner, "/companies");
  await owner.getByTestId("new-company").click();
  const dialog = owner.getByRole("dialog");
  const name = dialog.getByRole("textbox");
  await name.fill("A");
  // Create, the dialog's last button.
  await dialog.getByRole("button").last().click();

  await expect(name).toHaveAttribute("aria-invalid", "true");
  await expect(dialog.locator("#company-name-error")).toHaveText(
    "Use at least 2 characters.",
  );
  await expect(owner).toHaveURL(/\/companies$/);
  expect(await api<{ id: string }[]>(owner, "GET", "/companies/companies")).toEqual([
    expect.objectContaining({ id: company.id }),
  ]);
});
