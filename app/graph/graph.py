from langgraph.graph import StateGraph, END

from graph.edges import route_after_validation, route_after_sql_generate
from graph.nodes import Graph
from graph.states import GraphState

workflow = StateGraph(GraphState)

graph = Graph()

workflow.add_node("db_schema_node", graph.db_schema_node)
workflow.add_node("sql_generate_node", graph.sql_generate_node)
workflow.add_node("sql_exec_node", graph.sql_exec_node)
workflow.add_node("export_node", graph.export_node)

workflow.set_entry_point("db_schema_node")

workflow.add_edge("db_schema_node", "sql_generate_node")
workflow.add_conditional_edges("sql_generate_node", route_after_sql_generate,
                               {
                                   "error": END,
                                   "exec": "sql_exec_node"
                               })
workflow.add_conditional_edges("sql_exec_node", route_after_validation,
                               {
                                   "error": "sql_generate_node",
                                   "export": "export_node",
                               })
workflow.add_edge("export_node", END)

graph_compile = workflow.compile()
