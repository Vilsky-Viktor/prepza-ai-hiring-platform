// The visitor's country (a two-letter code), which the load balancer sets on every page request
// (the local gateway from a `test_country` cookie); billing's prices follow it.
export const COUNTRY_HEADER = "x-client-country"

// Sent on the window when the company's billing changed (the page reads it again after a
// payment, or its currency was changed), so what reads its own data (the automatic top-up)
// reads it again too.
export const BILLING_REFRESHED = "testee:billing-refreshed"
