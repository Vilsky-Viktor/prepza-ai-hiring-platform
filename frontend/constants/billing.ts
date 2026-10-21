// The visitor's country (a two-letter code), which the load balancer sets on every page request
// (the local gateway from a `test_country` cookie); billing's prices follow it.
export const COUNTRY_HEADER = "x-client-country"

// Sent on the window each time the page reads its billing again after a payment, so what reads
// its own data (the automatic top-up) reads it again too.
export const BILLING_REFRESHED = "prepza:billing-refreshed"
