from graph.states import GraphState


def route_after_validation(state: GraphState):
    valid_result = state["valid_result"]

    if valid_result is None:
        return "error"
    return "export"


def route_after_sql_generate(state: GraphState):
    final_result = state["final_result"]

    if final_result is not None:
        return "error"
    return "exec"
