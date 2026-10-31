// npm install @langchain/langgraph@1.5.0 @langchain/core@1.2.18 @langchain/anthropic@1.5.12 @langchain/mcp-adapters@1.1.4 @modelcontextprotocol/sdk@1.32.1
import { ChatAnthropic } from "@langchain/anthropic"
import { MessagesAnnotation, START, StateGraph } from "@langchain/langgraph"
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt"
import { MultiServerMCPClient } from "@langchain/mcp-adapters"

import { TESTEE_MCP, signIn } from "./testee-auth.js"

const QUESTION = "Which candidates passed my latest interview?"

async function main() {
  const client = new MultiServerMCPClient({
    mcpServers: {
      testee: { transport: "http", url: TESTEE_MCP, ...(await signIn()) },
    },
  })
  const tools = await client.getTools()
  const model = new ChatAnthropic({ model: "claude-opus-5-5" }).bindTools(tools)
  const graph = new StateGraph(MessagesAnnotation)
    .addNode("model", async (state) => ({
      messages: [await model.invoke(state.messages)],
    }))
    .addNode("tools", new ToolNode(tools))
    .addEdge(START, "model")
    .addConditionalEdges("model", toolsCondition)
    .addEdge("tools", "model")
    .compile()
  const result = await graph.invoke({
    messages: [{ role: "user", content: QUESTION }],
  })
  console.log(result.messages.at(-1)?.content)
  await client.close()
}

main()
