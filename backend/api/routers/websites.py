"""Website onboarding + management endpoints (Admin Portal)."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from knowledge.db import clear_website as clear_knowledge_chunks
from knowledge.db import init_schema as init_knowledge_schema
from flows.db import init_schema as init_flows_schema
from websites.db import (
    create_website,
    delete_website as db_delete_website,
    get_connection,
    get_website,
    init_schema as init_websites_schema,
    list_websites,
)
from websites.pipeline import run_ingestion_pipeline

from ..auth import require_admin

router = APIRouter(prefix="/api/websites", tags=["websites"], dependencies=[Depends(require_admin)])


class CreateWebsiteRequest(BaseModel):
    url: str
    name: str
    max_pages: int = 25
    max_depth: int = 2


@router.post("")
def create(req: CreateWebsiteRequest, background_tasks: BackgroundTasks) -> dict:
    conn = get_connection()
    try:
        init_websites_schema(conn)
        website = create_website(conn, req.url, req.name, req.max_pages, req.max_depth)
    finally:
        conn.close()

    background_tasks.add_task(
        run_ingestion_pipeline, website.id, website.website_id, website.url, website.max_pages, website.max_depth
    )
    return website.model_dump()


@router.get("")
def list_all() -> list[dict]:
    conn = get_connection()
    try:
        init_websites_schema(conn)
        return [w.model_dump() for w in list_websites(conn)]
    finally:
        conn.close()


@router.get("/{website_pk}")
def get_one(website_pk: int) -> dict:
    conn = get_connection()
    try:
        init_websites_schema(conn)
        website = get_website(conn, website_pk)
        if website is None:
            raise HTTPException(status_code=404, detail="Website not found")
        return website.model_dump()
    finally:
        conn.close()


@router.post("/{website_pk}/reingest")
def reingest(website_pk: int, background_tasks: BackgroundTasks) -> dict:
    conn = get_connection()
    try:
        init_websites_schema(conn)
        website = get_website(conn, website_pk)
        if website is None:
            raise HTTPException(status_code=404, detail="Website not found")
    finally:
        conn.close()

    background_tasks.add_task(
        run_ingestion_pipeline, website.id, website.website_id, website.url, website.max_pages, website.max_depth
    )
    return website.model_dump()


@router.delete("/{website_pk}")
def delete(website_pk: int) -> dict:
    conn = get_connection()
    try:
        init_websites_schema(conn)
        init_knowledge_schema(conn)
        init_flows_schema(conn)
        website = get_website(conn, website_pk)
        if website is None:
            raise HTTPException(status_code=404, detail="Website not found")
        clear_knowledge_chunks(conn, website.website_id)
        conn.execute("DELETE FROM flows WHERE website_id = %s", (website.website_id,))
        db_delete_website(conn, website_pk)
        return {"status": "deleted"}
    finally:
        conn.close()
