from langgraph.graph.state import StateGraph
from langgraph.graph import END
from .state import PipelineState
from .nodes import (
    extract_node,
    mapping_node,
    validation_node,
    output_node,
)

# Build graph
def build_graph():

    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("map", mapping_node)
    workflow.add_node("validate", validation_node)
    workflow.add_node("output", output_node)

    # Start → Extract
    workflow.set_entry_point("extract")

    # Extract → Mapping
    workflow.add_edge("extract", "map")

    # Mapping → Validation
    workflow.add_edge("map", "validate")

    # Validation → Output
    workflow.add_edge("validate", "output")

    # Output → END
    workflow.add_edge("output", END)

    # Compile the graph
    return workflow.compile()
