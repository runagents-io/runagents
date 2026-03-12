"""LangGraph agent with a tool-calling node.

The runtime finds the `graph` variable (a CompiledGraph) and wraps it.
Each POST /invoke calls graph.invoke({"messages": [HumanMessage(content=message)]}).

The platform sets OPENAI_BASE_URL automatically so ChatOpenAI routes
through the LLM Gateway without any configuration.

Deploy:
    runagents deploy --files agent.py,requirements.txt --name langgraph-agent
"""
import os
import json
import requests
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# --- State ---

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# --- LLM ---

llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

CALCULATOR_URL = os.environ.get("TOOL_URL_CALCULATOR", "http://calculator.agent-system.svc:8080")

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform arithmetic: add, subtract, multiply, divide",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "op": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                },
                "required": ["a", "b", "op"],
            },
        },
    }
]

llm_with_tools = llm.bind_tools(tools_schema)


# --- Nodes ---

def call_model(state: AgentState) -> AgentState:
    """Call the LLM with the current messages."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def call_tools(state: AgentState) -> AgentState:
    """Execute tool calls from the last LLM response."""
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        if tc["name"] == "calculate":
            resp = requests.post(f"{CALCULATOR_URL}/calculate", json=tc["args"])
            results.append(
                ToolMessage(content=json.dumps(resp.json()), tool_call_id=tc["id"])
            )
        else:
            results.append(
                ToolMessage(content=f"Unknown tool: {tc['name']}", tool_call_id=tc["id"])
            )
    return {"messages": results}


def should_call_tools(state: AgentState) -> str:
    """Route to tools node if the LLM made tool calls, otherwise end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


# --- Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("model", call_model)
workflow.add_node("tools", call_tools)

workflow.add_edge(START, "model")
workflow.add_conditional_edges("model", should_call_tools, {"tools": "tools", "end": END})
workflow.add_edge("tools", "model")

# The runtime discovers this variable by name and wraps it
graph = workflow.compile()
