import { readFileSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import { ADMIN_MESSAGES, SERVER_ONLY_MESSAGES } from "@/config/i18n"

import { SOURCE_ROOT, sourceFiles } from "../source-files"

// The groups each client component asks for with useTranslations("group…").
function clientGroups() {
  return sourceFiles(
    ["app", "components", "features", "hooks", "providers"],
    /\.tsx?$/
  )
    .filter((file) =>
      readFileSync(file, "utf8").trimStart().startsWith('"use client"')
    )
    .flatMap((file) =>
      [
        ...readFileSync(file, "utf8").matchAll(/useTranslations\(\s*"([\w]+)/g),
      ].map(([, group]) => ({ file: path.relative(SOURCE_ROOT, file), group }))
    )
}

describe("the messages the browser gets", () => {
  it("leaves out only groups no client component uses", () => {
    const used = clientGroups().filter(({ group }) =>
      (SERVER_ONLY_MESSAGES as readonly string[]).includes(group)
    )

    expect(used).toEqual([])
  })

  it("gives the admin zone's group only to admin zone components", () => {
    const outside = clientGroups().filter(
      ({ file, group }) =>
        (ADMIN_MESSAGES as readonly string[]).includes(group) &&
        !file.startsWith("app/superadmin") &&
        !file.startsWith("components/superadmin")
    )

    expect(outside).toEqual([])
  })
})
