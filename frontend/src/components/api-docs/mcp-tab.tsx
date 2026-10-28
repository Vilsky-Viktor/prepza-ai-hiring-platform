import { HighlightedCode } from "@/components/highlighted-code"
import { DocSection } from "@/components/api-docs/doc-section"
import { McpExamples } from "@/components/api-docs/mcp-examples"
import { RichText } from "@/components/api-docs/rich-text"
import {
  ChatGptSteps,
  ClaudeSteps,
  ServerAddress,
} from "@/components/company/ai-apps-setup"
import { Dotted } from "@/components/dot"
import { MCP_PATH } from "@/config/ai-apps"
import { LIST_BOX } from "@/config/lists"
import {
  MCP_AGENTS,
  MCP_APP_PAGES,
  MCP_CONNECTIONS,
  MCP_INTRO,
  MCP_OTHER_APPS,
  MCP_RULES,
  MCP_SERVER,
  MCP_TITLES,
  MCP_TOOL_LABELS,
  MCP_TOOLS_TEXT,
  MCP_UPDATES,
} from "@/config/mcp-docs"
import type { McpExample, McpTool, McpTools } from "@/types/mcp"

/** The developer docs' MCP tab's overview: the server and how to sign in, daily updates, the
 * rules with the limits as the server sets them, and managing connections. The tools, each AI
 * app's setup and the example agents are pages of their own. */
export function McpTab({ tools }: { tools: McpTools | null }) {
  return (
    <>
      <RichText text={MCP_INTRO} />
      <DocSection title={MCP_TITLES.server}>
        <ServerAddress />
        <RichText text={MCP_SERVER} />
      </DocSection>
      <DocSection title={MCP_TITLES.updates}>
        <RichText text={MCP_UPDATES} />
      </DocSection>
      {tools && <McpRules tools={tools} />}
      <DocSection title={MCP_TITLES.connections}>
        <RichText text={MCP_CONNECTIONS} />
      </DocSection>
    </>
  )
}

/** The MCP tab's example agents. */
export function McpAgents({ examples }: { examples: McpExample[] }) {
  return (
    <DocSection title={MCP_TITLES.agents}>
      <RichText text={MCP_AGENTS} />
      <McpExamples examples={examples} />
    </DocSection>
  )
}

/** The MCP overview's rules, with the limits as the server sets them. */
function McpRules({ tools }: { tools: McpTools }) {
  const { limits } = tools

  return (
    <DocSection title={MCP_TITLES.rules}>
      <RichText
        text={MCP_RULES.replace("{minute}", String(limits.calls_per_minute))
          .replace("{day}", limits.calls_per_day.toLocaleString("en"))
          .replace("{writes}", String(limits.writes_per_hour))}
      />
    </DocSection>
  )
}

/** The MCP tab's tools, as the server lists them. */
export function McpToolList({ tools }: { tools: McpTools }) {
  return (
    <DocSection title={MCP_TITLES.tools}>
      <RichText text={MCP_TOOLS_TEXT} />
      <ul className={LIST_BOX}>
        {tools.tools.map((tool) => (
          <ToolRow key={tool.name} tool={tool} />
        ))}
      </ul>
    </DocSection>
  )
}

/** One AI app's page of the MCP tab: the server's address, then the app's steps (Claude's and
 * ChatGPT's are the AI apps page's own). */
export function McpApp({ site, app }: { site: string; app: string }) {
  const page = MCP_APP_PAGES.find((item) => item.id === app)
  const other = MCP_OTHER_APPS.find((item) => item.id === app)

  return (
    // An app's name keeps its capitals in the lowercase title.
    <DocSection title={<span className="normal-case">{page?.label}</span>}>
      <ServerAddress />
      {app === "claude" && (
        <div className="space-y-4">
          <ClaudeSteps />
        </div>
      )}
      {app === "chatgpt" && <ChatGptSteps />}
      {other && (
        <div className="space-y-4">
          <RichText text={other.text} />
          {other.code && (
            <HighlightedCode
              code={other.code.replace("{url}", `${site}${MCP_PATH}`)}
              language="json"
            />
          )}
        </div>
      )}
    </DocSection>
  )
}

/** A tool as the Objects tab shows a field: its name, what it does to prepza's data and the API
 * key permission it needs, then what it does. */
function ToolRow({ tool }: { tool: McpTool }) {
  return (
    <li className="space-y-1 px-5 py-4" data-testid="mcp-tool">
      <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <code className="font-mono text-base font-medium">{tool.name}</code>
        <span className="text-sm text-muted-foreground">
          <Dotted
            items={[
              tool.read_only ? MCP_TOOL_LABELS.reads : MCP_TOOL_LABELS.changes,
              tool.destructive && MCP_TOOL_LABELS.destructive,
              tool.key_permission ? (
                <code className="font-mono">{tool.key_permission}</code>
              ) : (
                MCP_TOOL_LABELS.noKey
              ),
            ]}
          />
        </span>
      </p>
      <p className="text-sm text-muted-foreground">{tool.description}</p>
    </li>
  )
}
