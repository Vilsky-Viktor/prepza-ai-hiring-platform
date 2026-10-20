import type { components } from "@/types/api/billing"
import type { components as companies } from "@/types/api/companies"

type Schemas = components["schemas"]

export type Catalog = Schemas["CatalogOut"]
export type Product = Schemas["TopUpOut"]
export type Referral = Schemas["ReferralOut"]
export type AutoTopUp = Schemas["AutoTopUpOut"]
// The Paddle transaction a top-up's checkout opens, made by the backend.
export type CheckoutData = companies["schemas"]["TopUpCheckoutOut"]
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
export type PaymentFailureData = companies["schemas"]["PaymentFailureOut"]
