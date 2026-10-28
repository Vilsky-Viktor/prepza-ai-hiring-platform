import { readFile } from "node:fs/promises"
import path from "node:path"

import { MCP_EXAMPLES, MCP_EXAMPLES_DIR } from "@/constants/mcp-docs"
import type { McpExample } from "@/types/mcp"

/** The example agents, each in Python and TypeScript, read from their files: the files shown
 * are the ones that are run. */
export async function mcpExamples(): Promise<McpExample[]> {
  const root = path.join(process.cwd(), MCP_EXAMPLES_DIR)

  return Promise.all(
    MCP_EXAMPLES.map(async ({ key, title, text, files }) => ({
      key,
      title,
      text,
      code: {
        python: await readFile(path.join(root, "python", files.python), "utf8"),
        typescript: await readFile(
          path.join(root, "typescript", files.typescript),
          "utf8"
        ),
      },
    }))
  )
}
