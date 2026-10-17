import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.models.job import EmailApprovalRequest
from app.services.aggregator import aggregate_all_jobs
from app.services.email_service import format_daily_digest, send_application_email_with_approval

router = APIRouter(prefix="/api/v1/email", tags=["Email & Alerts"])

class DigestSendRequest(BaseModel):
    recipient_email: Optional[str] = None
    min_score: int = 70

@router.get("/digest/preview")
async def preview_daily_digest(
    min_score: int = Query(70, ge=0, le=100, description="Minimum match score threshold")
):
    """Generates preview HTML and plain-text representation of daily digest for high-match jobs."""
    jobs_response = await aggregate_all_jobs(limit=50)
    digest = format_daily_digest(jobs_response.results, min_score=min_score)
    return digest

@router.post("/digest/send")
async def send_daily_digest(payload: DigestSendRequest):
    """Sends or simulates sending the daily high-match job digest."""
    recipient = payload.recipient_email or os.getenv("DIGEST_RECIPIENT_EMAIL", "ansernawaz786@gmail.com")
    jobs_response = await aggregate_all_jobs(limit=50)
    digest = format_daily_digest(jobs_response.results, min_score=payload.min_score)
    
    # Send using approval-controlled pipeline
    result = await send_application_email_with_approval(
        tracker_id="daily_digest_broadcast",
        recipient_email=recipient,
        subject=digest["subject"],
        body_text=digest["text"],
        approved=True
    )
    return {
        "status": result["status"],
        "recipient": recipient,
        "jobs_included": digest["count"],
        "message": result["message"]
    }

@router.post("/approve-and-send")
async def approve_and_send_application_email(payload: EmailApprovalRequest):
    """
    STRICT APPROVAL GATE:
    Transmits an outreach or application email ONLY when approved is explicitly True.
    """
    if not payload.approved:
        raise HTTPException(
            status_code=400,
            detail="Approval required: Email transmission blocked because approval flag is False."
        )

    try:
        result = await send_application_email_with_approval(
            tracker_id=payload.tracker_id,
            recipient_email=payload.recipient_email,
            subject=payload.subject,
            body_text=payload.body_text,
            approved=payload.approved
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
