// npm install @llamaindex/tools@0.2.1 @llamaindex/workflow@1.1.25 @llamaindex/anthropic@0.3.27 @modelcontextprotocol/sdk@1.32.1
import { Anthropic } from "@llamaindex/anthropic"
import { mcp } from "@llamaindex/tools"
import { agent } from "@llamaindex/workflow"

import { TESTEE_MCP, signIn } from "./testee-auth.js"

const QUESTION = "Which candidates passed my latest interview?"

async function main() {
  const { authProvider, headers } = await signIn()
  const server = mcp({
    url: TESTEE_MCP,
    authProvider,
    requestInit: { headers },
  })
  const testee = agent({
    // A model this package knows takes tools: it doesn't yet know Claude's 5 models.
    llm: new Anthropic({ model: "claude-sonnet-4-6" }),
    tools: await server.tools(),
  })
  const result = await testee.run(QUESTION)
  console.log(result.data.result)
  await server.cleanup()
}

main()
