import pytest
import asyncio
from app.models.job import JobPosting, ApplicationTrackerItem
from app.storage.tracker_store import TrackerStore
from app.services.email_service import format_daily_digest, send_application_email_with_approval

def test_tracker_crud(tmp_path):
    store = TrackerStore()
    job = JobPosting(
        id="test_job_999",
        title="Full Stack Team Lead",
        company="Alpha Corp",
        location="Lahore, Pakistan",
        salary="PKR 500,000",
        url="https://alphacorp.com/careers/lead",
        source="Jooble"
    )

    item = ApplicationTrackerItem(
        id="app_test_1",
        job=job,
        status="saved"
    )

    # Save
    saved = store.save_or_update(item)
    assert saved.id == "app_test_1"

    # Read
    fetched = store.get_application("app_test_1")
    assert fetched is not None
    assert fetched.job.company == "Alpha Corp"

    # Status update
    updated = store.update_status("app_test_1", "interview")
    assert updated.status == "interview"

    # Cleanup
    store.delete("app_test_1")
    assert store.get_application("app_test_1") is None

def test_daily_digest_format():
    jobs = [
        JobPosting(
            title="Senior React Engineer",
            company="Acme",
            location="Remote",
            salary="$120k",
            url="https://example.com/1",
            source="Remotive",
            match_score=90
        ),
        JobPosting(
            title="Junior QA Intern",
            company="Beta",
            location="Remote",
            salary="Not specified",
            url="https://example.com/2",
            source="Jobicy",
            match_score=40
        )
    ]
    digest = format_daily_digest(jobs, min_score=70)
    assert digest["count"] == 1
    assert "Senior React Engineer" in digest["text"]
    assert "Junior QA Intern" not in digest["text"]

def test_email_approval_gate_rejection():
    # If approved is False, MUST reject with ValueError
    with pytest.raises(ValueError, match="Explicit user approval is required"):
        asyncio.run(send_application_email_with_approval(
            tracker_id="test_track_1",
            recipient_email="recruiter@company.com",
            subject="Test Subject",
            body_text="Test Body",
            approved=False
        ))

def test_email_dry_run_dispatch():
    # If approved is True, without SMTP credentials in test env, safe dry-run simulation occurs
    result = asyncio.run(send_application_email_with_approval(
        tracker_id="test_track_2",
        recipient_email="recruiter@company.com",
        subject="Test Subject",
        body_text="Test Body",
        approved=True
    ))
    assert result["status"] in ["simulated", "sent"]
