"""Flow management endpoints wrapping flows/db.py CRUD (Admin Portal)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from flows.db import (
    add_step,
    delete_flow,
    get_connection,
    get_flow,
    init_schema,
    list_flows,
    remove_step,
    rename_flow,
    reorder_steps,
    set_published,
    set_triggers,
)
from flows.discovery import FlowDiscoveryEngine
from flows.models import FlowStep
from understanding.bedrock_client import BedrockClient

from ..auth import require_admin

router = APIRouter(prefix="/api/flows", tags=["flows"], dependencies=[Depends(require_admin)])

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")


@router.get("")
def list_all(website_id: str) -> list[dict]:
    conn = get_connection()
    try:
        init_schema(conn)
        return [f.model_dump() for f in list_flows(conn, website_id)]
    finally:
        conn.close()


@router.get("/{flow_id}")
def get_one(flow_id: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        flow = get_flow(conn, flow_id)
        if flow is None:
            raise HTTPException(status_code=404, detail="Flow not found")
        return flow.model_dump()
    finally:
        conn.close()


class UpdateFlowRequest(BaseModel):
    flow_name: str | None = None
    trigger: list[str] | None = None


@router.patch("/{flow_id}")
def update(flow_id: int, req: UpdateFlowRequest) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        if req.flow_name is not None:
            rename_flow(conn, flow_id, req.flow_name)
        if req.trigger is not None:
            set_triggers(conn, flow_id, req.trigger)
        flow = get_flow(conn, flow_id)
        if flow is None:
            raise HTTPException(status_code=404, detail="Flow not found")
        return flow.model_dump()
    finally:
        conn.close()


class AddStepRequest(BaseModel):
    type: str
    options: list[str] = []
    position: int | None = None


@router.post("/{flow_id}/steps")
def add_flow_step(flow_id: int, req: AddStepRequest) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        flow = add_step(conn, flow_id, FlowStep(type=req.type, options=req.options), position=req.position)
        return flow.model_dump()
    finally:
        conn.close()


@router.delete("/{flow_id}/steps/{index}")
def remove_flow_step(flow_id: int, index: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        flow = remove_step(conn, flow_id, index)
        return flow.model_dump()
    finally:
        conn.close()


class ReorderRequest(BaseModel):
    order: list[int]


@router.post("/{flow_id}/reorder")
def reorder(flow_id: int, req: ReorderRequest) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        flow = reorder_steps(conn, flow_id, req.order)
        return flow.model_dump()
    finally:
        conn.close()


@router.post("/{flow_id}/publish")
def publish(flow_id: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        return set_published(conn, flow_id, True).model_dump()
    finally:
        conn.close()


@router.post("/{flow_id}/unpublish")
def unpublish(flow_id: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        return set_published(conn, flow_id, False).model_dump()
    finally:
        conn.close()


@router.delete("/{flow_id}")
def delete(flow_id: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        delete_flow(conn, flow_id)
        return {"status": "deleted"}
    finally:
        conn.close()


class DiscoverRequest(BaseModel):
    website_id: str
    understanding_path: str | None = None


@router.post("/discover")
def discover(req: DiscoverRequest) -> list[dict]:
    conn = get_connection()
    try:
        init_schema(conn)
        path = req.understanding_path or f"./output/{req.website_id}/understanding/understanding.json"
        client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        flows = FlowDiscoveryEngine(client).run(conn, path, req.website_id)
        return [f.model_dump() for f in flows]
    finally:
        conn.close()
