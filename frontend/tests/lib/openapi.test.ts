import { describe, expect, it } from "vitest"

import {
  errorsOf,
  fieldsOf,
  operationsOf,
  richText,
  descriptionTabs,
  schemasOf,
  successSchema,
  typeOf,
} from "@/lib/openapi"
import type { OpenApi } from "@/types/openapi"

const SPEC: OpenApi = {
  info: { title: "testee API", version: "1" },
  paths: {
    "/interviews": {
      get: {
        summary: "List interviews",
        responses: {
          "200": {
            description: "OK",
            content: {
              "application/json": {
                schema: {
                  type: "array",
                  items: { $ref: "#/components/schemas/Interview" },
                },
              },
            },
          },
          "401": { description: "No key" },
          "422": { description: "Validation Error" },
        },
      },
    },
  },
  components: {
    schemas: {
      Interview: {
        properties: {
          id: { type: "string", format: "uuid" },
          title: {
            anyOf: [{ type: "string" }, { type: "null" }],
            description: "Null while generating",
          },
        },
        required: ["id"],
      },
      HTTPValidationError: {},
    },
  },
}

describe("the API docs read the OpenAPI description", () => {
  it("names types in a few words", () => {
    expect(typeOf({ type: "string", format: "uuid" })).toBe("string (uuid)")
    expect(typeOf({ anyOf: [{ type: "integer" }, { type: "null" }] })).toBe(
      "integer | null"
    )
    expect(
      typeOf({
        type: "array",
        items: { $ref: "#/components/schemas/Candidate" },
      })
    ).toBe("array of Candidate")
  })

  it("lists an object's fields, a $ref followed, with what's required", () => {
    expect(fieldsOf(SPEC, { $ref: "#/components/schemas/Interview" })).toEqual([
      { name: "id", type: "string (uuid)", required: true, description: "" },
      {
        name: "title",
        type: "string | null",
        required: false,
        description: "Null while generating",
      },
    ])
  })

  it("lists routes, what they return and their errors without FastAPI's 422", () => {
    const [route] = operationsOf(SPEC.paths)

    expect([route.method, route.path]).toEqual(["GET", "/interviews"])
    expect(typeOf(successSchema(route.operation)!)).toBe("array of Interview")
    expect(errorsOf(route.operation)).toEqual([
      { code: "401", description: "No key" },
    ])
    expect(schemasOf(SPEC).map(([name]) => name)).toEqual(["Interview"])
  })

  it("splits a description into titled sections, steps and inline code", () => {
    const sections = richText(
      "Intro with `code`.\n\n## Keys\n\n1. Sign in.\n2. Open **Hiring**, then\n   a tab.\n\nAfter."
    )

    expect(sections.map((section) => section.title)).toEqual([null, "Keys"])
    expect(sections[0].blocks[0].pieces).toEqual([
      { text: "Intro with ", kind: "text" },
      { text: "code", kind: "code" },
      { text: ".", kind: "text" },
    ])
    const [steps, after] = sections[1].blocks

    expect(
      steps.steps?.map((step) => step.map((piece) => piece.text).join(""))
    ).toEqual(["Sign in.", "Open Hiring, then a tab."])
    expect(after.steps).toBeNull()
  })

  it("splits a description into its tabs at its top titles", () => {
    expect(
      descriptionTabs(
        "# API\n\nKeys.\n\n## Errors\n\nNone.\n\n# Web hooks\n\nSigned."
      )
    ).toEqual({ api: "Keys.\n\n## Errors\n\nNone.", webhooks: "Signed." })
  })

  it("reads a link in a paragraph, also across lines", () => {
    const [section] = richText("Get a [web\nhook](/api-docs?tab=webhooks) now.")

    expect(section.blocks[0].pieces).toEqual([
      { text: "Get a ", kind: "text" },
      { text: "web hook", kind: "link", href: "/api-docs?tab=webhooks" },
      { text: " now.", kind: "text" },
    ])
  })

  it("keeps a code block as written", () => {
    const [section] = richText('```html\n<div id="a"></div>\n  <b>x</b>\n```')

    expect(section.blocks[0].code).toEqual([
      { code: '<div id="a"></div>\n  <b>x</b>', language: "html" },
    ])
  })

  it("keeps a code block with blank lines whole", () => {
    const [section] = richText(
      "Before.\n\n```python\na = 1\n\nb = 2\n```\n\nAfter."
    )

    expect(section.blocks.map((block) => block.code)).toEqual([
      undefined,
      [{ code: "a = 1\n\nb = 2", language: "python" }],
      undefined,
    ])
  })

  it("makes code blocks that follow each other one example in several languages", () => {
    const [section] = richText(
      "```bash\ncurl x\n```\n\n```python\nget(x)\n```\n\nThen.\n\n```\nplain\n```"
    )

    expect(section.blocks.map((block) => block.code)).toEqual([
      [
        { code: "curl x", language: "bash" },
        { code: "get(x)", language: "python" },
      ],
      undefined,
      [{ code: "plain", language: undefined }],
    ])
  })
})
