from __future__ import annotations

import logging
import os
from functools import lru_cache
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

DEFAULT_MODEL = os.getenv("TRAVELBUDDY_MODEL", "gpt-4o-mini")
GRAPH_RECURSION_LIMIT = int(os.getenv("TRAVELBUDDY_RECURSION_LIMIT", "8"))
TRACE_ENABLED = os.getenv("TRAVELBUDDY_DEBUG", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

LOGGER = logging.getLogger("travelbuddy")
TOOLS_LIST = (search_flights, search_hotels, calculate_budget)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO if TRACE_ENABLED else logging.WARNING,
        format="%(message)s",
    )


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    prompt_path = BASE_DIR / "system_prompt.txt"
    if not prompt_path.exists():
        raise RuntimeError(f"Không tìm thấy file system prompt: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def ensure_system_message(messages: list[BaseMessage]) -> list[BaseMessage]:
    if messages and isinstance(messages[0], SystemMessage):
        return messages
    return [SystemMessage(content=load_system_prompt()), *messages]


def create_llm() -> ChatOpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Thiếu OPENAI_API_KEY trong file .env hoặc biến môi trường.")
    return ChatOpenAI(model=DEFAULT_MODEL, temperature=0)


def log_agent_trace(tool_calls: list[dict[str, object]]) -> None:
    if not tool_calls:
        LOGGER.info("[Trả lời trực tiếp]")
        return

    for tool_call in tool_calls:
        LOGGER.info("[Gọi tool: %s](%s)", tool_call["name"], tool_call["args"])


def create_agent_node():
    llm_with_tools = create_llm().bind_tools(TOOLS_LIST)

    def agent_node(state: AgentState) -> AgentState:
        response = llm_with_tools.invoke(state["messages"])
        log_agent_trace(getattr(response, "tool_calls", []))
        return {"messages": [response]}

    return agent_node


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", create_agent_node())
    builder.add_node("tools", ToolNode(list(TOOLS_LIST)))

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
    return builder.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()


def invoke_agent(user_input: str, history: list[BaseMessage] | None = None) -> list[BaseMessage]:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise ValueError("user_input không được để trống.")

    history = list(history or [])
    messages = ensure_system_message([*history, HumanMessage(content=cleaned_input)])
    result = get_graph().invoke(
        {"messages": messages},
        config={"recursion_limit": GRAPH_RECURSION_LIMIT},
    )
    return result["messages"]


def main() -> None:
    configure_logging()

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
        try:
            updated_messages = invoke_agent(user_input, conversation)
        except Exception as exc:
            LOGGER.exception("Lỗi khi chạy agent: %s", exc)
            print(
                "\nTravelBuddy: Tôi đang gặp lỗi khi xử lý yêu cầu này. "
                "Vui lòng kiểm tra cấu hình hoặc thử lại."
            )
            continue

        conversation = updated_messages
        final_message = updated_messages[-1]
        print(f"\nTravelBuddy: {final_message.content}")


if __name__ == "__main__":
    main()
