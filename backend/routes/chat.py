# ============================================================
# ALZHEIMER MRI STAGING - MEDICAL AI CHAT ROUTE
# ============================================================

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.services.chat_service import get_chat_provider

router = APIRouter(prefix="/api", tags=["Medical Assistant"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or inquiry")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous session conversation turns")
    mri_context: Optional[Dict[str, Any]] = Field(default=None, description="Structured prediction from current session")


class ChatSourceItem(BaseModel):
    name: str
    url: Optional[str] = None


class ChatMessageResponse(BaseModel):
    answer: str
    sources: List[ChatSourceItem]
    category: str
    disclaimer: str


# Simple in-memory rate tracking (client IP -> timestamps)
_client_request_history: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60.0  # 1 minute
MAX_REQUESTS_PER_WINDOW = 30  # Max 30 questions per minute per client


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_with_medical_assistant(
    request: Request,
    payload: ChatMessageRequest
):
    """
    Handle medical education and MRI report inquiries using NEUROSTAGE AI Medical Assistant.
    Provides structured, evidence-based, medically safe answers with clinical justification.
    """
    client_ip = request.client.host if request.client else "anonymous"
    import time
    now = time.time()

    # Rate limiting check
    if client_ip in _client_request_history:
        timestamps = [t for t in _client_request_history[client_ip] if now - t < RATE_LIMIT_WINDOW]
        _client_request_history[client_ip] = timestamps
        if len(timestamps) >= MAX_REQUESTS_PER_WINDOW:
            raise HTTPException(
                status_code=429,
                detail="Too many questions requested in a short period. Please pause and try again in a moment."
            )
        _client_request_history[client_ip].append(now)
    else:
        _client_request_history[client_ip] = [now]

    # Clean message text
    cleaned_message = payload.message.strip()
    if not cleaned_message:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        provider = get_chat_provider()
        result = await provider.get_response(
            message=cleaned_message,
            history=payload.history,
            mri_context=payload.mri_context
        )

        return ChatMessageResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            category=result.get("category", "alzheimer_information"),
            disclaimer=result.get("disclaimer", "Medical information only — not a clinical diagnosis.")
        )
    except Exception as e:
        # Never leak API keys or internal stack traces to the client
        print(f"[ChatRoute ERROR] {str(e)}")
        return ChatMessageResponse(
            answer="I am unable to process your request right now. Please try asking again in a few moments.",
            sources=[],
            category="error_fallback",
            disclaimer="NEUROSTAGE AI Medical Assistant provides educational information only."
        )
