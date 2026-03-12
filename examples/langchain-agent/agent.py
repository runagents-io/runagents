"""LangChain agent with tools -- auto-discovered by the runtime.

The runtime finds the `executor` variable (an AgentExecutor) and wraps it.
Each POST /invoke calls executor.invoke({"input": message}).

The platform sets OPENAI_BASE_URL automatically so ChatOpenAI routes
through the LLM Gateway without any configuration.

Deploy:
    runagents deploy --files agent.py,requirements.txt --name langchain-agent
"""
import os
import requests
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool


# The platform sets OPENAI_BASE_URL automatically -- ChatOpenAI reads it
llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

WEATHER_URL = os.environ.get("TOOL_URL_WEATHER", "http://weather.agent-system.svc:8080")
CALCULATOR_URL = os.environ.get("TOOL_URL_CALCULATOR", "http://calculator.agent-system.svc:8080")


@tool
def get_weather(city: str) -> str:
    """Get current weather conditions for a city."""
    resp = requests.post(f"{WEATHER_URL}/weather/lookup", json={"city": city})
    data = resp.json()
    return f"{data.get('condition', 'Unknown')}, {data.get('temp_c', '?')}°C"


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression. Supports: add, subtract, multiply, divide."""
    parts = expression.split()
    if len(parts) == 3:
        a, op, b = float(parts[0]), parts[1], float(parts[2])
        resp = requests.post(
            f"{CALCULATOR_URL}/calculate",
            json={"a": a, "b": b, "op": op},
        )
        return str(resp.json().get("result", "error"))
    return "Invalid expression format. Use: <number> <op> <number>"


prompt = ChatPromptTemplate.from_messages([
    ("system", os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant with access to weather and calculator tools.")),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, [get_weather, calculate], prompt)

# The runtime discovers this variable by name and wraps it
executor = AgentExecutor(agent=agent, tools=[get_weather, calculate], verbose=True)
