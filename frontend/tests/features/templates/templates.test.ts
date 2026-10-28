import { describe, expect, it } from "vitest"

import {
  templateChoice,
  templateQuery,
} from "@/features/templates/utils/templates"
import type { TemplateFilters } from "@/types/superadmin"

const filters = {
  levels: ["junior", "senior"],
  languages: ["en", "de", "fr"],
} as unknown as TemplateFilters

describe("templateChoice", () => {
  it("keeps only the level and languages the API offers", () => {
    const choice = templateChoice(
      { q: "  python  ", level: "expert" },
      ["de", "xx"],
      ["de", "xx"],
      filters
    )

    expect(choice).toEqual({ q: "python", level: null, languages: ["de"] })
  })

  it("means every language when all are asked for", () => {
    const choice = templateChoice({ level: "senior" }, ["all"], [], filters)

    expect(choice).toEqual({ q: "", level: "senior", languages: [] })
  })
})

describe("templateQuery", () => {
  it("sends the search, the level and each language", () => {
    const query = templateQuery({
      q: "sql",
      level: "junior",
      languages: ["en", "fr"],
    })

    expect(query.toString()).toBe("q=sql&level=junior&language=en&language=fr")
  })

  it("leaves out what wasn't chosen", () => {
    expect(
      templateQuery({ q: "", level: null, languages: [] }).toString()
    ).toBe("")
  })
})
