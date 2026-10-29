# Admin zone: Support

The Support tab of the [Admin zone](admin-zone.md).

For a complaint about an account, a company's top-ups or spending, an interview or a candidate, for someone who asks prepza to stop its emails, and for a company that impersonates another or abuses prepza. A search finds what the complaint is about; its page shows what support needs, and puts a company's credits right. A candidate's questions and answers are never shown: only facts about them.

- [Search](#search)
- [An account's page](#an-accounts-page)
- [A company's page](#a-companys-page)
- [An interview's page](#an-interviews-page)
- [A candidate's page](#a-candidates-page)
- [Emails](#emails)
- [Logs](#logs)

## Search

One box takes whatever the complaint gives (at most 300 characters), sent in the request body. It finds at most 20 results, each a prepza account, or a company, an interview or a candidate (an invite) with the company it belongs to:

- **a link or path from prepza's site,** on any host and under any language prefix: the deepest page it points at (`/companies/{id}`, `/interviews/{id}`, `/candidates/{invite id}`),
- **an id:** the company, interview or candidate invite that has it,
- **a Paddle transaction** (`txn_…`, from a receipt): the company the top-up paid into, as billing knows it,
- **an email address,** whatever its case: the account that signs in with it (accounts asks Firebase), then the companies with a member of that address and the candidates invited at it,
- **anything else:** the account with that id (from "copy id" in its menu or Settings) and the companies it's a member of, then companies whose name contains it; a company found both ways shows once. Only text that could be an account id (letters, digits, `-` and `_`, up to 128) is asked of library.

An account is titled by its address (by its id when it has none: a company's guest candidate). Each result opens its page, by its kind and id: an account's, a company's, an interview's or a candidate's. An id nothing has finds nothing.

## An account's page

- its address and when it was made, from accounts (Firebase); neither once the account is gone, as its memberships may outlive it,
- the companies it's a member of, with its role in each,
- the top-ups it paid for, newest first (at most 100): each with its company, what it cost (tax included) and when, from billing,
- what its AI calls cost in the last 30 days, and how many there were, from billing (`GET /billing/superadmin/ai-spend?user_id=`; the line is left out when billing doesn't answer),
- its email settings (below),
- when its address is on the suppression list (it bounced, marked an email as spam, or Resend suppressed it), on which nothing is sent to it, since when and why, with **Take off the list**, which takes it off Resend's suppression list too, so emails reach it again (when Resend keeps it, nothing changes and the page says the action failed) (`POST /notifications/superadmin/suppressed/lookup` and `/remove`, the address in the body).

There's a page for an id with an account or a membership; any other is "not found".

## A company's page

- its name, verification, verified domain, whether it's suspended, when it was made, and its members (email, role, whether they joined),
- its credits: the balance and how many are set aside for candidates who haven't finished,
- what its AI calls cost in the last 30 days, and how many there were (`GET /billing/superadmin/ai-spend?company_id=`),
- the credit history and the reserved credits, as the company's own billing tab shows them, with each top-up's invoice,
- its interviews, with their candidates count and status,
- its action log, newest first, in the same rows as the owner's **Action log** tab (one component): what a member did and about what (a candidate's email, an interview's title, a member's email, a key's or web hook's name), who they were ("A former member" once they've left), the date and time in the viewer's time zone, and whether the assistant, an AI app, the API or an ATS did it (see [Companies](companies.md#action-log)).

Its credits (the history), reserved credits, interviews, members and action log are each a page of their own, listed under Support in the admin zone's menu while the company is open (on a phone, the bar under the tabs that opens a menu of them), at `?page=reserved`, `?page=interviews`, `?page=members` and `?page=audit` (the credits at the company's own address; the older `?tab=` addresses lead there). The balance and the AI cost sit above each.

On phones, the actions take two rows (adjust credits and suspend side by side, then rename and delete), and the balance two lines. It can be:

- **suspended,** after a confirmation (see [Companies](companies.md#suspension)), and the suspension lifted,
- **renamed,**
- **deleted,** after a confirmation, with everything it has, as its owner would delete it,
- **given or charged credits:** an amount (up to 1,000,000 either way, not zero) and a note (up to 200 characters) that the company's credit history shows with the movement (reason `adjustment`). Billing refuses one that would take the available balance (the balance less the reserved credits) below zero. A key sent with it makes a repeated request count once.

## An interview's page

Its title, status (new, in process or hired), company, when it was made, its generation (and whether it failed), its topics by name (from library, never their questions), each question's time, the pass mark, and how many candidates it has. Below, its candidates newest first, as the company's list shows them: email, name, status, grade and when they were invited.

## A candidate's page

As the company's candidate list shows them, never their questions or answers:

- email, name, status, company and interview,
- when they were invited, when the invite was last sent, when they started and finished,
- grade and whether they passed, the extra time they were given (a percentage of the average time per question, which each question's own time is fitted from),
- their integrity signals, counted: page leaves, copy attempts and answers picked too fast,
- their credits, from billing: held (set aside), charged or released (given back); none when none were held,
- when the address is on the suppression list (it bounced, marked an email as spam, or Resend stopped sending to it), since when and why, with **Take off the list**, as on an account's page,
- the company emails stopped for the address (below).

An undelivered invite shows as the status `undelivered`; prepza records nothing about a delivered one.

## Emails

Stops the emails prepza sends to an address, for someone who asked by email rather than with a link (see [Unsubscribing](notifications.md#unsubscribing)). An address goes in the request body, never in a page or API address, which logs record.

- **An account's email settings,** on its page: as Settings → Emails shows them, each changed at once, and "Turn off all optional emails". Service emails can't be turned off. Product updates and offers can only be turned off here: consent to marketing is the user's own, so turning one on is refused ("Only the person can turn on product updates and offers."). An account without an address (a company's guest candidate) has none.
- **Emails from companies,** on a candidate's page, for their address: the companies that invited the address (companies' invites) or whose emails it stopped, by name, each "Emails are sent", "All emails stopped" (by a superadmin), "They stopped all emails themselves" (from an email's link) or "Reminders stopped for N invites":
  - "Stop emails" stops every email from that company to the address, only for a company that invited it.
  - "Resume emails" lets them through again (the person changed their mind), only after a superadmin's stop. The person's own stops, of all the company's emails or of an invite's reminders, stay: only they made them, and the row has no button for them.

Both are safe to repeat. A company that's gone isn't listed.

## Logs

Each search, each look at a page or its lists, and each action goes to the logs with the superadmin's id and what they looked at or did: the kind of query and the ids it found, the account, company, interview or candidate ids viewed, never the query or an email address. Adjustments and the actions above are warnings: "Credits of company {id} adjusted by {amount} by superadmin {id}". Also:

- An email settings change goes to the consent log (`email_consents`) with the source `admin` and the superadmin's id (`changed_by`), and to accounts' logs.
- Stopping or resuming a company's emails goes to notifications' logs with the superadmin's id, the company and the address's hash, never the address.

```
POST /companies/superadmin/support/search                                {query}
GET  /companies/superadmin/support/users/{user_id}
GET  /companies/superadmin/support/companies/{id}
GET  /companies/superadmin/support/companies/{id}/history                 ?offset&limit
GET  /companies/superadmin/support/companies/{id}/reserved                ?offset&limit
GET  /companies/superadmin/support/companies/{id}/interviews              ?offset&limit
GET  /companies/superadmin/support/companies/{id}/audit                   ?offset&limit
GET  /companies/superadmin/support/companies/{id}/invoice                 ?transaction_id
POST /companies/superadmin/support/companies/{id}/adjustments            {amount, note, key}
POST /companies/superadmin/companies/{id}/suspend | /unsuspend
PUT  /companies/superadmin/companies/{id}/name                            {name}
DELETE /companies/superadmin/companies/{id}
GET  /companies/superadmin/support/interviews/{id}
GET  /companies/superadmin/support/interviews/{id}/candidates             ?offset&limit
GET  /companies/superadmin/support/candidates/{invite id}
GET  /accounts/superadmin/emails/accounts/{user_id}
POST /accounts/superadmin/emails/lookup                                   {email}
PUT  /accounts/superadmin/emails/{user_id}/preferences                    {changes}
POST /notifications/superadmin/candidate-opt-outs/lookup                  {email}
PUT  /notifications/superadmin/candidate-opt-outs                         {email, company_id, stopped}
```

Behind them, internal routes:

- billing's `GET /internal/purchases/{transaction_id}` (whose wallet a top-up paid into), `GET /internal/purchases?buyer_id` (the top-ups someone paid for), `GET /internal/candidates/hold?key` (a candidate's credits) and `POST /internal/companies/{id}/adjustments`,
- accounts' `GET /internal/accounts/{user_id}` and `POST /internal/accounts/lookup` (`{email}`): an account's id, address and when it was made.
