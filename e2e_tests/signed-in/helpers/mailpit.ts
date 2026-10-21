import type { APIRequestContext } from "@playwright/test";

// The local stack's Mailpit, where every email goes without a Resend key (the test process is
// on the stack's network).
const MAILPIT = process.env.MAILPIT_URL ?? "http://mailpit:8025";

type Message = { ID: string; Subject: string; To: { Address: string }[] };

/** The emails to `address` whose subject is `subject`. */
export async function mails(
  request: APIRequestContext,
  address: string,
  subject: string,
) {
  const response = await request.get(`${MAILPIT}/api/v1/search`, {
    params: { query: `to:"${address}" subject:"${subject}"` },
  });
  const found = (await response.json()) as { messages: Message[] };

  return found.messages.filter((message) => message.Subject === subject);
}

/** Every email to `address`. */
export async function mailsTo(request: APIRequestContext, address: string) {
  const response = await request.get(`${MAILPIT}/api/v1/search`, {
    params: { query: `to:"${address}"` },
  });

  return ((await response.json()) as { messages: Message[] }).messages;
}

/** One email's plain text. */
export async function mailText(request: APIRequestContext, id: string) {
  const response = await request.get(`${MAILPIT}/api/v1/message/${id}`);

  return ((await response.json()) as { Text: string }).Text;
}

/** One email's HTML. */
export async function mailHtml(request: APIRequestContext, id: string) {
  const response = await request.get(`${MAILPIT}/api/v1/message/${id}`);

  return ((await response.json()) as { HTML: string }).HTML;
}

/** Deletes the emails the test made. */
export async function deleteMails(
  request: APIRequestContext,
  messages: Message[],
) {
  if (messages.length === 0) {
    return;
  }

  await request.delete(`${MAILPIT}/api/v1/messages`, {
    data: { IDs: messages.map((message) => message.ID) },
  });
}
