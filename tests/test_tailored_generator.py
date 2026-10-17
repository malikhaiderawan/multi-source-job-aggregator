import pytest
from app.models.job import JobPosting
from app.services.matching_engine import enrich_job_posting
from app.services.tailored_generator import generate_tailored_application
from app.models.profile import ANSER_PROFILE

def test_generate_tailored_application_without_hallucinating():
    job = JobPosting(
        title="Senior React Native Developer",
        company="Fintech Stream",
        location="Worldwide Remote",
        salary="$110k",
        url="https://example.com/job-mobile",
        source="Remotive",
        description_snippet="Seeking Senior React Native Engineer with Node.js and Redux experience.",
        is_remote=True
    )
    enriched = enrich_job_posting(job)
    response = generate_tailored_application(enriched)

    assert response.candidate_name == "Anser Nawaz"
    assert len(response.tailored_cv_bullet_points) >= 3

    # Ensure verified companies and projects are referenced
    cover_letter = response.cover_letter
    assert "Coder Crew" in cover_letter or "ASOFT" in cover_letter or "AfroTech Connect" in cover_letter
    assert "Anser Nawaz" in cover_letter
    assert ANSER_PROFILE.email in cover_letter
    assert "Fintech Stream" in cover_letter

    # Ensure recruiter outreach email is personalized
    email_text = response.recruiter_email
    assert "Fintech Stream" in email_text
    assert "6+ years" in email_text
    assert "Senior React Native Developer" in email_text
