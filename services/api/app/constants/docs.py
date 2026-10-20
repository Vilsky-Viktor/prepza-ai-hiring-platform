# The public API's description: its reference's API, web hooks and SDK tabs, each under its
# "# " title (the developer docs page splits it there; objects are the fourth tab).
API_TITLE = "prepza API"
API_VERSION = "1"
API_DESCRIPTION = """# API

The prepza API connects prepza to your own platform. Use it to create interviews from job
descriptions, invite candidates, remind, update or remove them, read their results, find a
candidate by email and read your credits, and receive a [web hook](/api-docs?tab=webhooks) as
soon as a candidate finishes.

## Getting an API key

1. Sign in to prepza as an owner or admin of your company.
2. Open **Hiring**, select your company and go to the **Integrations** tab.
3. In the **API** section, open the API page and select **New key**.
4. Name the key after the platform that will use it, choose when it expires (in 1, 3, 6 or 12
   months, or never), then select **New key**.
5. Copy the key and store it securely. It is shown only once: prepza keeps only a hash of it.

A company can have a limited number of keys; the API page refuses one more. An expired key
returns `401`; make a new one before it expires. Deleting a key on the same page revokes it immediately.

## Authentication

Send the key with every request in the `Authorization` header: `Authorization: Bearer pz_...`.
A key belongs to one company and acts on behalf of the member who created it, so invitations are
sent under that member's email limits. If the member leaves the company or is no longer an owner
or admin, the key stops working and requests return `401`.

## Example: inviting a candidate

Invite a candidate to an interview and get their invite link. Sending the same request again is
safe: it never invites them twice.

```bash
curl -X POST "https://prepza.ai/api/v1/interviews/$INTERVIEW_ID/candidates" \\
  -H "Authorization: Bearer $PREPZA_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "ada@example.com", "name": "Ada Lovelace"}'
```

```python
import os

import httpx

interview_id = "YOUR_INTERVIEW_ID"
api_key = os.environ["PREPZA_API_KEY"]

response = httpx.post(
    f"https://prepza.ai/api/v1/interviews/{interview_id}/candidates",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"email": "ada@example.com", "name": "Ada Lovelace"},
)
response.raise_for_status()
print(response.json()["invite_url"])
```

```typescript
const interviewId = "YOUR_INTERVIEW_ID"
const response = await fetch(
  `https://prepza.ai/api/v1/interviews/${interviewId}/candidates`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.PREPZA_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: "ada@example.com", name: "Ada Lovelace" }),
  },
)

if (!response.ok) {
  throw new Error((await response.json()).detail)
}

const candidate = await response.json()
console.log(candidate.invite_url)
```

## Rate limits and pagination

Your company's keys together have a limit of requests per minute; further requests return
`429` until the minute ends, with a `Retry-After` header giving the seconds left. List endpoints return the newest items first and accept `offset` and `limit` (up to 100
items per request).

## Keeping your copy in sync

Interviews and candidates carry `updated_at`, when they last changed. To fetch only what changed,
pass `updated_since` to a list: it returns the items changed at that time or later, oldest
change first. For the next page, pass the last item's `updated_at` as `updated_since` and its
`id` as `after`, so items changed at the same moment are neither repeated nor missed. Keep the
last pair and start from it next time. A candidate's progress while they answer doesn't change
`updated_at`; a removed candidate leaves the list, and the `candidate.removed` web hook event
says so.

## Retrying safely

Every request can be retried as it is, with nothing extra to send. Inviting an address that is
already invited, or has finished, returns that candidate as they are (`200` instead of `201`),
without another email or credits; an expired invite is sent again. Creating an interview with
the same request from the same key within 15 minutes returns the interview the first request
made. A retry while the first request is still running returns `409`: wait a moment and retry.

## Errors

Failed requests return a standard HTTP status code and a JSON body whose `detail` field describes
the problem. Each endpoint below lists the errors it can return.

## Results support a person's decision

A candidate's `grade`, `passed` and `signals` help a person decide; they are not a decision.
Don't reject candidates automatically on them: before rejecting anyone, a person should open the
candidate's full results (`results_url`) and review them.

## Invite links

Until a candidate finishes, they come with their invite link (`invite_url`), the same link the
invite email carries. Send it to them yourself if the email didn't reach them; only the invited
email can use it, unless they were invited with `sign_in` false. It's null once they've finished
or the invite has expired.

## Sending candidates from your own platform

When your platform already knows who the candidate is, invite them with `sign_in` false: prepza
sends no emails, and the `invite_url` opens the interview without signing in to prepza. Anyone
with that link can take the interview, so give it only to the candidate. Add a `return_url` on
your company's verified website domain to bring them back once they've finished, or [embed the
interview](/api-docs?tab=sdk) in your own page instead.

## Verified companies

Bringing candidates back to your site and [embedding the interview](/api-docs?tab=sdk) work only
on your company's verified website domain and its subdomains. To verify your company, select
**Verify** next to its name in prepza and enter its website. Once an owner or admin signs in with
a work email on that domain, prepza reviews the company and adds the verified badge; until then, a
`return_url` returns `422` and an [embedded interview](/api-docs?tab=sdk) isn't shown.

# Web hooks

Owners and admins can add a few web hook endpoints on the same API page. Each endpoint gets
every event below as a `POST` request: a candidate started, finished (with their results), wasn't
reached by the invitation email, expired or was removed, and an interview is ready. Ignore the
types you don't need. A candidate's results never change after they finish: a fixed question
applies only to candidates who start after the fix. Endpoints must use HTTPS and be reachable
from the public internet.

On the API page, **send test event** sends a signed `test` event to an endpoint at once, and the
**delivery log** shows its latest 20 sends: each event's type, when, and whether it was
delivered, the status the endpoint answered, or what went wrong.

Every request carries a `Prepza-Signature` header in the form `t=<timestamp>,v1=<signature>`. The
signature is the hex-encoded HMAC-SHA256 of `<timestamp>.<raw request body>`, computed with the
web hook's signing secret, which is shown once when the web hook is added. Verify the signature,
and reject requests whose timestamp is more than a few minutes old, before processing an event.
Pass the raw request body, as received, before any JSON parsing.

```python
import hashlib
import hmac
import time


def verify(secret: str, header: str, body: bytes, tolerance: int = 300) -> bool:
    # Whether a request came from prepza: its Prepza-Signature header and raw body.
    parts = dict(part.split("=", 1) for part in header.split(","))
    timestamp = int(parts["t"])
    expected = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()

    return abs(time.time() - timestamp) <= tolerance and hmac.compare_digest(
        expected, parts["v1"]
    )
```

```typescript
import { createHmac, timingSafeEqual } from "node:crypto"

/** Whether a request came from prepza: its Prepza-Signature header and raw body. */
export function verify(
  secret: string,
  header: string,
  body: string,
  tolerance = 300,
): boolean {
  const parts = Object.fromEntries(
    header.split(",").map((part) => part.split("=", 2)),
  )
  const timestamp = Number(parts.t)
  const expected = createHmac("sha256", secret)
    .update(`${timestamp}.${body}`)
    .digest("hex")
  const fresh = Math.abs(Date.now() / 1000 - timestamp) <= tolerance

  return (
    fresh &&
    parts.v1?.length === expected.length &&
    timingSafeEqual(Buffer.from(expected), Buffer.from(parts.v1))
  )
}
```

Respond with any `2xx` status within 10 seconds to confirm delivery. Other responses and timeouts
are retried with growing pauses, from 5 minutes up to 6 hours apart, for 3 days; after that the
web hook is paused: it gets no events, and the API page shows it as paused, until a test event
sent from there goes through. An event can occasionally arrive more than once; use its `id` to
ignore duplicates.

Each request body is a JSON object with the event's `id`, its `type`, `occurred_at` (when the
change happened, in ISO 8601) and its `data`. A retried event can arrive after a later one, so
order a candidate's events by `occurred_at`, not by when they arrive.

# SDK

Your page can show the interview itself, for a candidate invited with `sign_in` false. Your
server invites them and passes the `invite_url` to your page, which embeds it with prepza's
script; never put your API key in a page. The page must be on your company's verified website
domain (or a subdomain of it) and served over HTTPS: anywhere else the interview isn't shown.

```html
<div id="interview"></div>
<script src="https://prepza.ai/embed/v1.js"></script>
<script>
  // The candidate's invite_url, which your server got when it invited them.
  const candidateInviteUrl = "https://prepza.ai/invite/3fTq9xLk2VbN7wZr8YcP1mHd5sJ4gAe6uQo0RiKtEy"
  const interview = Prepza.embed({
    element: "#interview",
    url: candidateInviteUrl,
    theme: "dark",
    onReady: () => {},
    onStart: () => {},
    onFinish: ({ candidateId }) => {},
  })
</script>
```

`theme` is optional: `"light"` or `"dark"` always shows the interview in that theme, in your
company's colors for it (set on the company's **brand** tab); `"default"`, or none, the
candidate's own theme, or the one the invite asked for. The frame fits its height to the
interview. `onFinish` gets the candidate's `id`, so your page can take them on; their results come
with the `candidate.finished` web hook as usual. `interview.destroy()` removes the frame. While
the interview runs, the candidate should stay on it: leaving it, including for the rest of your
page, is recorded as a page leave."""
