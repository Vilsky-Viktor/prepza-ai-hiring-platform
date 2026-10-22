# The API reference's API tab: getting a key, signing in, errors, lists and the changelog.
API_TAB = """# API

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
items per request). A full page comes with a `Link` header to the next one,
`Link: <https://prepza.ai/api/v1/...>; rel="next"`; follow it until a response has none (the
page after a full one can be empty).

## Keeping your copy in sync

Interviews and candidates carry `updated_at`, when they last changed. To fetch only what changed,
pass `updated_since` to a list: it returns the items changed at that time or later, oldest
change first. For the next page, pass the last item's `updated_at` as `updated_since` and its
`id` as `after`, so items changed at the same moment are neither repeated nor missed (the
`Link` header's next page does this for you). Keep the
last pair and start from it next time. A candidate's progress while they answer doesn't change
`updated_at`; a removed candidate leaves the list, and the `candidate.removed` web hook event
says so.

## Retrying safely

Every request can be retried as it is, with nothing extra to send. Inviting an address that is
already invited, or has finished, returns that candidate as they are (`200` instead of `201`),
without another email or credits; an expired invite is sent again. Creating an interview with
the same request from the same key within 15 minutes returns the interview the first request
made, with `200`: `201` only ever means something new was made. A retry while the first request
is still running returns `409` (`request_in_progress`): wait a moment and retry.

## Errors

Failed requests return a standard HTTP status code and a JSON body with a `code` and a `detail`:
`{"detail": "Interview not found", "code": "not_found"}`. Branch on `code`, which never changes;
`detail` explains it for people, in the language of your `Accept-Language` header. For an invalid
request (`validation_failed`), `detail` is a list with one entry per bad field, which its `loc`
names. Each endpoint below lists the errors it can return. New codes can be added, so handle one
you don't know by its HTTP status.

| Code | Status | Meaning |
|---|---|---|
| `invalid_api_key` | 401 | The key is missing or not a key |
| `api_key_expired` | 401 | The key has expired |
| `key_creator_lost_access` | 401 | The key's creator is no longer an owner or admin |
| `missing_permission` | 403 | The key lacks the endpoint's permission |
| `not_found` | 404 | No such interview or candidate in your company |
| `insufficient_credits` | 402 | Not enough credits to invite |
| `interview_not_ready` | 409 | The interview's questions are still being made |
| `candidate_finished` | 409 | The candidate already finished |
| `candidate_started` | 409 | Extra time only before the candidate starts |
| `invited_without_sign_in` | 409 | prepza doesn't email a candidate invited with `sign_in` false |
| `company_suspended` | 409 | The company is suspended |
| `interview_quota_reached` | 409 | As many interviews without candidates as allowed |
| `request_in_progress` | 409 | The same request is still running |
| `idempotency_key_reused` | 422 | An `Idempotency-Key` sent before with another request |
| `return_url_off_domain` | 422 | `return_url` isn't on the verified domain |
| `validation_failed` | 422 | The request is invalid; `detail` names each field |
| `body_too_large` | 413 | The request body is too large |
| `rate_limited` | 429 | A rate or email limit; wait `Retry-After` seconds |
| `paused` | 503 | What the endpoint does is paused for a while |
| `ai_budget_used_up` | 503 | Today's AI budget is used up; `Retry-After` says until when |
| `maintenance` | 503 | prepza is down for maintenance |

Any other refusal carries its status's code: `bad_request`, `unauthorized`, `forbidden`,
`method_not_allowed`, `conflict` or `unavailable`.


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

## Changelog

Within `v1`, fields, optional parameters, error codes, enum values and event types are only ever
added. Anything retired first answers with `Deprecation` and `Sunset` headers and is listed here.

- 2026-10-22: every error carries a machine-readable `code` beside its `detail` (see Errors).
- 2026-10-22: a full page of a list sends a `Link` header to the next one; candidates carry
  their `interview_id`.
- 2026-10-22: a retried request that made nothing new answers `200`, not `201`.

"""
