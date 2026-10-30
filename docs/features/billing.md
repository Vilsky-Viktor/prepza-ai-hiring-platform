# Credits and payments

Companies pay per candidate from a wallet of credits. There's no paid subscription: the optional automatic top-up saves the card through Paddle as a $0 subscription, and charges only the top-ups.

- [Credits](#credits)
- [Top-ups](#top-ups)
- [Automatic top-up](#automatic-top-up)
- [Referrals](#referrals)
- [A company's billing tab](#a-companys-billing-tab)
- [Refunds and chargebacks](#refunds-and-chargebacks)
- [Missed web hooks](#missed-web-hooks)
- [Who reaches a company's payments](#who-reaches-a-companys-payments)
- [Deleting a company](#deleting-a-company)
- [AI usage and limit hits](#ai-usage-and-limit-hits)
- [Currencies](#currencies)
- [Setting up Paddle](#setting-up-paddle)

## Credits

- Credits never expire. Larger top-ups buy them for less money (see [Top-ups](#top-ups)), so a credit has no fixed price.
- A company pays 500 credits ($5, €5, £4 and so on: see [Top-ups](#top-ups)) per candidate who answers at least one question: picks an answer, not lets its time run out.
- Generating an interview is free.
- Only what works is charged: a candidate's credits are set aside on invite and given back if they never answer.
- A candidate removed before finishing (revoked, with their interview deleted, or deleting their own account) is charged by the same rule, if they picked an answer to at least one question (rounds' `picked` count); otherwise their credits come back.
- Credits set aside for an invite that then fails (the email limits, saving it, starting it, or billing's answer lost on the way) come back at once: a new invite's, or an expired one's sent again or started again (expiry won't release an expired invite a second time). An invite's earlier hold stays.
- An automatic top-up that a hold calls for is charged before billing answers the hold (Cloud Run slows the CPU once an answer is sent, so nothing runs after it), waited for at most 5 seconds (`AUTO_TOP_UP_WAIT_SECONDS`), so an invite never waits long on Paddle; a charge cut off counts as one whose answer was lost, which its web hook settles.
- Each invite has its own hold, so a candidate removed and invited again is charged again when they finish. Its key is the invite's own, `{interview_id}:{random}` (companies' `hold_key`), never the candidate's email, so billing keeps no candidate's email (the keys made before were rewritten that way, by billing's migration 0011 and companies' 0036 with `prepza_common.limits.credit_keys`).
- A company runs low below 500 credits available (balance less what's set aside) when no automatic top-up refills it. Notifications reads those companies for its reminder emails, and the assistant's `get_updates` for AI apps, only its own companies' (`GET /internal/companies/low?ids=`, each with the credits available and the candidates they pay for), and only for owners and admins, or an API key with `credits:read` ([AI apps over MCP](mcp.md#whats-new-get_updates)).
- Whenever a company gets credits (a top-up, a referral reward, a chargeback reversed), billing publishes `credits.added`: candidates its ATSs sent that weren't invited for lack of credits are invited then (see [ATS integrations](ats.md)).
- A person's first company gets 1,500 credits, enough for 3 candidates; on the site, creating it asks them to show they're a person first ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)). The credits come once per owner's email, so creating any company needs a verified email: a sign-in that doesn't verify it (GitHub) is told to confirm it first, with the link sent when they signed in, and one confirmed meanwhile counts without signing in again.
- The welcome gift is given once per inbox: case, a `+tag` and Gmail's dots don't make a new one (`src/billing/helpers/gifts.py` in billing). A new company asks for it up to 3 times, with the same company: billing gives it once per company, so an answer lost on the way neither loses the gift nor the referral. Only when every try fails is the company removed again, so its name stays free.

Until its first top-up, a company can have 1 generated interview waiting without a candidate before it generates another, and generates at most 3 a day; after it, 5 waiting and 10 a day. Interviews copied from templates don't count, and retrying a failed generation isn't a new one.

## Top-ups

Large top-ups buy candidates for less: each level has its own price per candidate in each currency (`CANDIDATE_PRICES` in `src/billing/constants/products.py`), round prices of their own rather than a conversion (see [Currencies](#currencies)).

Per candidate, in a top-up of 10–49 / 50–199 / 200–499 / 500–1,000 candidates; the fixed top-ups buy 10, 50, 200 and 500 (count × price):

| Currency | Per candidate | Fixed top-ups | Next level from |
|---|---|---|---|
| USD | $5 / 4 / 3 / 2 | $50 / 200 / 600 / 1,000 | 40, 150, 334 |
| EUR | €5 / 4 / 3 / 2 | €50 / 200 / 600 / 1,000 | 40, 150, 334 |
| GBP | £4 / 3 / 2.25 / 1.50 | £40 / 150 / 450 / 750 | 38, 150, 334 |
| CAD | CA$7 / 5.50 / 4 / 2.75 | CA$70 / 275 / 800 / 1,375 | 40, 146, 344 |
| AUD | A$7.50 / 6 / 4.50 / 3 | A$75 / 300 / 900 / 1,500 | 40, 150, 334 |
| ILS | ₪18 / 15 / 11 / 7.50 | ₪180 / 750 / 2,200 / 3,750 | 42, 147, 341 |
| PLN | 18 / 15 / 11 / 7.50 zł | 180 / 750 / 2,200 / 3,750 zł | 42, 147, 341 |
| CHF | CHF 4.50 / 3.50 / 2.60 / 1.75 | CHF 45 / 175 / 520 / 875 | 39, 149, 337 |
| JPY | ¥750 / 600 / 450 / 300 | ¥7,500 / 30,000 / 90,000 / 150,000 | 40, 150, 334 |
| KRW | ₩7,000 / 5,500 / 4,000 / 2,750 | ₩70,000 / 275,000 / 800,000 / 1,375,000 | 40, 146, 344 |
| TWD | NT$160 / 130 / 95 / 65 | NT$1,600 / 6,500 / 19,000 / 32,500 | 41, 147, 343 |
| HKD | HK$40 / 31 / 23 / 16 | HK$400 / 1,550 / 4,600 / 8,000 | 39, 149, 348 |
| THB | ฿170 / 135 / 100 / 70 | ฿1,700 / 6,750 / 20,000 / 35,000 | 40, 149, 350 |
| SGD | S$6.50 / 5.30 / 4 / 2.65 | S$65 / 265 / 800 / 1,325 | 41, 151, 332 |
| INR | ₹420 / 340 / 250 / 170 | ₹4,200 / 17,000 / 50,000 / 85,000 | 41, 148, 340 |

"Next level from": the counts from which a top-up buys the next level's smallest one instead (below), worked out from each currency's own prices.

These fixed top-ups (keys `topup_50` to `topup_1000`, kept from when they were dollar amounts) are what automatic top-up buys; the pricing and home pages show their prices. Saved automatic top-ups were moved to them by billing's migration 0012, each threshold keeping its number of candidates.

The top-up dialog (on the top-up page and a company's billing tab and header) buys any number of candidates from 10 to 1,000 instead:

- A slider with one equal part per price level (10–49, 50–199, 200–499 and 500–1,000 candidates), each labelled with its price per candidate in the company's currency; the count shows over the knob. Arrow keys move one candidate, Page Up and Page Down ten, Home and End to the ends.
- Under it, what the count costs, as three cards: the price, the credits (500 a candidate) and the candidates.
- Never more than the next level: when the count at its level's price costs at least the next level's smallest top-up (50 for $200, 200 for $600, 500 for $1,000), it buys that instead, at that price, and the dialog says so ("50 candidates for the same price"). In US dollars 40–49 buy 50, 150–199 buy 200 and 334–499 buy 500; other currencies' steps are in the table above.
- Billing decides all of it (`custom_top_up` in `src/billing/helpers/credits.py`), in the company's currency: its catalog (`custom`) gives the range, whether it's on sale (Paddle's product for it is set), and each level's first count, price per candidate and the count from which it buys the next level (`upgrade_from`). The dialog only displays and multiplies.
- Top up sends the count (`POST /companies/{id}/billing/checkout` with `{"candidates": N}`); billing works out again what it buys in the company's currency, refuses a count out of the range ("Choose from 10 to 1,000 candidates.", 422) or a sale before the product is set ("This top-up isn't available", 422), and makes the checkout: one item named in the buyer's interface language, which Paddle shows at checkout and on the invoice ("1,000 candidates", "1.000 Kandidaten", "50 кандидатов": the number written as that language writes it, the noun in its plural form; companies passes the language the site sends as `Accept-Language`), with its price made in the transaction, under the `PADDLE_PRODUCT_CANDIDATES` product, in that currency only (and the transaction's `currency_code`), tax added on top (`tax_mode: external`), quantity fixed at 1, so the buyer can't change what they buy. What it buys goes in the price's custom data (`candidates`, or a fixed top-up's `top_up` key for automatic top-up), the wallet and the buyer in the transaction's.
- The webhook grants those candidates (500 credits each) for a paid line of that product, the same in any currency, never anything the browser sent; a count out of the range grants nothing and is logged as an error, to refund. The money kept is what Paddle charged: the line's subtotal and the transaction's currency.
- Under the slider, the automatic top-up as a card, then "This company pays in USD. **Change**" (the company's currency, linking to its billing tab).

- Top up on the top-up page, for any company you belong to.
- Billing makes each top-up's checkout (a Paddle transaction naming the company and the buyer), after checking with companies that the buyer is its owner or an admin (`POST /companies/{id}/billing/checkout`); the browser only opens it, so it can't send the money to another wallet or record someone else as the buyer. A paid transaction billing didn't make (its origin isn't `api`), or one into a company deleted meanwhile, adds no credits and is logged as an error, to refund.
- Paddle's checkout doesn't offer a discount code field.
- Paddle's checkout opens over the page the buyer is on, in the site's light or dark theme and language (English where Paddle doesn't have it), as one page.
- Top up closes the top-up dialog once the checkout shows, so only the checkout is open.
- When Paddle completes the payment (`checkout.completed` in Paddle.js), its checkout closes and a dialog on the same page says the payment went through: "Payment received" for a top-up, "Automatic top-up is on" for the card that turns it on. Nothing is added to the address, and one checkout shows it once.
- The home and pricing pages show the prices, their range and the free candidates as billing's catalog (`/billing/catalog`) gives them, in the visitor's currency (see [Currencies](#currencies)). Kept 5 minutes; when billing can't answer and nothing is kept, the pricing page shows its title, intro and Top up with "Prices aren't available right now" instead of the list, rather than an empty or error page.

When a payment fails in Paddle's checkout (a declined card, a failed Google Pay, Apple Pay or PayPal payment, and so on), the site says why and what to do:

- Paddle.js reports `checkout.payment.failed`; while Paddle's checkout still shows its own error, the site asks why (`GET /companies/{id}/billing/payment-failure?transaction_id=…`, owners and admins). Billing reads the transaction from Paddle and answers only for the caller's own checkout into that company (its custom data names both; 404 otherwise, and a malformed id is refused before Paddle is asked).
- Billing names the latest payment attempt's `error_code` by what the buyer can do (`src/billing/constants/payment_failures.py`): `card_declined`, `insufficient_funds`, `expired_card`, `invalid_details`, `authentication_failed` (the bank's 3-D Secure check), `card_not_supported`, `payment_method_failed` (a wallet or PayPal without a clearer code), `try_later` (the bank or Paddle unreachable) or `other` (anything else, and Paddle slow or down: up to four reads 1.5 seconds apart, 4 seconds each, since Paddle can record the code a few seconds after the failure).
- Then Paddle's checkout closes and a dialog says "Payment didn't go through" with that reason's advice (another card or payment method, check the card details, confirm in the banking app, try later, ask the bank), **Close** and **Try again**, which opens the same checkout again. A failure the buyer has already retried past in Paddle's checkout shows nothing.
- The same holds for the checkout that turns automatic top-up on.
- Making checkouts, looking up failed payments and opening invoices count together against `CHECKOUT_CALLS_PER_USER_HOUR` (60 a user an hour by default), as each calls Paddle's API.

Balances follow a payment as it lands:

- They are rechecked for a minute after a completed payment.
- They catch up when the tab is back in view (an automatic top-up, a payment in another tab).
- A balance that goes up counts up to its new value, on the top-up page and on a company's interviews page.

## Automatic top-up

On the top-up page, under each balance, "Set up automatic top-up" opens the choice of a top-up and a balance to refill under; once it's on, the line shows the setting ("Automatic top-up: $50 under 500 credits") with an edit icon to change or turn it off. The top-up dialog shows it as a card with **Set up** or **Change**.

- Each amount shows the candidates it buys, in the list and in the chosen amount, from billing's catalog.
- The dialog's buttons: **Turn off** (when it's on), **Close**, and **Save**, which needs a change once it's on (turning it on needs none).
- **The buyer's agreement.** Turning it on, or saving a change, needs the buyer's own tick on a box under the choices, never ticked beforehand and cleared whenever the amount or the level changes: it names the amount, plus any VAT or sales tax, the balance that starts a charge, and that it charges until turned off in the same place. Billing refuses a save without it ("Tick the box to agree to the automatic top-up's charges.", 422; `agreed` in `AutoTopUpIn`). The setting keeps when it was last agreed to (`auto_top_ups.agreed_at`, for as long as it runs), and the company's action log keeps who agreed and when, with the terms in the buyer's language ("$50 plus tax when the balance falls under 1,500 credits", the entry's label).
- **Emails.** Once the card is saved (the start, below), owners and admins are told in the bell and by email what each charge costs, plus tax, the level that starts one and how to turn it off; one notice per subscription (`auto_top_up_on`, keyed by it), written only by the call that attached the subscription, so Paddle's two events for one checkout, arriving together or again, confirm it once. Each charge is told the same way (`auto_top_up_charged`, keyed by Paddle's transaction): what the card paid with tax, the day, the credits it added and those available after it, saved with the credits, so a repeated web hook or the reconciliation's replay adds none. Paddle emails its own receipt; ours carries how to turn it off. Both open the company's billing page.
- **Turning it off** is the dialog's **Turn off**, in the same place it was turned on, effective at once (below). Cancelling through Paddle's own emails or portal, which Paddle schedules for the end of the subscription's month, ends it at once too: billing's `subscription.updated` handler cancels a subscription with a scheduled cancel in Paddle and turns it off; if Paddle can't cancel it, the handler fails and Paddle sends the event again.

- The card is saved through Paddle once, with a $0 subscription whose checkout billing makes in the company's currency.
- Each charge's item is named in the interface language of whoever turned it on (kept with the setting, `auto_top_ups.language`; it changes only with the person whose card pays), in English for one set up before the language was kept.
- Every charge is in the company's currency, at that currency's price for the fixed top-up: if the company's currency changed since the subscription started, billing first switches the subscription to it (Paddle's `currency_code`, nothing billed for the switch), as Paddle charges a subscription in its own currency and would otherwise convert. The amounts it shows are in the company's currency too.
- Running, it charges the card of whoever set it up: only they change what it buys or when. Any other owner or admin may turn it off, then turn it on with their own card (`NOT_YOUR_AUTO_TOP_UP`, a 403, otherwise).
- Turning it off (by a member, by removing or demoting the member whose card pays, or by deleting the company or that member's account) cancels its Paddle subscription first and only then forgets it; a subscription Paddle already ended counts as cancelled. If Paddle can't cancel it, it stays on and the action fails, to be tried again, so the card is never left saved with nothing pointing at it.
- A user's data export ("Download my data") lists the automatic top-ups they turned on, as their card pays for them, with what each buys, when they last agreed to its terms and when it last charged or was declined, beside what they bought for their companies.
- It is shown only when Paddle's API key and the $0 price are set (see [Setting up Paddle](#setting-up-paddle)).
- A card that declines an automatic top-up is tried again within the card networks' limits (Visa: at most 15 retries in 30 days, none after a "never retry" decline): after 1, 3 and then 7 days (`AUTO_TOP_UP_RETRY_WAITS`, `src/billing/constants/declines.py`), and each decline tells the company's owners and admins (the bell, and an email whatever their settings) that it will be tried again. A fourth decline in a row, or one that can't pass later (Paddle's error codes in `HARD_DECLINE_CODES`: stolen, lost or blocked, fraud, expired, refused for good, a bank check or details the holder must give), **pauses** it: no charge until the card is updated, and owners and admins are told (bell and email, opening the company's billing page). Paddle's answer to a declined charge (`subscription_payment_declined`) gives no reason, but it records the attempt as a cancelled `subscription_charge` transaction whose payment has the error code (checked in the sandbox): billing reads it, bounded at 2 s; when there's none, the decline counts as one that may pass. Saving the setting again doesn't retry a declined card sooner.
- Paused, the setting says so in red with **Update card**: Paddle's checkout for the subscription's new card (`POST /companies/{id}/auto-top-up/card`, counted against `CHECKOUT_CALLS_PER_USER_HOUR`; billing makes the transaction with Paddle's `GET /subscriptions/{id}/update-payment-method-transaction`). Only the person whose card pays may (`NOT_YOUR_AUTO_TOP_UP`, a 403); others turn it off and set it up with their own card. Paddle's `transaction.completed` for that checkout (origin `subscription_payment_method_change`) ends a pause from before it, starts the declines over and, under the threshold, charges the new card at once; a repeated or late web hook (or the daily reconciliation's replay) resumes nothing paused since.
- Paddle refusing billing itself (its API key wrong, expired or short of a permission, or its rate limit: `401`, `403`, `429`) isn't the card's fault: nobody is told, and it alerts as Paddle failing does ([runbooks](../runbooks.md#paddle-down)).
- **Its price.** Each automatic top-up keeps the price it was agreed at (`price`, `price_currency`): the price list's when it's set up or another top-up is chosen. A new price list doesn't change it at once: the daily `POST /internal/schedules/auto-top-up-prices` (Cloud Scheduler's `billing-auto-top-up-prices`; locally `scripts/local/crontab`) finds each running one whose price list now differs, sets the new price from midnight UTC 31 days later (`AUTO_TOP_UP_PRICE_NOTICE_DAYS`), and tells owners and admins through billing's outbox, once per new price (the bell, and an email with both prices, plus tax, and the day). Charges before that day cost the agreed price; the setting shows "From <day>: <new price>". Changing only the level keeps both prices. This is the terms' promise of at least 30 days' notice.
- **Its currency.** Choosing another currency for the company is the member's own choice and applies at once, without a notice: charges cost the price list's price in it, and the answer (`auto_top_up_price`) has the site say so in a toast ("Automatic top-up now charges €50.") and update the setting.
- A charge Paddle doesn't answer (a timeout or an error on its side) isn't counted as declined: if it went through, Paddle's webhook adds the credits; either way no other charge follows until a charge's credits have come, for at most a day (`AUTO_TOP_UP_UNCREDITED_WAIT`), so a late or failing webhook never charges the card again and again. Once they've come, the next charge waits at least 10 minutes (`AUTO_TOP_UP_COOLDOWN`).

## Referrals

- A company's referral link is in its referrals tab, above the companies that came through it and topped up, each with the credits it gave the company then (none past the yearly limit below), not today's reward.
- Both companies get 1,000 credits (2 candidates) once the new one first tops up, any amount.
- The link asks the visitor first (a toast with **Keep** and **No thanks**), as the cookie serves the referral and not the page they asked for; kept, its code goes in a cookie (`prepza_ref`, 30 days), which companies reads when the visitor creates a company, on the site or through the in-app assistant: confirming the assistant's action passes the cookie on (only a code that reads right). AI apps connected over MCP have no browser cookie, so a company they create records no referral.
- A referrer earns the reward for at most 25 referrals in any 365 days; past that, only the new company gets its 1,000 credits.
- If that top-up is refunded in full or charged back, both rewards are taken back, even after the referred company was deleted: its rewarded referral is kept (only ids and the top-up that paid it), so deleting it can't keep the referrer's reward.

A balance shows short from a thousand credits up ("3.5K", in the language's own way), and says the whole amount on hover ("Current balance: 3,549"), wherever it appears: the company's header, the billing and top-up pages and the assistant's answers.

## A company's billing tab

Owners and admins see a company's **billing** tab, before referrals; viewers don't, and its API answers them with 403.

- At the top: the available credits, the credits reserved for candidates who haven't finished, the automatic top-up setting, the company's currency (a pill with its code, such as USD, EUR or JPY, beside the top-up button, which owners and admins change at once) and the top-up button. On phones the currency and the button go together under the balance.
- Two pages of billing's own, listed under it in the company's side menu (on a phone, a bar under the tabs naming the open one, which opens a menu of both): **history** first and **reserved (N)** (`?tab=reserved`), so a long list of reserved candidates never pushes the history out of sight; only the open page's list is loaded.
- **Reserved**: an info card on what reserved credits are, then the candidates invited who haven't finished (invited, undelivered or in progress), each opening the candidate's page. Their count comes with the company's credits (`reserved_candidates`).
- **History**: every movement of the company's credits, newest first, loading more as you scroll. Each shows the credits it moved (+5,000, −500), what it was and when:
  - a top-up: what was paid (tax included), whether it was automatic, and its invoice, opened through a temporary Paddle link made on request;
  - a candidate: the candidate and their test, opening the candidate's page, or "A deleted candidate" when the invite is gone;
  - a refund, a chargeback, a chargeback reversed: the money it moved;
  - a referral reward, a referral reward taken back, the welcome gift.

Billing's history entries keep the money a top-up, refund or chargeback moved (`total`, in minor units, and `currency`; stored as an integer, `total_minor`, which every purchase has; the API gives `total` as a string) and whether a top-up was automatic, and a superadmin's adjustment (reason `adjustment`, see [Admin zone](admin-support.md)) its `note`; entries from before that was kept have the money of their top-up only. Companies' `GET /companies/{id}/billing/history` and `/billing/reserved` serve the tab: the history comes from billing's internal `GET /internal/companies/{id}/history`, and its candidates are matched to their invites by the key of their credits in one query. The invoice (`/billing/invoice?transaction_id=`) is billing's own route, which checks the transaction topped up that company.

## Refunds and chargebacks

Refunds and chargebacks in Paddle take back the credits they bought, in proportion to the money returned (a top-up of any number of candidates too: $100 back of $200 takes back half its credits).

## Missed web hooks

Paddle retries a web hook for about two days (three tries in the sandbox). So that a payment's credits or a refund's take-back is never lost when it gives up (a wrong web hook secret, a long outage), billing reconciles with Paddle daily (`POST /internal/schedules/reconcile`, Cloud Scheduler's `billing-reconcile`; locally `scripts/local/crontab`):

- It reads Paddle's completed transactions updated in the last week and its approved adjustments created in it (`RECONCILE_WINDOW`, `src/billing/constants/reconciliation.py`), up to 10 pages of 200 each, the rest left to the next run.
- Each one billing hasn't counted yet goes through the same handler as its web hook, so it counts once whichever comes first, and two runs at once change nothing twice. Payments go first, so a refund whose payment's web hook was lost counts too.
- What it had to apply is logged as a warning ("Reconciliation credited transaction …", "Reconciliation counted adjustment …"): a sign that web hooks are failing. One item failing is logged and the rest go on. Each of these lines, and each paid transaction billing refuses to credit ("refund it"), fires the **prepza payment not credited** alert ([runbook](../runbooks.md#a-payment-not-credited)).
- It needs the API key's permission to read transactions and adjustments (see [Setting up Paddle](#setting-up-paddle)).

## Who reaches a company's payments

A company's prices, currency, checkouts, invoices, failed payments and automatic top-up are billing's own routes (`src/billing/api/v1/company_payments.py`, `company_auto_top_ups.py`), kept at the addresses the site always used: `/api/companies/companies/{id}/billing/catalog`, `/currency`, `/checkout`, `/invoice`, `/payment-failure`, and `/api/companies/companies/{id}/auto-top-up` (and `/card`). The gateway and the load balancer send exactly these paths to billing (`gateway/nginx.conf`, `company_billing_paths` in `infra/terraform/locals.tf`); the history and the reserved list stay with companies, which knows the candidates. Billing asks companies who the user is in the company (`prepza_common.auth.company_access`, with the assistant's `X-Assistant` header passed on): any member sees the currency and the automatic top-up, only owners and admins pay, change them or read invoices and failures; others get 404, a viewer changing 403, and a suspended company or an AI app the company doesn't allow 403 with companies' reason. A changed currency and an automatic top-up set up, changed or turned off are logged in the company's action log through billing's outbox, in the same save as the change.

## Deleting a company

Deleting a company deletes its credits: billing's internal `DELETE /internal/companies/{id}` removes the wallet, its holds and its history (holds and history a batch at a time, each batch its own transaction, so a deletion cut off midway goes on when it's run again), and turns off automatic top-up. Purchases stay on record, and nothing is refunded; a refund Paddle makes later takes back only the referral reward the top-up paid. Before it's deleted, the owner sees how many credits are lost: the remove dialog, and the assistant's delete card, read the company's balance (`GET /companies/{id}/credits`, whose `candidates` is how many candidates the available credits pay for, worked out by billing) and add "Its 900 credits (about 3 candidates) will be lost and aren't refunded." when there are any.

## AI usage and limit hits

Billing keeps what AI costs and who hits which limit, for the admin zone's AI costs page and Limits (see [Admin zone](admin-zone.md#ai-costs)):

- **`ai_usage`:** one row per AI call (or per model of one generation run): its action, service, model, input, cached input and output tokens (or audio seconds), cost in USD, company and user (either may be empty), what it was for (`subject_id`: a generation, a conversation, a question), outcome (`ok`, `cut`, `failed`) and when it happened.
- **`limit_hits`:** one row per refusal, ours or a provider's: the limit, its kind (`ours` or `provider:<name>`), its scope (user, company, ip or everyone), the company and user, and what was refused. An IP is never stored.
- **`limit_settings`** and **`limit_changes`:** the limits a superadmin changed, and every change with who made it (see [Admin zone](admin-zone.md#limits)).

The services record each AI call (`prepza_common.ai.ai_usage.record`) and each refusal (`prepza_common.limits.limits.record_hit`) as a log line and an event on the `events` topic, `ai.used` or `limit.hit`, which Pub/Sub pushes to billing's `POST /internal/events`. A record's publish is tried 3 times, then given up with a log line; the log line still carries the cost, so the `prepza_ai_spend` metric and its alert stay whole.

- **Idempotent:** the event id is unique in both tables, so a redelivered event changes nothing.
- **Order:** each row keeps the call's own time, so the order events arrive in doesn't matter.
- **Failures:** an error answers 5xx and Pub/Sub delivers the event again, then dead-letters it as any other; an event no retry can store (missing or malformed data) is logged as an error and acknowledged instead.

Who a call was for is decided as it's stored: a call for a company is **paid** if the company had a purchase by the call's time, **unpaid** otherwise; a call without a company is **prepza**'s when its action is prepza's own work (`PREPZA_ACTIONS`: templates, quality checks, batches, embeddings, news and campaign translations) and **no company** otherwise (the help chat's visitors, candidates, people without a company). Billing then adds an unpaid or no-company call's cost to the day's unpaid AI spend in Redis (`spend:ai:unpaid:<date>`), which the services check against the `AI_SPEND_UNPAID_DAY` cap before their AI calls for those users (`prepza_common.ai.ai_cap`); it logs once when the day passes 80% of the cap and once when it reaches it.

- **Kept:** `ai_usage` and `limit_hits` 13 months, for year-on-year comparison, and `limit_changes` 24 months, by the daily `/internal/schedules/retention`.
- **Deleted accounts and companies:** deleting an account (accounts' `user.deleted` event) or a company (`DELETE /internal/companies/{id}`) empties its id in both tables, a batch at a time; the costs and hits stay.

```
GET    /superadmin/ai-costs?period=         # the AI costs page
GET    /superadmin/limit-hits?period=
GET    /superadmin/ai-spend?company_id=|user_id=   # 30 days, for a support page
GET    /superadmin/limits
PUT    /superadmin/limits/{name}
DELETE /superadmin/limits/{name}
GET    /superadmin/limits/changes
POST   /internal/events                     # Pub/Sub
POST   /internal/schedules/limits           # every 5 minutes
POST   /internal/schedules/retention        # daily
POST   /internal/schedules/reconcile        # daily: Paddle's payments and refunds of the last week
```

To fill in the top lists' names, billing asks companies for companies' names and accounts for accounts' emails. `MONTHLY_BUDGET` (USD a month, set in the admin zone's Controls, see [Admin zone](admin-zone.md#limits)) is what the page compares the month's spend with; at 0 it shows the month's spend alone.

## Currencies

Prices are in the local currency in Canada, Australia, Israel, Poland, Switzerland, Japan, South Korea, Taiwan, Hong Kong, Thailand, Singapore and India; in euros in the rest of the EU and in Iceland, Liechtenstein and Norway; in pounds in the UK; and in US dollars elsewhere (`src/billing/constants/currencies.py`; migration 0018 added all but USD, EUR and GBP, and Poland and Switzerland moved from euros to their own, saved currencies staying as they were). Each is a payment currency Paddle supports. Amounts are in each currency's smallest unit, as Paddle counts them: cents, but whole yen and won (Paddle's `decimal_places` 0); the site and the FAQ format them by the currency's own decimals. Tests keep both in line with Paddle's own figures (its `GET /currencies`): every currency billing sells in has Paddle's decimal places on the site (`frontend/tests/lib/format.test.ts`), and every top-up is in whole minor units above Paddle's minimum payment in that currency (`tests/unit/test_paddle_amounts.py`). Billing decides which, never the site:

- **The country:** Google's load balancer adds `X-Client-Country: {client_region}` to every request, replacing any the browser sent; the site's server-side calls pass it on as `?country=`. Locally the gateway takes it from a `test_country` cookie ("DE", "GB"). The header is optional everywhere: calls from AI apps, the public API, other services and tests have none.
- **Saved currencies** (`currency_choices`, migration 0017): a person's is saved from their country at sign-up, a company's from its creator's country when it's created; one without (older accounts and companies) gets it the first time billing sees them with a known country, US dollars until then. Travelling later changes nothing. A person changes theirs in Settings (beside the language); owners and admins change a company's beside its Top up button, on its billing tab and the top-up page (`PUT /companies/{id}/billing/currency`, in the action log as "Changed the currency").
- **Which applies:** a company's billing (its catalog `GET /companies/{id}/billing/catalog`, the top-up dialog, automatic top-up, checkouts) uses the company's; elsewhere a signed-in person sees their own (`GET /billing/catalog` with their token), and a signed-out visitor their country's, not saved.
- The FAQ and the help chat name prices in the visitor's country's currency; the admin zone's stats show what was paid in each currency apart.
- Deleting an account or a company deletes its saved currency; a user's data export includes theirs.

## How it's built

Routes call services (`src/billing/services/` in billing), which open each transaction and pass it to the repositories; Paddle, companies and Redis are called outside it. A company's welcome (its wallet and welcome credits, the referral it came through and its currency) is one save, and so is the end of a deletion: a company's wallet, referral and currency once its holds and history are gone, and an account's automatic top-ups, its id on its purchases and its currency once Paddle has cancelled its card's subscriptions. A failure saves none of it, so the retry finds it all still to do. A hold, a charge, a top-up, a refund and a referral reward are each one save, guarded by row locks and unique keys against two at once; a declined automatic charge is saved in steps, as Paddle is read between them.

## Setting up Paddle

`billing` sells through [Paddle](https://www.paddle.com), which is the merchant of record: it handles VAT and sales tax. Businesses and consumers can both buy; prices don't include VAT or sales tax: where it applies, Paddle adds it at checkout, on top of the listed price, and the checkout shows the total before the buyer pays. A company pays in its own currency (see [Currencies](#currencies)); a card in another currency may be converted by its bank or card issuer.

Every price is made by billing in the transaction itself, in one currency, with the transaction's `currency_code`: Paddle then charges that currency from any country (a price with country overrides is instead charged in the buyer's country's currency, converting when the transaction's differs, so overrides aren't used).

1. In Paddle (start with the sandbox), create one product (say, "Candidates"), with no price: billing prices each top-up under it, tax **Exclusive** (`tax_mode: external`), so VAT or sales tax is added on top at checkout, as the pricing page and the terms say. Also create a client-side token. Under Settings → Currencies, keep automatic currency conversion off.
2. Under Developer tools → Notifications, add a webhook destination at `https://<your domain>/api/billing/webhooks/paddle` for these events, then copy its secret key:

   | Event | Why |
   |---|---|
   | `transaction.completed` | A payment |
   | `adjustment.created`, `adjustment.updated` | Refunds and chargebacks, which take credits back |
   | `subscription.created`, `subscription.canceled` | Start and end automatic top-ups |
   | `subscription.updated` | A cancel scheduled in Paddle (its emails or portal) ends automatic top-up at once |

   A card saved for an automatic top-up (**Update card**) arrives as `transaction.completed` too.

3. Create a server-side API key with permission to read and write transactions (billing makes every top-up's checkout, reads invoices for the billing tab and lists payments for the daily reconciliation), to read adjustments (the reconciliation's refunds and chargebacks) and to read and update subscriptions (automatic top-up's charges, currency and card updates). Paddle's keys expire (90 days by default, a year at most): note the date and replace the key before it (see [runbooks](../runbooks.md#paddle-down)). For automatic top-up, also create a $0 monthly price (its checkout saves the card); without it and the key, automatic top-up isn't offered.
4. Set these in `.env`, then restart billing:

   | Setting | Value |
   |---|---|
   | `PADDLE_ENVIRONMENT` | The Paddle environment |
   | `PADDLE_CLIENT_TOKEN` | The client-side token |
   | `PADDLE_WEBHOOK_SECRET` | The webhook's secret key |
   | `PADDLE_PRODUCT_CANDIDATES` | The product every top-up is sold under |
   | `PADDLE_PRICE_AUTO_TOP_UP` | The $0 monthly price |
   | `PADDLE_API_KEY` | The server-side API key |

In Google Cloud, the webhook secret and the API key go into the `paddle-webhook-secret` and `paddle-api-key` secrets (see [infra/README.md](../../infra/README.md)).

- The API key and the client-side token must belong to `PADDLE_ENVIRONMENT`'s account (`pdl_sdbx_…` and `test_…` for the sandbox, `pdl_live_…` and `live_…` for production), or billing doesn't start, naming the setting (never its value): sandbox and live never mix.
- Every call to Paddle's API asks for version 1 (the `Paddle-Version` header, `PADDLE_API_VERSION`), so a newer default in Paddle's dashboard changes nothing until billing moves to it.
- Until `PADDLE_PRODUCT_CANDIDATES` is set, the top-up dialog's button is disabled and automatic top-up isn't offered.
- Until both automatic top-up values are set, its line on the top-up page is hidden.
- Locally, Paddle reaches the webhook only through a tunnel, for example `cloudflared tunnel --url http://localhost:8090`.
- In the sandbox, pay with Paddle's test cards (any name, a future expiry): `4242 4242 4242 4242` pays, `4000 0000 0000 0002` is declined, and `4000 0038 0000 0446` asks for 3-D Secure, which can be failed.
