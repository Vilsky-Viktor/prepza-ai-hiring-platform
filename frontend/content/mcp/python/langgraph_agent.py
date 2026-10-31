# pip install "langgraph==1.2.15" "langchain-anthropic==1.7.6" "langchain-mcp-adapters==0.3.2" "mcp==1.30.0"
import asyncio

from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from testee_auth import TESTEE_MCP, connection

QUESTION = "Which candidates passed my latest interview?"


async def main() -> None:
    server = {"transport": "streamable_http", "url": TESTEE_MCP, **connection()}
    tools = await MultiServerMCPClient({"testee": server}).get_tools()
    model = ChatAnthropic(model="claude-opus-5-5").bind_tools(tools)

    async def call_model(state: MessagesState) -> dict:
        return {"messages": [await model.ainvoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    result = await graph.compile().ainvoke({"messages": [("user", QUESTION)]})
    print(result["messages"][-1].content)


asyncio.run(main())
