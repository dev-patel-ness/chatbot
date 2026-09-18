"""Mock action APIs (architecture.md §13). Simulates website-specific business backends."""
from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ness Mock Actions API")

SERVICES = [
    {"id": "cloud-services", "name": "Cloud Services", "url": "https://www.ness.com/services/cloud-services"},
    {"id": "data-and-ai", "name": "Data & AI", "url": "https://www.ness.com/services/data-and-ai"},
    {"id": "innovation-design", "name": "Innovation & Design", "url": "https://www.ness.com/services/innovation-design"},
    {"id": "integration-and-streaming", "name": "Integration & Streaming", "url": "https://www.ness.com/services/integration-and-streaming"},
    {"id": "intelligent-engineering", "name": "Intelligent Engineering", "url": "https://www.ness.com/services/intelligent-engineering"},
    {"id": "salesforce", "name": "Salesforce", "url": "https://www.ness.com/services/salesforce"},
]


@app.get("/api/services")
def list_services() -> dict:
    return {"services": SERVICES}


@app.get("/api/services/{service_id}")
def get_service(service_id: str) -> dict:
    for service in SERVICES:
        if service["id"] == service_id:
            return service
    raise HTTPException(status_code=404, detail="Service not found")


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str


@app.post("/api/contact")
def submit_contact(payload: ContactRequest) -> dict:
    return {
        "status": "received",
        "ticket_id": f"TCK-{uuid.uuid4().hex[:8].upper()}",
        "name": payload.name,
        "email": payload.email,
    }


class BookDemoRequest(BaseModel):
    name: str
    email: str
    preferred_date: str


@app.post("/api/book-demo")
def book_demo(payload: BookDemoRequest) -> dict:
    return {
        "status": "scheduled",
        "demo_id": f"DEMO-{uuid.uuid4().hex[:8].upper()}",
        "name": payload.name,
        "email": payload.email,
        "scheduled_date": payload.preferred_date,
    }
