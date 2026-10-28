import { HighlightedCode } from "@/components/common/highlighted-code"
import { SetupSection } from "@/components/common/ai-apps-setup"
import { TabPanels } from "@/components/tab-panels"
import { MCP_LANGUAGES } from "@/config/mcp-docs"
import type { McpExample } from "@/types/mcp"

/** The shared sign-in file, then the agents (LangGraph, LangChain, LlamaIndex) as tabs; each in
 * an editor whose header picks its language. */
export function McpExamples({ examples }: { examples: McpExample[] }) {
  const [signIn, ...agents] = examples

  return (
    <div className="space-y-10">
      {signIn && (
        <SetupSection
          title={<span className="normal-case">{signIn.title}</span>}
          text={signIn.text}
        >
          <Editor example={signIn} />
        </SetupSection>
      )}
      <TabPanels
        panels={agents.map((agent) => ({
          id: agent.key,
          label: agent.title,
          content: (
            <div className="space-y-4">
              <p className="text-base text-muted-foreground">{agent.text}</p>
              <Editor example={agent} />
            </div>
          ),
        }))}
      />
    </div>
  )
}

function Editor({ example }: { example: McpExample }) {
  return (
    <HighlightedCode
      variants={MCP_LANGUAGES.map((language) => ({
        code: example.code[language],
        language,
      }))}
    />
  )
}
