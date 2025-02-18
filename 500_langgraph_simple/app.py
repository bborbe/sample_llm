from langgraph.graph import StateGraph
from typing import TypedDict


# Define the state for the graph
class CalcState(TypedDict):
    input_value: int
    result: int


# Define nodes
def start_node(state: CalcState) -> CalcState:
    state["result"] = state["input_value"]
    return state


def add_node(state: CalcState) -> CalcState:
    state["result"] = state["result"] + 42
    return state


def multiply_node(state: CalcState) -> CalcState:
    state["result"] = state["result"] * 3
    return state


# Create the LangGraph
workflow = StateGraph(CalcState)
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
