from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from typing import TypedDict
from langchain.tools import Tool

model_name = "llama3.2:3b"


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""

    print("method multiply was called with arguments:", a, b)
    return a * b


# Let's inspect some of the attributes associated with the tool.
print("multiply.name:", multiply.name)
print("multiply.description:", multiply.description)
print("multiply.args:", multiply.args)

llm = ChatOpenAI(
    api_key="none",
    model=model_name,
    base_url="http://localhost:11434/v1",
    streaming=True,
)


# Define the state for the graph
class CalcState(TypedDict):
    input_value: int
    result: int


# Define tools

def add_five(value: int) -> int:
    return value + 5


def multiply_by_two(value: int) -> int:
    return value * 2


add_tool = Tool(name="add_five", func=add_five, description="Adds 5 to a number")
multiply_tool = Tool(name="multiply_by_two", func=multiply_by_two, description="Multiplies a number by 2")

# Create the LangGraph
workflow = StateGraph(TypedDict)


# Define nodes
def start_node(state: CalcState) -> CalcState:
    return state


# Add nodes to the workflow
workflow.add_node("start", start_node)
workflow.add_node("add", add_node)
workflow.add_node("multiply", multiply_node)

# Define edges
workflow.set_entry_point("start")
workflow.add_edge("start", "add")
workflow.add_edge("add", "multiply")

# Compile the workflow
graph = workflow.compile()

# Run the workflow
input_state = {"input_value": 10, "result": 0}
final_state = graph.invoke(input_state)
print("Final Result:", final_state["result"])








from langgraph.graph import StateGraph
from typing import TypedDict
from langchain.tools import Tool

# Define the state for the graph
class CalcState(TypedDict):
    input_value: int
    result: int

# Define tools

def add_five(value: int) -> int:
    return value + 5

def multiply_by_two(value: int) -> int:
    return value * 2

add_tool = Tool(name="add_five", func=add_five, description="Adds 5 to a number")
multiply_tool = Tool(name="multiply_by_two", func=multiply_by_two, description="Multiplies a number by 2")

# Create the LangGraph
workflow = StateGraph(CalcState)

# Define nodes
def start_node(state: CalcState) -> CalcState:
    return state

def add_node(state: CalcState) -> CalcState:
    state["result"] = add_tool.run(state["input_value"])
    return state

def multiply_node(state: CalcState) -> CalcState:
    state["result"] = multiply_tool.run(state["result"])
    return state

# Add nodes to the workflow
workflow.add_node("start", start_node)
workflow.add_node("add", add_node)
workflow.add_node("multiply", multiply_node)

# Define edges
workflow.set_entry_point("start")
workflow.add_edge("start", "add")
workflow.add_edge("add", "multiply")

# Compile the workflow
graph = workflow.compile()

# Run the workflow
input_state = {"input_value": 10, "result": 0}
final_state = graph.invoke(input_state)
print("Final Result:", final_state["result"])



from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

# Define a new graph
workflow = StateGraph(AgentState)

# Define the nodes we will cycle between
workflow.add_node("agent", agent)  # agent
retrieve = ToolNode([retriever_tool])
workflow.add_node("retrieve", retrieve)  # retrieval
workflow.add_node("rewrite", rewrite)  # Re-writing the question
workflow.add_node(
    "generate", generate
)  # Generating a response after we know the documents are relevant
# Call agent node to decide to retrieve or not
workflow.add_edge(START, "agent")

# Decide whether to retrieve
workflow.add_conditional_edges(
    "agent",
    # Assess agent decision
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate", END)
workflow.add_edge("rewrite", "agent")

# Compile
graph = workflow.compile()
