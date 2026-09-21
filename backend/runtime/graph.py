"""Builds the Stage 5+7 LangGraph state machine (architecture.md §11.1, §14)."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .nodes import (
    RuntimeDeps,
    node_detect_intents,
    node_execute_intents,
    node_generate_response,
    node_input_safety,
    node_merge_context,
    node_output_safety,
    node_resolve_conflict,
    route_after_detection,
    route_after_input_safety,
)


class RuntimeState(TypedDict, total=False):
    website_id: str
    website_name: str
    user_message: str
    history: list[str]
    conversation_id: int
    input_blocked: bool
    intent_result: dict
    conflict_resolution: dict
    node_outputs: list[dict]
    merged_context: dict
    final_response: str
    sources: list[str]


def build_runtime_graph(deps: RuntimeDeps):
    graph = StateGraph(RuntimeState)

    graph.add_node("input_safety", lambda state: node_input_safety(deps, state))
    graph.add_node("detect_intents", lambda state: node_detect_intents(deps, state))
    graph.add_node("resolve_conflict", lambda state: node_resolve_conflict(deps, state))
    graph.add_node("execute_intents", lambda state: node_execute_intents(deps, state))
    graph.add_node("merge_context", lambda state: node_merge_context(deps, state))
    graph.add_node("generate_response", lambda state: node_generate_response(deps, state))
    graph.add_node("output_safety", lambda state: node_output_safety(deps, state))

    graph.add_edge(START, "input_safety")
    graph.add_conditional_edges(
        "input_safety",
        route_after_input_safety,
        {"blocked": END, "detect_intents": "detect_intents"},
    )
    graph.add_conditional_edges(
        "detect_intents",
        route_after_detection,
        {"resolve_conflict": "resolve_conflict", "execute_intents": "execute_intents"},
    )
    graph.add_edge("resolve_conflict", "execute_intents")
    graph.add_edge("execute_intents", "merge_context")
    graph.add_edge("merge_context", "generate_response")
    graph.add_edge("generate_response", "output_safety")
    graph.add_edge("output_safety", END)

    return graph.compile()
