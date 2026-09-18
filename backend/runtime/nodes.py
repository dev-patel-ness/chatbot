"""Graph node implementations for the Stage 5 LangGraph runtime."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import psycopg
from understanding.bedrock_client import BedrockClient
from knowledge.rag import RagEngine
from tools.executor import ToolExecutor
from safety.checker import SafetyChecker
from safety.models import DEFAULT_UNSAFE_FALLBACK

from .handlers import handle_flow, handle_rag, handle_tool
from .models import ConflictResolution, Intent, IntentDetectionResult, NodeOutput
from .prompts import (
    CONFLICT_RESOLUTION_SYSTEM,
    MULTI_INTENT_DETECTION_SYSTEM,
    UNIFIED_RESPONSE_SYSTEM_TEMPLATE,
    conflict_resolution_user,
    multi_intent_detection_user,
    unified_response_user,
)

logger = logging.getLogger(__name__)


@dataclass
class RuntimeDeps:
    llm_client: BedrockClient
    rag_engine: RagEngine
    tool_executor: ToolExecutor
    safety_checker: SafetyChecker
    conn: psycopg.Connection
    website_id: str
    website_name: str


def node_input_safety(deps: RuntimeDeps, state: dict) -> dict:
    result = deps.safety_checker.check_input(state["user_message"])
    if result.is_safe:
        return {"input_blocked": False}
    return {
        "input_blocked": True,
        "final_response": DEFAULT_UNSAFE_FALLBACK,
        "sources": [],
    }


def route_after_input_safety(state: dict) -> str:
    return "blocked" if state.get("input_blocked") else "detect_intents"


def node_detect_intents(deps: RuntimeDeps, state: dict) -> dict:
    user_prompt = multi_intent_detection_user(state.get("history", []), state["user_message"])
    data = deps.llm_client.invoke_json(MULTI_INTENT_DETECTION_SYSTEM, user_prompt)
    result = IntentDetectionResult.model_validate(data)
    logger.info(
        "Detected %d intent(s), conflicts=%s, strategy=%s",
        len(result.intents), result.has_conflicts, result.strategy,
    )
    return {"intent_result": result.model_dump()}


def route_after_detection(state: dict) -> str:
    return "resolve_conflict" if state["intent_result"]["has_conflicts"] else "execute_intents"


def node_resolve_conflict(deps: RuntimeDeps, state: dict) -> dict:
    intent_result = IntentDetectionResult.model_validate(state["intent_result"])
    user_prompt = conflict_resolution_user(
        [i.model_dump() for i in intent_result.intents],
        conflict_score=0.9,
    )
    data = deps.llm_client.invoke_json(CONFLICT_RESOLUTION_SYSTEM, user_prompt)
    resolution = ConflictResolution.model_validate(data)
    logger.info("Conflict resolution: %s", resolution.resolution)
    return {"conflict_resolution": resolution.model_dump()}


def _dispatch_intent(deps: RuntimeDeps, intent: Intent, conversation: list[str], extra_context: str = "") -> NodeOutput:
    if intent.type == "knowledge_retrieval":
        return handle_rag(deps.rag_engine, deps.conn, deps.website_id, intent, extra_context)
    if intent.type == "flow_trigger":
        return handle_flow(deps.conn, deps.website_id, intent)
    if intent.type == "action":
        return handle_tool(deps.tool_executor, intent, conversation)
    return handle_rag(deps.rag_engine, deps.conn, deps.website_id, intent, extra_context)


def node_execute_intents(deps: RuntimeDeps, state: dict) -> dict:
    intent_result = IntentDetectionResult.model_validate(state["intent_result"])
    intents = sorted(intent_result.intents, key=lambda i: i.priority)
    strategy = intent_result.strategy
    conversation = state.get("history", []) + [state["user_message"]]

    if strategy == "parallel" and len(intents) > 1:
        with ThreadPoolExecutor(max_workers=len(intents)) as pool:
            futures = [pool.submit(_dispatch_intent, deps, intent, conversation) for intent in intents]
            outputs = [f.result() for f in futures]
    elif strategy == "sequential" and len(intents) > 1:
        outputs = []
        running_context = ""
        for intent in intents:
            output = _dispatch_intent(deps, intent, conversation, extra_context=running_context)
            outputs.append(output)
            running_context += f"\n[Earlier in this conversation] {output.text}"
    else:
        outputs = [_dispatch_intent(deps, intents[0], conversation)] if intents else []

    logger.info("Executed %d intent(s) using strategy=%s", len(outputs), strategy)
    return {"node_outputs": [o.model_dump() for o in outputs]}


def node_merge_context(deps: RuntimeDeps, state: dict) -> dict:
    node_outputs = [NodeOutput.model_validate(o) for o in state.get("node_outputs", [])]
    conflict_resolution = state.get("conflict_resolution")

    merged = {
        "primary_topic": node_outputs[0].intent.topic if node_outputs and node_outputs[0].intent.topic else None,
        "all_intents": [o.intent.model_dump() for o in node_outputs],
        "results": [{"node": o.node, "text": o.text, "sources": o.sources} for o in node_outputs],
    }
    if conflict_resolution:
        merged["conflict_resolution"] = conflict_resolution

    all_sources = list(dict.fromkeys(s for o in node_outputs for s in o.sources))
    return {"merged_context": merged, "sources": all_sources}


def node_generate_response(deps: RuntimeDeps, state: dict) -> dict:
    system_prompt = UNIFIED_RESPONSE_SYSTEM_TEMPLATE.format(website_name=deps.website_name)
    user_prompt = unified_response_user(state["merged_context"], state["user_message"])
    final_response = deps.llm_client.invoke(system_prompt, user_prompt, max_tokens=600)
    return {"final_response": final_response}


def node_output_safety(deps: RuntimeDeps, state: dict) -> dict:
    result = deps.safety_checker.check_output(state["final_response"])
    return {"final_response": result.final_response}
