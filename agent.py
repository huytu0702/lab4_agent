from __future__ import annotations

from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from tools import calculate_budget, search_flights, search_hotels


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = (BASE_DIR / "system_prompt.txt").read_text(encoding="utf-8")


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools_list)


def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"[Gọi tool: {tool_call['name']}]({tool_call['args']})")
    else:
        print("[Trả lời trực tiếp]")

    return {"messages": [response]}


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "tools",
        END: END,
    },
)
builder.add_edge("tools", "agent")

graph = builder.compile()


def invoke_agent(user_input: str, history: list[BaseMessage] | None = None) -> list[BaseMessage]:
    history = history or []
    result = graph.invoke({"messages": [*history, HumanMessage(content=user_input)]})
    return result["messages"]


if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy — Trợ lý Du lịch Thông minh")
    print("Gõ 'quit' để thoát")
    print("=" * 60)

    conversation: list[BaseMessage] = []

    while True:
        user_input = input("\nBạn: ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if not user_input:
            continue

        print("\n[TravelBuddy đang suy nghĩ...]")
        updated_messages = invoke_agent(user_input, conversation)
        conversation = updated_messages
        final_message = updated_messages[-1]
        print(f"\nTravelBuddy: {final_message.content}")
