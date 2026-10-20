import { expect, test } from "../fixtures";
import { API_URL } from "../constants";
import { api, createCompany, createInterview } from "../helpers/api";
import { failGeneration } from "../helpers/db";
import { ownerEmail, throwawayEmail } from "../helpers/users";

// Every API permission: the test calls every route.
const EVERY_PERMISSION = [
  "interviews:read",
  "interviews:create",
  "candidates:read",
  "candidates:invite",
  "candidates:change",
  "candidates:delete",
  "credits:read",
];

// A company's platform runs its hiring through the API: it invites a candidate safely twice,
// corrects them, gives extra time, reminds, finds them by email, reads the credits, removes
// them, and asks for a new interview under the app's own limits.
test("the API invites, updates, reminds, finds and removes a candidate", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const { key } = await api<{ key: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    { name: "Careers site", expiry: "1", permissions: EVERY_PERMISSION },
  );
  const headers = { Authorization: `Bearer ${key}` };
  const call = (method: string, path: string, data?: object, extra = {}) =>
    owner.request.fetch(`${API_URL}/v1${path}`, {
      method,
      headers: { ...headers, ...extra },
      data,
    });
  const email = throwawayEmail("api-candidate");
  const candidates = `/interviews/${interviewId}/candidates`;

  // A retry needs nothing from the client: the same invite again is the same candidate,
  // returned as they are (200), invited once.
  const first = await call("POST", candidates, { email });
  const again = await call("POST", candidates, { email });
  expect([first.status(), again.status()]).toEqual([201, 200]);
  const candidate = await first.json();
  expect((await again.json()).id).toBe(candidate.id);
  // An Idempotency-Key an older integration still sends keeps working; the same key with
  // another request is refused.
  const keyed = await call(
    "POST",
    candidates,
    { email },
    { "Idempotency-Key": "e2e-1" },
  );
  expect(keyed.status()).toBe(200);
  const reused = await call(
    "POST",
    candidates,
    { email: throwawayEmail("api-other") },
    { "Idempotency-Key": "e2e-1" },
  );
  expect(reused.status()).toBe(422);
  expect((await reused.json()).detail).toBe(
    "This Idempotency-Key was already used for a different request.",
  );

  const path = `${candidates}/${candidate.id}`;
  const updated = await call("PATCH", path, {
    name: "Anna Nowak",
    extra_time: 50,
  });
  expect(updated.status()).toBe(200);
  expect(await updated.json()).toMatchObject({
    name: "Anna Nowak",
    extra_time: 50,
  });

  // Syncing from the change: the updated candidate is listed as changed since then.
  const changedAt = (await updated.json()).updated_at;
  const changed = await call(
    "GET",
    `${candidates}?updated_since=${encodeURIComponent(changedAt)}`,
  );
  expect((await changed.json()).map((row: { id: string }) => row.id)).toEqual([
    candidate.id,
  ]);

  expect((await call("POST", `${path}/resend`)).status()).toBe(204);
  const found = await call(
    "GET",
    `/candidates?email=${encodeURIComponent(email)}`,
  );
  expect((await found.json()).map((row: { id: string }) => row.id)).toEqual([
    candidate.id,
  ]);

  const credits = await (await call("GET", "/credits")).json();
  expect(credits.reserved).toBeGreaterThan(0);

  // Invited without prepza's emails: there's no email to send again.
  const guest = await call("POST", candidates, {
    email: throwawayEmail("api-guest"),
    sign_in: false,
  });
  const guestId = (await guest.json()).id;
  expect((await call("POST", `${candidates}/${guestId}/resend`)).status()).toBe(
    409,
  );

  expect((await call("DELETE", path)).status()).toBe(204);
  expect((await call("GET", path)).status()).toBe(404);

  // A new interview follows the app's limits: an unpaid company with one waiting gets none.
  // (A second interview, without candidates, so nothing is generated for real.)
  const waiting = await createInterview(owner, company.id);
  await failGeneration(waiting, company.id);
  const made = await call("POST", "/interviews", {
    job_description:
      "Senior accountant: month-end close, IFRS reporting and audits.",
  });
  expect(made.status()).toBe(429);
});
