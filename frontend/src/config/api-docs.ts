// The developer docs' tabs, in order: the API, its web hooks and the SDK (each with its part of
// the API's description, lib/openapi.ts descriptionTabs), the MCP server (config/mcp-docs.ts)
// and the objects they return. The first is the page's own address.
export const DOC_TABS = ["api", "webhooks", "sdk", "mcp", "objects"] as const

export type DocTab = (typeof DOC_TABS)[number]
