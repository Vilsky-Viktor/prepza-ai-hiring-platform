import type { components } from "@/types/api/billing"

type Schemas = components["schemas"]

export type Catalog = Schemas["CatalogOut"]
export type Product = Schemas["TopUpOut"]
export type Referral = Schemas["ReferralOut"]
export type AutoTopUp = Schemas["AutoTopUpOut"]
// The currency someone sees prices in, or a company pays in (and its running automatic
// top-up's), with the ones to choose from.
export type CurrencyChoice = Schemas["CurrencyOut"]
export type CompanyCurrency = Schemas["CompanyCurrencyOut"]
// The Paddle transaction a top-up's checkout opens, made by the backend.
export type CheckoutData = Schemas["TopUpCheckoutOut"]
// A company's credits: available, set aside for candidates who haven't finished (and how many
// candidates those are), running low, and how many candidates they pay for.
export type CompanyCredits = {
  available: number
  reserved: number
  reserved_candidates: number
  low: boolean
  candidates: number
}
// Why a checkout's payment failed, as billing decides it: one of a fixed set of keys, each with
// its advice in the messages (billing.paymentFailed).
export type PaymentFailureData = Schemas["PaymentFailureOut"]
