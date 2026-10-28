import { expect, it } from "vitest"

import { COMPANY_INTERVIEW_PAGE } from "@/config/layout"

it("knows a company's interview pages, which show no header or footer", () => {
  for (const path of [
    "/invite/tok",
    "/de/apply/tok",
    "/embedded/tok",
    "/companies/c1/interviews/i1/try",
  ]) {
    expect(COMPANY_INTERVIEW_PAGE.test(path), path).toBe(true)
  }

  for (const path of [
    "/companies/c1/interviews/i1",
    "/companies/c1/interviews/i1/try/more",
    "/practice/rounds/r1",
  ]) {
    expect(COMPANY_INTERVIEW_PAGE.test(path), path).toBe(false)
  }
})
