import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from app.models.job import JobPosting, ApplicationTrackerItem
from app.models.profile import ANSER_PROFILE
from app.storage.tracker_store import TRACKER_STORE
from app.services.location_classifier import classify_location_eligibility
from app.services.matching_engine import detect_category, calculate_match_score, enrich_job_posting
from app.services.aggregator import aggregate_all_jobs
from app.services.email_service import send_application_email_with_approval

# =========================================================================
# 1. Location Classification Tests (Task B)
# =========================================================================

def test_location_classifier_lahore_onsite_and_hybrid():
    code, detail = classify_location_eligibility("Lahore, Pakistan")
    assert code == "lahore_onsite"
    assert "Lahore" in detail

    code, detail = classify_location_eligibility("Lahore, Pakistan (Hybrid)")
    assert code == "lahore_hybrid"
    assert "Hybrid" in detail

    code, detail = classify_location_eligibility("Gulberg III, Lahore")
    assert code == "lahore_onsite"

    code, detail = classify_location_eligibility("Lahore, Pakistan", snippet="We work on a flexible hybrid schedule")
    assert code == "lahore_hybrid"

def test_location_classifier_pakistan_remote():
    code, detail = classify_location_eligibility("Pakistan (Remote)", is_remote=True)
    assert code == "pakistan_remote"

    code, detail = classify_location_eligibility("Islamabad, Pakistan", is_remote=True)
    assert code == "pakistan_remote"

    code, detail = classify_location_eligibility("Remote / Pakistan")
    assert code == "pakistan_remote"

def test_location_classifier_worldwide_remote():
    code, detail = classify_location_eligibility("Worldwide / Remote", is_remote=True)
    assert code == "worldwide_remote"
    assert "open to global applicants" in detail

    code, detail = classify_location_eligibility("Anywhere in the World", is_remote=True)
    assert code == "worldwide_remote"

    code, detail = classify_location_eligibility("Remote - Worldwide")
    assert code == "worldwide_remote"

    code, detail = classify_location_eligibility("Work from anywhere", is_remote=True)
    assert code == "worldwide_remote"

def test_location_classifier_ineligible_regions():
    code, detail = classify_location_eligibility("USA Only", is_remote=True)
    assert code == "ineligible_region"
    assert "not eligible" in detail.lower()

    code, detail = classify_location_eligibility("US or Canada", is_remote=True)
    assert code == "ineligible_region"

    code, detail = classify_location_eligibility("London, UK", is_remote=False)
    assert code == "ineligible_region"

    code, detail = classify_location_eligibility("Germany (EU Citizens Only)", is_remote=True)
    assert code == "ineligible_region"

    code, detail = classify_location_eligibility("Latin America Only", is_remote=True)
    assert code == "ineligible_region"

def test_location_classifier_unknown():
    code, detail = classify_location_eligibility("Remote", is_remote=True)
    assert code == "eligibility_unknown"
    assert "not explicitly confirmed" in detail.lower() or "unspecified" in detail.lower()

    code, detail = classify_location_eligibility("")
    assert code == "eligibility_unknown"

    code, detail = classify_location_eligibility("Not specified", is_remote=True)
    assert code == "eligibility_unknown"


# =========================================================================
# 2. Category Detection & Profile Match Integrity Tests (Task C)
# =========================================================================

def test_category_detection_mobile_dedicated():
    assert detect_category("Senior React Native Developer") == "Mobile"
    assert detect_category("Flutter Mobile App Engineer") == "Mobile"
    assert detect_category("Lead iOS & Android Developer") == "Mobile"
    assert detect_category("Senior Mobile Architect") == "Mobile"

def test_category_detection_preserves_fullstack_and_backend():
    # Job mentions collaborating with mobile developers, but title is clearly Full Stack
    title = "Senior Full-Stack Engineer"
    text = "You will work with mobile developers on API integration and React Native frontends."
    assert detect_category(title, text) == "Full-stack"

    # Backend job mentions iOS clients
    title = "Senior Backend Engineer (Node.js & FastAPI)"
    text = "Build scalable REST APIs consumed by our web and iOS applications."
    assert detect_category(title, text) == "Backend"

def test_category_detection_frontend():
    assert detect_category("Senior Frontend Developer (React & Next.js)") == "Frontend"
    assert detect_category("Website Developer - React.js") == "Frontend"

def test_match_scoring_for_anser_nawaz():
    job = JobPosting(
        title="Senior Full-Stack Developer",
        company="TechCorp Lahore",
        location="Lahore, Pakistan",
        salary="PKR 450,000 - 650,000",
        url="https://example.com/job/anser-fit",
        description_snippet="Looking for senior developer with React, Node.js, Next.js, PostgreSQL and Docker experience."
    )
    enriched = enrich_job_posting(job, profile=ANSER_PROFILE)
    assert enriched.location_eligibility == "lahore_onsite"
    assert enriched.category == "Full-stack"
    assert enriched.match_score >= 85
    assert enriched.match_breakdown is not None
    assert "React" in enriched.match_breakdown.matched_skills or "Node.js" in enriched.match_breakdown.matched_skills


# =========================================================================
# 3. Dry-Run & Email Dispatch Integrity Tests (Task A)
# =========================================================================

def test_email_dry_run_integrity_preserves_stage_and_flags():
    # Setup test tracker item in saved stage
    test_item = ApplicationTrackerItem(
        id="test_dry_run_integrity_item",
        candidate_id="anser_nawaz",
        job=JobPosting(
            title="Senior React Developer",
            company="Global Soft",
            location="Lahore",
            url="https://example.com/job/test1"
        ),
        status="saved",
        notes="Initial review completed."
    )
    TRACKER_STORE.save_or_update(test_item, expected_candidate_id="anser_nawaz")

    # Ensure SMTP env vars are cleared
    with patch.dict(os.environ, {"SMTP_HOST": "", "SMTP_USER": "", "SMTP_PASS": ""}, clear=False):
        result = asyncio.run(send_application_email_with_approval(
            tracker_id="test_dry_run_integrity_item",
            recipient_email="recruiter@example.com",
            subject="Senior Developer Opportunity - Anser Nawaz",
            body_text="Dear Hiring Team, I am writing to apply...",
            approved=True
        ))

        assert result["status"] == "simulated"
        assert result["email_sent"] is False
        assert "Dry-run logged — not transmitted" in result["message"]

        # Verify persistent item state
        updated = TRACKER_STORE.get_application("test_dry_run_integrity_item")
        assert updated is not None
        assert updated.email_sent is False
        assert updated.recruiter_email_sent is False
        assert updated.email_dispatch_mode == "simulated_dry_run"
        # Application status must NOT be changed to applied
        assert updated.status == "saved"
        assert "[Dry-run logged — not transmitted]" in (updated.notes or "")

def test_email_approval_gate_strictly_enforced():
    with pytest.raises(ValueError, match="Security Gate: Explicit user approval is required"):
        asyncio.run(send_application_email_with_approval(
            tracker_id="test_dry_run_integrity_item",
            recipient_email="recruiter@example.com",
            subject="Test",
            body_text="Body",
            approved=False
        ))

def test_email_live_smtp_dispatch_success():
    test_item = ApplicationTrackerItem(
        id="test_live_smtp_item",
        candidate_id="anser_nawaz",
        job=JobPosting(
            title="Senior Mobile Developer",
            company="Mobile World",
            location="Worldwide Remote",
            url="https://example.com/job/test2"
        ),
        status="saved"
    )
    TRACKER_STORE.save_or_update(test_item, expected_candidate_id="anser_nawaz")

    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_PORT": "587", "SMTP_USER": "u", "SMTP_PASS": "p"}), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = asyncio.run(send_application_email_with_approval(
            tracker_id="test_live_smtp_item",
            recipient_email="recruiter@example.com",
            subject="Senior Mobile Developer - Anser Nawaz",
            body_text="Dear Hiring Manager...",
            approved=True
        ))

        assert result["status"] == "sent"
        assert result["email_sent"] is True
        assert mock_server.starttls.called
        assert mock_server.login.called
        assert mock_server.send_message.called

        updated = TRACKER_STORE.get_application("test_live_smtp_item")
        assert updated is not None
        assert updated.email_sent is True
        assert updated.recruiter_email_sent is True
        assert updated.email_dispatch_mode == "live_smtp"
        assert "[Live recruiter email transmitted" in (updated.notes or "")

def test_email_live_smtp_failure_raises_and_protects_status():
    test_item = ApplicationTrackerItem(
        id="test_smtp_fail_item",
        candidate_id="anser_nawaz",
        job=JobPosting(
            title="Senior Engineer",
            company="Company",
            location="Lahore",
            url="https://example.com/job/fail"
        ),
        status="saved"
    )
    TRACKER_STORE.save_or_update(test_item, expected_candidate_id="anser_nawaz")

    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_PORT": "587", "SMTP_USER": "u", "SMTP_PASS": "p"}), \
         patch("smtplib.SMTP", side_effect=Exception("Connection refused")):
        
        with pytest.raises(RuntimeError, match="SMTP transmission failed"):
            asyncio.run(send_application_email_with_approval(
                tracker_id="test_smtp_fail_item",
                recipient_email="recruiter@example.com",
                subject="Test",
                body_text="Body",
                approved=True
            ))

        updated = TRACKER_STORE.get_application("test_smtp_fail_item")
        assert updated is not None
        assert updated.email_sent is False
        assert updated.recruiter_email_sent is False


# =========================================================================
# 4. Aggregator Location & Eligibility Filtering Tests (Tasks B & C)
# =========================================================================

def test_aggregator_location_and_eligibility_filtering():
    sample_jobs = [
        JobPosting(
            id="job_lhr_onsite",
            title="Senior Flutter Developer",
            company="Lahore AppStudio",
            location="Lahore, Pakistan",
            url="https://example.com/lhr1"
        ),
        JobPosting(
            id="job_lhr_hybrid",
            title="Senior React Native Developer",
            company="Fintech Lahore",
            location="Lahore, Pakistan (Hybrid)",
            url="https://example.com/lhr2"
        ),
        JobPosting(
            id="job_pak_remote",
            title="Senior Full-Stack Engineer",
            company="RemotePk",
            location="Pakistan (Remote)",
            is_remote=True,
            url="https://example.com/pak1"
        ),
        JobPosting(
            id="job_worldwide",
            title="Senior Node.js Developer",
            company="GlobalScale",
            location="Worldwide / Remote",
            is_remote=True,
            url="https://example.com/ww1"
        ),
        JobPosting(
            id="job_us_only",
            title="Lead iOS Engineer",
            company="USCorp",
            location="USA Only",
            is_remote=True,
            url="https://example.com/us1"
        ),
        JobPosting(
            id="job_unknown_remote",
            title="Senior Python Engineer",
            company="VagueTech",
            location="Remote",
            is_remote=True,
            url="https://example.com/vague1"
        )
    ]

    with patch("app.services.aggregator.fetch_remotive_jobs", return_value=[]), \
         patch("app.services.aggregator.fetch_jobicy_jobs", return_value=[]), \
         patch("app.services.aggregator.fetch_arbeitnow_jobs", return_value=[]), \
         patch("app.services.aggregator.fetch_wwr_jobs", return_value=[]), \
         patch("app.services.aggregator.fetch_mustakbil_jobs", return_value=[]), \
         patch("app.services.aggregator.LINKEDIN_JOB_STORE.get_all_jobs", return_value=[]), \
         patch("app.services.aggregator.fetch_jooble_jobs", return_value=sample_jobs):

        # 1. Searching for "Lahore":
        # Must return lahore_onsite, lahore_hybrid, pakistan_remote
        # Must EXCLUDE job_us_only and job_unknown_remote
        lhr_res = asyncio.run(aggregate_all_jobs(location="Lahore"))
        returned_ids = [j.id for j in lhr_res.results]
        assert "job_lhr_onsite" in returned_ids
        assert "job_lhr_hybrid" in returned_ids
        assert "job_pak_remote" in returned_ids
        assert "job_us_only" not in returned_ids
        assert "job_unknown_remote" not in returned_ids

        # 2. Filtering by eligibility "lahore_local"
        local_res = asyncio.run(aggregate_all_jobs(eligibility="lahore_local"))
        local_ids = [j.id for j in local_res.results]
        assert "job_lhr_onsite" in local_ids
        assert "job_lhr_hybrid" in local_ids
        assert "job_pak_remote" not in local_ids
        assert "job_worldwide" not in local_ids

        # 3. Filtering by eligibility "worldwide_remote"
        ww_res = asyncio.run(aggregate_all_jobs(eligibility="worldwide_remote"))
        ww_ids = [j.id for j in ww_res.results]
        assert "job_worldwide" in ww_ids
        assert "job_us_only" not in ww_ids
        assert "job_lhr_onsite" not in ww_ids

        # 4. Check eligibility_count breakdown
        all_res = asyncio.run(aggregate_all_jobs())
        assert all_res.eligibility_count.get("lahore_onsite") == 1
        assert all_res.eligibility_count.get("lahore_hybrid") == 1
        assert all_res.eligibility_count.get("pakistan_remote") == 1
        assert all_res.eligibility_count.get("worldwide_remote") == 1
        assert all_res.eligibility_count.get("ineligible_region") == 1
        assert all_res.eligibility_count.get("eligibility_unknown") == 1
