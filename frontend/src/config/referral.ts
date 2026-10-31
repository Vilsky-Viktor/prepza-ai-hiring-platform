// Matches REFERRAL_COOKIE in testee_common.config.constants: the backend reads it when a new person
// signs up or makes a company.
export const REFERRAL_COOKIE = "testee_ref"
export const REFERRAL_PARAM = "ref"
export const REFERRAL_DAYS = 30
// The shape of a code billing makes; anything else isn't kept.
export const REFERRAL_CODE = /^[A-Za-z0-9_-]{4,16}$/
