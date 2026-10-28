---
paths:
  - "services/billing/**/*auto_top_up*"
  - "services/companies/src/companies/**/auto_top_ups.py"
  - "frontend/src/components/common/auto-top-up*"
  - "e2e_tests/signed-in/**/*auto-top-up*"
---

# Automatic top-up (merchant-initiated charges)

The rest of payments (prices, the ledger, web hooks, refunds, tests) is in
`.claude/rules/payments.md`; CLAUDE.md wins on conflict.

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

Research (local notes, git-ignored): `internal_docs/best-practices/payments.md`.
