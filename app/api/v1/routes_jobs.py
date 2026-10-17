from typing import Optional
from fastapi import APIRouter, Query
from app.models.job import JobListResponse, LinkedInSyncResponse
from app.services.aggregator import aggregate_all_jobs
from app.clients.linkedin_email_client import sync_linkedin_alert_emails

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.get("", response_model=JobListResponse)
async def get_jobs(
    keyword: str = Query("", description="Job title, skill, or technology"),
    location: str = Query("", description="Lahore, Pakistan, or Remote"),
    category: str = Query("All", description="Mobile, Frontend, Backend, Full-stack, or All"),
    eligibility: Optional[str] = Query(None, description="lahore_local, pakistan_all, worldwide_remote, remote_eligible, eligibility_unknown, or all"),
    min_score: int = Query(0, ge=0, le=100, description="Minimum match percentage (0-100)"),
    limit: int = Query(100, ge=1, le=500, description="Max results to return"),
    candidate_id: Optional[str] = Query(None, description="Optional candidate profile ID; defaults to active candidate")
):
    """
    Fetches real-time tech jobs aggregated across Remotive, Jobicy, Arbeitnow,
    WeWorkRemotely RSS, Jooble, and synced LinkedIn Job Alerts, scored against the selected candidate profile.
    """
    return await aggregate_all_jobs(
        keyword=keyword,
        location=location,
        category=category,
        eligibility=eligibility,
        min_score=min_score,
        limit=limit,
        candidate_id=candidate_id
    )

@router.post("/sync-linkedin-alerts", response_model=LinkedInSyncResponse)
async def sync_linkedin_alerts(
    max_emails: int = Query(25, ge=1, le=100, description="Max emails to scan"),
    candidate_id: Optional[str] = Query(None, description="Candidate ID to score against")
):
    """
    Connects to the user's configured mailbox via secure IMAP/TLS, safely fetches
    LinkedIn Job Alert emails, extracts real job postings, enriches them against
    the active candidate profile, and saves new postings.
    """
    return await sync_linkedin_alert_emails(max_emails=max_emails, candidate_id=candidate_id)

