---
paths:
  - "services/billing/**"
  - "services/companies/app/routers/billing.py"
  - "services/companies/app/routers/auto_top_ups.py"
  - "services/companies/app/integrations/billing_prices.py"
  - "services/companies/app/schemas/billing.py"
  - "services/companies/app/schemas/auto_top_ups.py"
  - "frontend/lib/paddle.ts"
  - "frontend/lib/top-up.ts"
  - "frontend/constants/paddle.ts"
  - "frontend/components/billing/**"
  - "frontend/app/top-up/**"
  - "e2e_tests/signed-in/helpers/paddle.ts"
  - "docs/features/billing.md"
---

# Payments (Paddle Billing, prepaid credits)

prepza sells prepaid credits through Paddle Billing, the merchant of record (MoR): Paddle is the
seller on the invoice, collects and remits VAT and sales tax, screens fraud, runs disputes and
holds the card data. billing makes every checkout, Paddle.js only shows it, web hooks grant.
CLAUDE.md wins on conflict; rule 4 decides "not adopted". Overlaps are pointed at, not repeated.

## Choosing and running the gateway

- One provider, Paddle, behind one module (`services/billing/app/integrations/paddle.py`). No
  gateway abstraction or second processor (rule 4): saved cards can't move between providers, an
  MoR swap means new terms, tax and payouts, and a second gateway would double the web hooks,
  ledger keys and tests. Revisit only with a reason the user names (fees at volume, a market
  Paddle can't sell in, an account hold); `internal_docs/best-practices/payments.md` compares
  Stripe Managed Payments.
- Adding a payment method, country or currency is a Paddle setting plus billing's lists
  (`constants/currencies.py`, `CANDIDATE_PRICES`), checked against Paddle's supported currencies,
  their decimals and minimum charges; fees, payouts and the account's verification are the user's.
- Sandbox and live are separate Paddle accounts: their API keys (`pdl_sdbx_` / `pdl_live_`) and
  client tokens (`test_` / `live_`) must match `PADDLE_ENVIRONMENT`, or billing refuses to start
  (`config/settings.py`). Development and every test use the sandbox; never a real card or a live
  key on a laptop, in CI or in a test.
- The API key has only the permissions billing uses (listed in `docs/features/billing.md`, Setting
  up Paddle) and an expiry; keys and the web hook secret live in Secret Manager. Every call pins
  `Paddle-Version` (`PADDLE_API_VERSION`); a new version is adopted deliberately.

## Prices and money

- The server sets every price: billing makes the transaction with its items priced inline (under
  `PADDLE_PRODUCT_CANDIDATES`), its currency, quantity locked to 1 and whose wallet in
  `custom_data`. The browser sends only a count or a choice; never an amount, currency, owner or
  product. No discount codes in checkout unless billing issues them.
- Money is an integer in the currency's minor units as Paddle counts them (JPY and KRW have no
  decimals; the others in our list have two), carried as Paddle's string or a Python `int`;
  never a float, never divided or converted in code. Each amount travels with its currency, and
  each transaction keeps the currency it was paid in. Prices are round amounts per currency, not
  conversions; each smallest top-up stays above Paddle's minimum charge (a test checks).
- Proportions (a partial refund's credits) are integer arithmetic, rounded in the customer's
  favour (floor of what is taken back). The site formats money only for display (`lib/format.ts`).
- Prices are shown without tax and Paddle adds VAT or sales tax at checkout (`tax_mode:
  external`); billing never computes or adds tax. Changing that is the user's decision.

## Granting only what was paid

- Credits come only from a verified `transaction.completed` (fully paid and processed); never from
  Paddle.js's `checkout.completed`, a redirect or anything the browser says. The page says the
  payment is on its way and refreshes until the balance shows it.
- Grant only for a transaction billing made (`origin: api`, or a charge on a subscription billing
  knows), into a wallet that still exists, for lines of billing's product with a count billing
  sells; anything else is logged as an error to refund, never credited.
- The ledger is append-only: every movement is one `entries` row with a unique key derived from
  Paddle's ids (`{transaction}:{product}`, `adjustment:{transaction}:{adjustment}`); a correction
  or reversal is a new entry, never an update or delete. The balance moves in the same database
  transaction as its entry.

## Web hooks

- Verify `Paddle-Signature` (HMAC-SHA256 of `ts:raw body`, constant-time, any `h1` during secret
  rotation) before parsing; refuse a missing secret; log refusals for their alert. Tolerance 300
  s, not Paddle's 5 s: billing scales to zero, and a cold start would refuse fresh deliveries.
- Idempotent on Paddle's object ids (transaction, adjustment, subscription) through unique keys
  and `INSERT … ON CONFLICT`, which also covers duplicate events; no table of event ids.
- Independent of order: a handler reads the current state from Paddle or the database where order
  matters (`subscription.created` after `.canceled`); reconciliation repairs what came too early
  (a refund before its payment).
- Answer within Paddle's 5 s: database work and outbox writes only; slow follow-ups go through the
  outbox or are bounded. A handler that fails answers 5xx so Paddle retries (about two days live,
  three tries in the sandbox); unknown types get 200. A new type is subscribed in Paddle and
  listed in `docs/features/billing.md`.
- Reconciliation, daily (`/internal/schedules/reconcile`): Paddle's completed transactions and
  approved adjustments of the last `RECONCILE_WINDOW` go through the same idempotent handlers;
  what it had to apply is logged as a warning (a missed web hook). Bounded pages, the rest left
  to the next run; two runs at once change nothing twice.

## Refunds, chargebacks and failed payments

- Refunds and chargebacks are made in Paddle (support or Paddle's dispute process), never by
  editing balances. An approved `refund` or a `chargeback` takes back the credits in proportion
  to the money returned (several partials add up to a full one); `chargeback_reverse` returns
  them; `chargeback_warning`, pending and rejected adjustments change nothing. The balance may go
  negative; a fully refunded top-up also takes back its referral reward.
- A payment failing in checkout: billing reads the attempt's `error_code` from Paddle for the
  buyer's own transaction only and maps it to advice (`constants/payment_failures.py`).

## Automatic top-up (merchant-initiated charges)

- The card is saved once through a Paddle checkout (the buyer's consent and 3-D Secure happen
  there); later charges are `POST /subscriptions/{id}/charge`, which Paddle sends as
  merchant-initiated. Before turning it on the buyer sees what it buys, when it charges, that a
  receipt follows each charge and that it can be turned off at any time.
- One charge at a time per wallet (`claim_charge`, atomic): a cooldown between charges, none while
  the last charge's credits haven't come. Never retry in a loop; Paddle's limit is 20 charges an
  hour per subscription.
- A declined card is retried within card-network limits (Visa: at most 15 in 30 days):
  `AUTO_TOP_UP_RETRY_WAITS` (1, 3, 7 days), then paused; a decline in `HARD_DECLINE_CODES`
  pauses at once. Paused, nothing is charged until Paddle saves a new card (its card-update
  checkout, by the card's owner only); owners and admins are told by bell and email.
- What a charge costs is agreed (`price`): a new price list applies only from a day announced at
  least 30 days ahead by email and bell (the terms' promise); a currency or top-up the company
  chooses applies at once.
- Only the person whose card pays can change what it buys; anyone allowed can turn it off, which
  cancels the subscription first; so does deleting the account or company. Every charge
  notifies the owner (the bell; Paddle emails the receipt).

## Checkout in the browser

- Paddle.js comes from Paddle's CDN through `@paddle/paddle-js`, initialised once; the CSP allows
  Paddle's origins (`frontend/constants/security.ts`). Card details are typed only into Paddle's
  frames, so prepza never sees them (PCI DSS SAQ A territory; Paddle is the merchant).
- Open checkout by `transactionId` only, with the site's theme and language; a failed payment
  shows billing's advice and can be retried on the same transaction.

## Abuse, observability, data

- Creating checkouts (card updates too), reading failures and invoice links count against
  `CHECKOUT_CALLS_PER_USER_HOUR` after the role check (`.claude/rules/security.md`, Rate
  limiting); Paddle screens card testing.
- Paddle failing (no answer, 5xx) and Paddle refusing billing's key (401, 403: wrong, expired or
  missing permission) log "Paddle unavailable" for the alert; a declined card doesn't. Refused
  signatures alert, and so do "refund it" errors and what reconciliation had to apply or failed
  on (`monitoring_billing.tf`). Runbooks: `docs/runbooks.md` (Paddle down, A payment not
  credited).
- Keep only Paddle's ids, amounts, currency, status and the buyer's prepza id; never card data,
  addresses or tax ids (Paddle holds them as controller). Send Paddle the buyer's email only;
  logs carry transaction and adjustment ids, never emails or tokens.

## Tests

- Unit: signatures (valid, rotated, tampered, expired, no secret), every event type, duplicates
  and out-of-order events, refund shares; Paddle faked with `httpx.MockTransport`.
- Integration: grants, adjustments, auto top-up races and reconciliation against Postgres, each
  test with its own wallet.
- Browser: the sandbox checkout with Paddle's test cards (4242… pays, 4000 0000 0000 0002
  declines, 4000 0038 0000 0446 asks for 3-D Secure); the web hook simulator for event shapes.

## Not adopted

- A gateway abstraction or second provider; Paddle's webhook IP allow-list (signatures suffice,
  and the lists change); storing raw events or event ids; a double-entry ledger with contra
  accounts (one wallet per company, append-only entries are enough at this size).

Research (local notes, git-ignored): `internal_docs/best-practices/payments.md`.
