import { describe, expect, it } from "vitest"

import { campaignForm } from "@/lib/campaigns"
import type { Campaign } from "@/types/campaigns"

const campaign = {
  id: "c-1",
  kind: "promotions",
  link: "https://example.com/offer",
  groups: ["members", "learners"],
  editors_only: true,
  companies: [{ id: "co-1", name: "Acme" }],
  texts: {
    en: { subject: "Spring offer", text: "<p>Half off</p>", button: "See it" },
    de: {
      subject: "Frühlingsangebot",
      text: "<p>Halber Preis</p>",
      button: null,
    },
  },
} as unknown as Campaign

describe("campaignForm", () => {
  it("starts a new campaign as an empty update to everyone", () => {
    expect(campaignForm(undefined, "en")).toEqual({
      kind: "updates",
      audience: { groups: [], editorsOnly: false, companies: [] },
      subject: "",
      text: "",
      button: "",
      link: "",
    })
  })

  it("fills a campaign's audience and its texts in the language asked for", () => {
    expect(campaignForm(campaign, "de")).toEqual({
      kind: "promotions",
      audience: {
        groups: ["members", "learners"],
        editorsOnly: true,
        companies: [{ id: "co-1", name: "Acme" }],
      },
      subject: "Frühlingsangebot",
      text: "<p>Halber Preis</p>",
      button: "",
      link: "https://example.com/offer",
    })
  })

  it("falls back to the English texts in a language without its own", () => {
    expect(campaignForm(campaign, "fr").subject).toBe("Spring offer")
  })
})
