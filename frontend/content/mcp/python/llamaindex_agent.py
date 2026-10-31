# pip install "llama-index-core==0.14.25" "llama-index-llms-anthropic==0.12.3" "llama-index-tools-mcp==0.4.8" "mcp==1.30.0"
import asyncio

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

from testee_auth import TESTEE_MCP, connection

QUESTION = "Which candidates passed my latest interview?"


async def main() -> None:
    client = BasicMCPClient(TESTEE_MCP, **connection())
    tools = await McpToolSpec(client=client).to_tool_list_async()
    agent = FunctionAgent(tools=tools, llm=Anthropic(model="claude-opus-5-5"))
    print(await agent.run(QUESTION))


asyncio.run(main())
