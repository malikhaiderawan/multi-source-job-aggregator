from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MatchScoreBreakdown(BaseModel):
    skills_score: int = Field(default=0, description="Score based on matched technical skills (0-40)")
    seniority_score: int = Field(default=0, description="Score based on 6+ years experience & senior title (0-25)")
    location_score: int = Field(default=0, description="Score based on Lahore, Pakistan, or international remote (0-25)")
    salary_score: int = Field(default=0, description="Bonus score for disclosed competitive salary (0-10)")
    total_score: int = Field(default=0, description="Aggregated score (0-100)")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class JobPosting(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique job identifier")
    title: str
    company: str
    location: str
    salary: str = "Not specified"
    url: str
    source: str = "Unknown"
    posted_date: Optional[str] = Field(default=None, description="ISO or human formatted date")
    description_snippet: Optional[str] = Field(default="", description="Key snippet or requirements")
    category: Optional[str] = Field(default="Full-stack", description="Mobile, Frontend, Backend, or Full-stack")
    is_remote: bool = Field(default=False, description="Whether the job is remote")
    country: Optional[str] = Field(default=None, description="Country or region")
    seniority_level: Optional[str] = Field(default="Senior", description="Senior, Lead, Mid, etc.")
    tags: List[str] = Field(default_factory=list)
    match_score: int = Field(default=0, description="Match percentage against candidate profile (0-100)")
    match_breakdown: Optional[MatchScoreBreakdown] = None
    application_status: Optional[str] = Field(default="untracked", description="saved, pending_approval, applied, interview, rejected, follow_up, untracked")
    location_eligibility: str = Field(default="eligibility_unknown", description="lahore_onsite, lahore_hybrid, pakistan_remote, worldwide_remote, ineligible_region, eligibility_unknown")
    eligibility_detail: Optional[str] = Field(default="", description="Factual explanation and evidence for regional eligibility")
    original_location: Optional[str] = Field(default=None, description="Original raw location string from provider")
    contact_email: Optional[str] = Field(default=None, description="Extracted recruiter or application contact email")

class JobListResponse(BaseModel):
    total_count: int
    count: int
    results: List[JobPosting]
    categories_count: Dict[str, int] = Field(default_factory=dict)
    providers_count: Dict[str, int] = Field(default_factory=dict)
    eligibility_count: Dict[str, int] = Field(default_factory=dict)
    query_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ApplicationTrackerItem(BaseModel):
    id: str
    candidate_id: str = Field(default="anser_nawaz", description="Stable identifier of the candidate owner")
    job: JobPosting
    status: str = Field(default="saved", description="saved, pending_approval, applied, interview, rejected, follow_up")
    notes: Optional[str] = ""
    tailored_cv_bullet_points: List[str] = Field(default_factory=list)
    tailored_cover_letter: Optional[str] = ""
    tailored_recruiter_email: Optional[str] = ""
    email_recipient: Optional[str] = ""
    email_approved: bool = False
    email_sent: bool = False
    email_dispatch_mode: Optional[str] = Field(default="none", description="none, simulated_dry_run, live_smtp")
    recruiter_email_sent: bool = Field(default=False, description="Whether recruiter outreach email was genuinely transmitted via live SMTP")
    official_application_submitted: bool = Field(default=False, description="Whether the official application was submitted on the company careers portal")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ApplicationGenerateRequest(BaseModel):
    job: JobPosting
    custom_tone: Optional[str] = "professional"  # professional, confident, technical

class ApplicationGenerateResponse(BaseModel):
    job_id: str
    candidate_name: str
    tailored_cv_bullet_points: List[str]
    cover_letter: str
    recruiter_email: str
    key_selling_points: List[str]
    suggested_recipient_email: Optional[str] = None

class EmailApprovalRequest(BaseModel):
    tracker_id: str
    recipient_email: str
    subject: str
    body_text: str
    approved: bool = True

class LinkedInSyncResponse(BaseModel):
    status: str = Field(description="success, missing_credentials, or error")
    message: str = Field(description="User-facing summary message")
    emails_scanned: int = 0
    jobs_extracted: int = 0
    unique_jobs_added: int = 0
    duplicates_skipped: int = 0
    failures: int = 0
    eligibility_count: Dict[str, int] = Field(default_factory=dict)
    jobs: List[JobPosting] = Field(default_factory=list)

