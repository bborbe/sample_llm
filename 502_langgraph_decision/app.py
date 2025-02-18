from typing import Literal

import logfire
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()


# Define the state for the graph
class GraphState(BaseModel):
    input_value: int
    result: int


# Define nodes
def start_node(state: GraphState) -> GraphState:
    with logfire.span('start_node {}'.format(state)):
        state.result = state.input_value
        return state


def add_node(state: GraphState) -> GraphState:
    with logfire.span('add_node {}'.format(state)):
        state.result = state.result + 42
        return state


def sub_node(state: GraphState) -> GraphState:
    with logfire.span('sub_node {}'.format(state)):
        state.result = state.result - 23
        return state


def multiply_node(state: GraphState) -> GraphState:
    with logfire.span('multiply_node {}'.format(state)):
        state.result = state.result * 3
        return state


def continue_next(state: GraphState) -> Literal["to_add", "to_sub"]:
    with logfire.span('continue_next {}'.format(state)):
        if state.result % 10 == 0:
            return "to_add"
        else:
            return "to_sub"


# Create the LangGraph
workflow = StateGraph(GraphState)
# Add nodes to the workflow
workflow.add_node("start", start_node)
workflow.add_node("add", add_node)
workflow.add_node("sub", sub_node)
workflow.add_node("multiply", multiply_node)

# Define edges
workflow.set_entry_point("start")
workflow.add_conditional_edges("start", continue_next, {
    "to_add": "add",
    "to_sub": "sub",
})
workflow.add_edge("add", "multiply")
workflow.add_edge("multiply", END)  # End the graph after node_1

# Compile the workflow
graph = workflow.compile()

# Run the workflow
try:
    input_state = {"input_value": 10, "result": 0}
    final_state = graph.invoke(input_state)
    print("Final Result:", final_state["result"])
except Exception as e:
    print("An exception was raised because `a` is an integer rather than a string.")
    print(e)
