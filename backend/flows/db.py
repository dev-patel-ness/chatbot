"""PostgreSQL storage + CRUD for flows (architecture.md §9-10)."""
from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

from knowledge.db import get_connection  # reuse shared connection/DSN setup

from .models import Flow, FlowStep

__all__ = ["get_connection", "init_schema", "create_flow", "list_flows", "get_flow", "delete_flow"]


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS flows (
            id BIGSERIAL PRIMARY KEY,
            website_id TEXT NOT NULL,
            flow_name TEXT NOT NULL,
            trigger JSONB NOT NULL DEFAULT '[]',
            steps JSONB NOT NULL DEFAULT '[]',
            published BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS flows_website_idx ON flows (website_id)")


def _row_to_flow(row: tuple) -> Flow:
    flow_id, website_id, flow_name, trigger, steps, published = row
    return Flow(
        id=flow_id,
        website_id=website_id,
        flow_name=flow_name,
        trigger=trigger,
        steps=[FlowStep.model_validate(s) for s in steps],
        published=published,
    )


def create_flow(conn: psycopg.Connection, website_id: str, flow_name: str, trigger: list[str], steps: list[FlowStep]) -> Flow:
    row = conn.execute(
        """
        INSERT INTO flows (website_id, flow_name, trigger, steps)
        VALUES (%s, %s, %s, %s)
        RETURNING id, website_id, flow_name, trigger, steps, published
        """,
        (website_id, flow_name, Jsonb(trigger), Jsonb([s.model_dump() for s in steps])),
    ).fetchone()
    return _row_to_flow(row)


def list_flows(conn: psycopg.Connection, website_id: str) -> list[Flow]:
    rows = conn.execute(
        "SELECT id, website_id, flow_name, trigger, steps, published FROM flows WHERE website_id = %s ORDER BY id",
        (website_id,),
    ).fetchall()
    return [_row_to_flow(row) for row in rows]


def get_flow(conn: psycopg.Connection, flow_id: int) -> Flow | None:
    row = conn.execute(
        "SELECT id, website_id, flow_name, trigger, steps, published FROM flows WHERE id = %s", (flow_id,)
    ).fetchone()
    return _row_to_flow(row) if row else None


def rename_flow(conn: psycopg.Connection, flow_id: int, new_name: str) -> None:
    conn.execute("UPDATE flows SET flow_name = %s, updated_at = now() WHERE id = %s", (new_name, flow_id))


def set_triggers(conn: psycopg.Connection, flow_id: int, triggers: list[str]) -> None:
    conn.execute("UPDATE flows SET trigger = %s, updated_at = now() WHERE id = %s", (Jsonb(triggers), flow_id))


def set_steps(conn: psycopg.Connection, flow_id: int, steps: list[FlowStep]) -> None:
    conn.execute(
        "UPDATE flows SET steps = %s, updated_at = now() WHERE id = %s",
        (Jsonb([s.model_dump() for s in steps]), flow_id),
    )


def add_step(conn: psycopg.Connection, flow_id: int, step: FlowStep, position: int | None = None) -> Flow:
    flow = get_flow(conn, flow_id)
    if flow is None:
        raise ValueError(f"Flow {flow_id} not found")
    steps = list(flow.steps)
    if position is None or position >= len(steps):
        steps.append(step)
    else:
        steps.insert(position, step)
    set_steps(conn, flow_id, steps)
    return get_flow(conn, flow_id)


def remove_step(conn: psycopg.Connection, flow_id: int, index: int) -> Flow:
    flow = get_flow(conn, flow_id)
    if flow is None:
        raise ValueError(f"Flow {flow_id} not found")
    steps = list(flow.steps)
    if 0 <= index < len(steps):
        steps.pop(index)
    set_steps(conn, flow_id, steps)
    return get_flow(conn, flow_id)


def reorder_steps(conn: psycopg.Connection, flow_id: int, new_order: list[int]) -> Flow:
    flow = get_flow(conn, flow_id)
    if flow is None:
        raise ValueError(f"Flow {flow_id} not found")
    steps = [flow.steps[i] for i in new_order]
    set_steps(conn, flow_id, steps)
    return get_flow(conn, flow_id)


def set_published(conn: psycopg.Connection, flow_id: int, published: bool) -> Flow:
    conn.execute("UPDATE flows SET published = %s, updated_at = now() WHERE id = %s", (published, flow_id))
    return get_flow(conn, flow_id)


def delete_flow(conn: psycopg.Connection, flow_id: int) -> None:
    conn.execute("DELETE FROM flows WHERE id = %s", (flow_id,))
