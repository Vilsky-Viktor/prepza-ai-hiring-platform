import { CodeEditor } from "@/components/code-editor"
import { DocSection } from "@/components/api-docs/doc-section"
import { McpExamples } from "@/components/api-docs/mcp-examples"
import { RichText } from "@/components/api-docs/rich-text"
import {
  ChatGptSteps,
  ClaudeSteps,
  ServerAddress,
} from "@/components/company/ai-apps-setup"
import { Dotted } from "@/components/dot"
import { TabPanels } from "@/components/tab-panels"
import { MCP_PATH } from "@/constants/ai-apps"
import { LIST_BOX } from "@/constants/lists"
import {
  MCP_AGENTS,
  MCP_CONNECTIONS,
  MCP_INTRO,
  MCP_OTHER_APPS,
  MCP_RULES,
  MCP_SERVER,
  MCP_TITLES,
  MCP_TOOL_LABELS,
  MCP_TOOLS_TEXT,
  MCP_UPDATES,
} from "@/constants/mcp-docs"
import type { McpExample, McpTool, McpTools } from "@/types/mcp"

/** The developer docs' MCP tab: the server and how to sign in, the AI apps' setup as tabs (the AI
 * apps page's own steps for Claude and ChatGPT, then other apps), daily updates, example agents, and the tools and limits as the server
 * lists them. */
export function McpTab({
  site,
  examples,
  tools,
}: {
  site: string
  examples: McpExample[]
  tools: McpTools | null
}) {
  const url = `${site}${MCP_PATH}`

  return (
    <>
      <RichText text={MCP_INTRO} />
      <DocSection title={MCP_TITLES.server}>
        <ServerAddress />
        <RichText text={MCP_SERVER} />
      </DocSection>
      <DocSection title={MCP_TITLES.apps}>
        {/* Each app a tab: Claude's and ChatGPT's steps are the AI apps page's own. */}
        <TabPanels
          panels={[
            {
              id: "claude",
              label: "Claude",
              content: (
                <div className="space-y-4">
                  <ClaudeSteps />
                </div>
              ),
            },
            { id: "chatgpt", label: "ChatGPT", content: <ChatGptSteps /> },
            ...MCP_OTHER_APPS.map((app) => ({
              id: app.label,
              label: app.label,
              content: (
                <div className="space-y-4">
                  <RichText text={app.text} />
                  {app.code && (
                    <CodeEditor
                      code={app.code.replace("{url}", url)}
                      language="json"
                    />
                  )}
                </div>
              ),
            })),
          ]}
        />
      </DocSection>
      <DocSection title={MCP_TITLES.updates}>
        <RichText text={MCP_UPDATES} />
      </DocSection>
      <DocSection title={MCP_TITLES.agents}>
        <RichText text={MCP_AGENTS} />
        <McpExamples examples={examples} />
      </DocSection>
      {tools && (
        <DocSection title={MCP_TITLES.rules}>
          <RichText
            text={MCP_RULES.replace(
              "{minute}",
              String(tools.limits.calls_per_minute)
            )
              .replace("{day}", tools.limits.calls_per_day.toLocaleString("en"))
              .replace("{writes}", String(tools.limits.writes_per_hour))}
          />
        </DocSection>
      )}
      <DocSection title={MCP_TITLES.connections}>
        <RichText text={MCP_CONNECTIONS} />
      </DocSection>
      {/* The tools last: the longest list. */}
      {tools && (
        <DocSection title={MCP_TITLES.tools}>
          <RichText text={MCP_TOOLS_TEXT} />
          <ul className={LIST_BOX}>
            {tools.tools.map((tool) => (
              <ToolRow key={tool.name} tool={tool} />
            ))}
          </ul>
        </DocSection>
      )}
    </>
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
