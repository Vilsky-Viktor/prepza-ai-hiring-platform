import type { Field, OpenApi, Operation, Schema } from "@/types/openapi"

// FastAPI's own schemas for its 422 answers: the docs describe errors in words instead.
const HIDDEN_SCHEMAS = ["HTTPValidationError", "ValidationError"]

/** "#/components/schemas/Candidate" -> "Candidate". */
export function refName(ref: string) {
  return ref.split("/").pop() ?? ref
}

/** A schema's type in a few words: "string (uuid)", "array of Candidate", "integer | null". */
export function typeOf(schema: Schema): string {
  if (schema.$ref) {
    return refName(schema.$ref)
  }

  if (schema.anyOf) {
    return schema.anyOf.map(typeOf).join(" | ")
  }

  if (schema.type === "array" && schema.items) {
    return `array of ${typeOf(schema.items)}`
  }

  return schema.format
    ? `${schema.type} (${schema.format})`
    : (schema.type ?? "any")
}

/** The fields of an object schema (or the one a $ref names), in the order the API lists them. */
export function fieldsOf(spec: OpenApi, schema: Schema): Field[] {
  const target = schema.$ref
    ? spec.components.schemas[refName(schema.$ref)]
    : schema

  return Object.entries(target?.properties ?? {}).map(([name, property]) => ({
    name,
    type: typeOf(property),
    required: target?.required?.includes(name) ?? false,
    description: property.description ?? "",
  }))
}

/** Every route as method, path and operation, in the API's order. */
export function operationsOf(paths: OpenApi["paths"]) {
  return Object.entries(paths).flatMap(([path, methods]) =>
    Object.entries(methods).map(([method, operation]) => ({
      method: method.toUpperCase(),
      path,
      operation,
    }))
  )
}

/** The schema a successful answer (2xx) carries, if any. */
export function successSchema(operation: Operation): Schema | null {
  const [, answer] =
    Object.entries(operation.responses).find(([code]) =>
      code.startsWith("2")
    ) ?? []

  return answer?.content?.["application/json"]?.schema ?? null
}

/** The schema a request's JSON body takes, if any. */
export function bodySchema(operation: Operation): Schema | null {
  return operation.requestBody?.content["application/json"]?.schema ?? null
}

/** The error answers an operation lists (FastAPI's 422 left out), as code and description. */
export function errorsOf(operation: Operation) {
  return Object.entries(operation.responses)
    .filter(([code]) => !code.startsWith("2") && code !== "422")
    .map(([code, answer]) => ({ code, description: answer.description }))
}

/** The schemas the docs describe, by name. */
export function schemasOf(spec: OpenApi) {
  return Object.entries(spec.components.schemas).filter(
    ([name]) => !HIDDEN_SCHEMAS.includes(name)
  )
}

// A numbered step: "1. ", its text going on over indented lines.
const STEP = /^\d+\.\s+/

type Pieces = ReturnType<typeof pieces>

/** The description split at its "# " titles, by tab ("# Web hooks" is "webhooks"): what each of
 * the developer docs' tabs says before its own reference. */
export function descriptionTabs(text: string): Record<string, string> {
  const tabs: Record<string, string> = {}

  for (const part of text.split(/^# /m).slice(1)) {
    const [title, ...rest] = part.split("\n")
    tabs[title.trim().toLowerCase().replace(/\s+/g, "")] = rest
      .join("\n")
      .trim()
  }

  return tabs
}

/** A description's sections: its text up to the first "## " title (title null), then each
 * title with the blocks under it. A block is a paragraph, numbered steps when every line
 * starts a step ("1. ", "2. ") or goes on with one (indented), or code between "```" lines, kept
 * as written, with its language ("```python"; blocks that follow each other are one example in
 * several languages); text comes as text, bold, code and link pieces ("**", "`", "[text](href)"). */
export function richText(text: string) {
  const sections: {
    title: string | null
    blocks: {
      steps: Pieces[] | null
      pieces: Pieces
      // One example in its languages: code blocks that follow each other.
      code?: { code: string; language?: string }[]
    }[]
  }[] = [{ title: null, blocks: [] }]

  for (const block of blocksOf(text)) {
    const lines = block.split("\n")

    if (block.startsWith("```")) {
      const blocks = sections[sections.length - 1].blocks
      const variant = {
        code: lines.slice(1, -1).join("\n"),
        language: lines[0].slice(3).trim() || undefined,
      }
      const previous = blocks[blocks.length - 1]

      if (previous?.code) {
        previous.code.push(variant)
      } else {
        blocks.push({ steps: null, pieces: [], code: [variant] })
      }
    } else if (block.startsWith("## ")) {
      sections.push({ title: block.slice(3).trim(), blocks: [] })
    } else if (lines.every((line) => STEP.test(line) || /^\s/.test(line))) {
      sections[sections.length - 1].blocks.push({
        steps: block
          .split(/\n(?=\d+\.\s)/)
          .map((step) => pieces(step.replace(STEP, ""))),
        pieces: [],
      })
    } else {
      sections[sections.length - 1].blocks.push({
        steps: null,
        pieces: pieces(block),
      })
    }
  }

  return sections.filter((section) => section.title || section.blocks.length)
}

/** The text's blocks, split at blank lines, but each code fence whole, blank lines and all. */
function blocksOf(text: string) {
  return text
    .split(/^(```[^\n]*\n[\s\S]*?\n```)$/m)
    .flatMap((chunk) =>
      chunk.startsWith("```") ? [chunk] : chunk.split(/\n\s*\n/)
    )
    .filter((block) => block.trim())
}

function pieces(paragraph: string) {
  return paragraph
    .replace(/\s*\n\s*/g, " ")
    .split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/)
    .filter(Boolean)
    .map((piece) => {
      const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(piece)

      if (link) {
        return { text: link[1], kind: "link" as const, href: link[2] }
      }

      if (piece.startsWith("**")) {
        return { text: piece.slice(2, -2), kind: "bold" as const }
      }

      if (piece.startsWith("`")) {
        return { text: piece.slice(1, -1), kind: "code" as const }
      }

      return { text: piece, kind: "text" as const }
    })
}
