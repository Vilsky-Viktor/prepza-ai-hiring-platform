// The assistant's public list of the MCP server's tools and limits (GET /api/assistant/mcp/tools).

export type McpTool = {
  name: string
  description: string
  read_only: boolean
  destructive: boolean
  idempotent: boolean
  // The API key permission it needs ("mcp": nothing more); null: keys don't get it.
  key_permission: string | null
}

export type McpTools = {
  tools: McpTool[]
  limits: {
    calls_per_minute: number
    calls_per_day: number
    writes_per_hour: number
  }
}

// An example agent, in each language: its files' contents.
export type McpExample = {
  key: string
  title: string
  text: string
  code: Record<"python" | "typescript", string>
}
