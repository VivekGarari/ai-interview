from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional

from app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Orchestration"])


class RoutingRequest(BaseModel):
    task_type: str = "coding"
    capabilities: Optional[Dict[str, bool]] = None
    prompt: str = ""


@router.get("/capabilities")
def get_capabilities():
    return {
        "status": "ok",
        "capabilities": ai_service.get_capabilities(),
        "default_provider": ai_service.default_provider,
    }


@router.post("/route")
def route_request(payload: RoutingRequest):
    provider = ai_service.get_provider_for_task(payload.task_type, payload.capabilities or {})
    return {
        "task_type": payload.task_type,
        "provider": provider,
        "prompt_preview": payload.prompt[:120] if payload.prompt else "",
        "message": f"Route {payload.task_type} work to {provider}",
    }
