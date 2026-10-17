import os
import asyncio
import email
from email.message import EmailMessage
import pytest
from unittest.mock import patch, MagicMock
from app.models.job import JobPosting
from app.models.profile import ANSER_PROFILE
from app.storage.linkedin_job_store import LinkedInJobStore
from app.clients.linkedin_email_client import (
    is_trusted_linkedin_sender,
    is_trusted_indeed_sender,
    is_trusted_alert_sender,
    extract_jobs_from_html,
    extract_jobs_from_text,
    extract_indeed_jobs_from_html,
    extract_indeed_jobs_from_text,
    parse_email_message,
    sync_linkedin_alert_emails
)
from app.clients.mustakbil_client import fetch_mustakbil_jobs
from app.services.matching_engine import enrich_job_posting

# =========================================================================
# 1. Valid Email Parsing Tests (HTML & Plain Text)
# =========================================================================

def test_parse_valid_linkedin_html_email():
    html_content = """
    <html>
    <body>
        <div class="job-card">
            <a href="https://www.linkedin.com/comm/jobs/view/4112233445?trackingId=abc&refId=123">
                Senior Full-Stack Engineer (React & Node.js)
            </a>
            <div class="meta">
                <span>Arbisoft</span> · <span>Lahore, Punjab, Pakistan (Hybrid)</span>
            </div>
        </div>
        <div class="job-card">
            <a href="https://www.linkedin.com/comm/jobs/view/4223344556?trackingId=def">
                Senior Flutter Developer
            </a>
            <div>
                <span>TechLogix</span> · <span>Lahore, Pakistan</span>
            </div>
        </div>
        <div class="footer">
            <a href="https://www.linkedin.com/e/unsubscribe/xyz">Unsubscribe</a>
            <a href="https://www.linkedin.com/comm/jobs/settings">Manage alerts</a>
        </div>
    </body>
    </html>
    """
    msg = EmailMessage()
    msg["From"] = "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>"
    msg["To"] = "ansernawaz786@gmail.com"
    msg["Subject"] = "30+ new jobs for 'Full Stack Engineer' in Lahore"
    msg["Date"] = "Wed, 15 Oct 2026 10:00:00 +0500"
    msg.set_content("Please enable HTML to view jobs.")
    msg.add_alternative(html_content, subtype="html")

    is_valid, jobs, reason = parse_email_message(msg)

    assert is_valid is True
    assert len(jobs) == 2

    # Job 1 validation
    j1 = jobs[0]
    assert j1["job_id"] == "4112233445"
    assert j1["title"] == "Senior Full-Stack Engineer (React & Node.js)"
    assert j1["company"] == "Arbisoft"
    assert "Lahore" in j1["location"]
    assert j1["url"] == "https://www.linkedin.com/jobs/view/4112233445"

    # Job 2 validation
    j2 = jobs[1]
    assert j2["job_id"] == "4223344556"
    assert j2["title"] == "Senior Flutter Developer"
    assert j2["company"] == "TechLogix"
    assert "Lahore" in j2["location"]
    assert j2["url"] == "https://www.linkedin.com/jobs/view/4223344556"

def test_parse_valid_linkedin_plaintext_email():
    plain_content = """
    New jobs matching your search criteria:

    Senior React Native Developer
    Devsinc · Lahore, Pakistan (On-site)
    View job: https://www.linkedin.com/comm/jobs/view/4334455667?trackingId=ghi

    Lead Software Engineer
    Systems Limited · Worldwide / Remote
    View job: https://www.linkedin.com/jobs/view/4445566778?ref=email

    Manage alerts: https://www.linkedin.com/e/unsubscribe/123
    """
    msg = EmailMessage()
    msg["From"] = "LinkedIn Notifications <jobs-noreply@linkedin.com>"
    msg["To"] = "ansernawaz786@gmail.com"
    msg["Subject"] = "New jobs for Senior Mobile Developer"
    msg["Date"] = "Wed, 15 Oct 2026 12:00:00 +0500"
    msg.set_content(plain_content)

    is_valid, jobs, reason = parse_email_message(msg)

    assert is_valid is True
    assert len(jobs) == 2

    assert jobs[0]["job_id"] == "4334455667"
    assert jobs[0]["title"] == "Senior React Native Developer"
    assert jobs[0]["company"] == "Devsinc"
    assert "Lahore" in jobs[0]["location"]

    assert jobs[1]["job_id"] == "4445566778"
    assert jobs[1]["title"] == "Lead Software Engineer"
    assert jobs[1]["company"] == "Systems Limited"
    assert "Worldwide" in jobs[1]["location"]


# =========================================================================
# 2. Untrusted Sender & Security Tests
# =========================================================================

def test_reject_untrusted_sender():
    msg = EmailMessage()
    msg["From"] = "Scam Recruiter <phishing@untrusted-domain.com>"
    msg["To"] = "ansernawaz786@gmail.com"
    msg["Subject"] = "Job alert: Fake Software Engineer"
    msg.set_content("Check this job: https://www.linkedin.com/jobs/view/9999999999")

    is_valid, jobs, reason = parse_email_message(msg)
    assert is_valid is False
    assert len(jobs) == 0
    assert "Rejected untrusted sender" in reason

def test_trusted_linkedin_domains_validation():
    assert is_trusted_linkedin_sender("jobalerts-noreply@linkedin.com") is True
    assert is_trusted_linkedin_sender("alerts@e.linkedin.com") is True
    assert is_trusted_linkedin_sender("notifications@sub.linkedin.com") is True
    assert is_trusted_linkedin_sender("spoofed@linkedin.com.attacker.org") is False
    assert is_trusted_linkedin_sender("fake@notlinkedin.com") is False
    assert is_trusted_linkedin_sender("") is False


# =========================================================================
# 3. Duplicate Handling Tests
# =========================================================================

def test_duplicate_handling_in_store(tmp_path):
    store_file = os.path.join(tmp_path, "test_linkedin_store.json")
    store = LinkedInJobStore(filepath=store_file)

    job1 = JobPosting(
        id="linkedin_111",
        title="Senior React Native Developer",
        company="Company A",
        location="Lahore",
        url="https://www.linkedin.com/jobs/view/111"
    )
    job2 = JobPosting(
        id="linkedin_222",
        title="Senior Node Engineer",
        company="Company B",
        location="Lahore",
        url="https://www.linkedin.com/jobs/view/222"
    )

    # First save: 2 new jobs
    added, dups = store.save_jobs([job1, job2])
    assert added == 2
    assert dups == 0
    assert len(store.get_all_jobs()) == 2

    # Second save with 1 existing and 1 new job: 1 added, 1 duplicate skipped
    job3 = JobPosting(
        id="linkedin_333",
        title="Flutter Engineer",
        company="Company C",
        location="Lahore",
        url="https://www.linkedin.com/jobs/view/333"
    )
    added, dups = store.save_jobs([job1, job3])
    assert added == 1
    assert dups == 1
    assert len(store.get_all_jobs()) == 3


# =========================================================================
# 4. Missing Credentials & Connection Failure Tests
# =========================================================================

def test_missing_credentials_graceful_response():
    with patch.dict(os.environ, {"LINKEDIN_ALERT_EMAIL_USER": "", "LINKEDIN_ALERT_EMAIL_PASS": ""}, clear=False):
        res = asyncio.run(sync_linkedin_alert_emails(max_emails=10))
        assert res.status == "missing_credentials"
        assert "Mailbox credentials not configured" in res.message
        assert res.jobs_extracted == 0
        assert res.unique_jobs_added == 0

def test_imap_connection_failure_safe_handling():
    with patch.dict(os.environ, {
        "LINKEDIN_ALERT_EMAIL_USER": "test@gmail.com",
        "LINKEDIN_ALERT_EMAIL_PASS": "pass123",
        "LINKEDIN_ALERT_IMAP_SERVER": "imap.test.com",
        "LINKEDIN_ALERT_IMAP_PORT": "993"
    }):
        with patch("imaplib.IMAP4_SSL", side_effect=Exception("IMAP authentication failed")):
            res = asyncio.run(sync_linkedin_alert_emails(max_emails=10))
            assert res.status == "error"
            assert "IMAP connection error" in res.message
            assert res.failures == 1
            assert res.unique_jobs_added == 0


# =========================================================================
# 5. Location Classification & Candidate Matching on LinkedIn Postings
# =========================================================================

def test_location_and_candidate_matching_on_linkedin_jobs():
    # 1. Lahore Hybrid Mobile Job
    job_lhr = JobPosting(
        id="linkedin_555",
        title="Senior Flutter & React Native Developer",
        company="Lahore Mobile Labs",
        location="Lahore, Punjab, Pakistan (Hybrid)",
        url="https://www.linkedin.com/jobs/view/555"
    )
    enriched_lhr = enrich_job_posting(job_lhr, profile=ANSER_PROFILE)
    assert enriched_lhr.location_eligibility == "lahore_hybrid"
    assert enriched_lhr.category == "Mobile"
    assert enriched_lhr.match_score >= 80
    assert enriched_lhr.application_status == "untracked"

    # 2. Pakistan Remote Full-Stack Job
    job_rem = JobPosting(
        id="linkedin_666",
        title="Senior Full-Stack Developer (Next.js & Node.js)",
        company="Global Software",
        location="Pakistan (Remote)",
        is_remote=True,
        url="https://www.linkedin.com/jobs/view/666"
    )
    enriched_rem = enrich_job_posting(job_rem, profile=ANSER_PROFILE)
    assert enriched_rem.location_eligibility == "pakistan_remote"
    assert enriched_rem.category == "Full-stack"
    assert enriched_rem.match_score >= 80
    assert enriched_rem.application_status == "untracked"


# =========================================================================
# 6. Indeed Pakistan Job Alert & Local Portal Tests
# =========================================================================

def test_parse_valid_indeed_html_email():
    html_content = """
    <html>
    <body>
        <a href="https://pk.indeed.com/rc/clk/dl?jk=e363a7acfd5c1c6e&from=ja" class="strong-text-link">
            Senior Backend Engineer
        </a>
        <div>
            <p>Slicon Systems</p>
            <p>Lahore</p>
            <p>Rs 150,000 - Rs 250,000 a month</p>
        </div>
        <a href="https://pk.indeed.com/rc/clk/dl?jk=49ad34ce4fc6c6df&from=ja" class="strong-text-link">
            Senior React Native Developer
        </a>
        <div>
            <p>Virtuosoft</p>
            <p>Lahore (Hybrid)</p>
        </div>
        <a href="https://www.indeed.com/account/alerts">Manage alerts</a>
    </body>
    </html>
    """
    msg = EmailMessage()
    msg["From"] = "Indeed Job Alert <donotreply@jobalert.indeed.com>"
    msg["To"] = "ansernawaz786@gmail.com"
    msg["Subject"] = "10 new jobs for React Native in Lahore"
    msg["Date"] = "Wed, 15 Oct 2026 10:00:00 +0500"
    msg.add_alternative(html_content, subtype="html")

    is_valid, jobs, reason = parse_email_message(msg)

    assert is_valid is True
    assert len(jobs) == 2

    # Job 1 validation
    j1 = jobs[0]
    assert j1["job_id"] == "e363a7acfd5c1c6e"
    assert j1["title"] == "Senior Backend Engineer"
    assert j1["company"] == "Slicon Systems"
    assert "Lahore" in j1["location"]
    assert "150,000" in j1["salary"]
    assert j1["url"] == "https://pk.indeed.com/viewjob?jk=e363a7acfd5c1c6e"
    assert j1["source"] == "Indeed Alert"

    # Job 2 validation
    j2 = jobs[1]
    assert j2["job_id"] == "49ad34ce4fc6c6df"
    assert j2["title"] == "Senior React Native Developer"
    assert j2["company"] == "Virtuosoft"
    assert "Lahore" in j2["location"]
    assert j2["url"] == "https://pk.indeed.com/viewjob?jk=49ad34ce4fc6c6df"
    assert j2["source"] == "Indeed Alert"


def test_parse_valid_indeed_plaintext_email():
    plain_content = """
    Indeed Job Alert
    2 new jobs matching your search:

    Full-Stack Engineer
    Systems Limited - Lahore
    Rs 200,000 a month
    https://pk.indeed.com/rc/clk/dl?jk=34ce7c6270badced&from=ja

    Mobile App Developer
    TechLogix - Lahore
    https://pk.indeed.com/rc/clk/dl?jk=eaec2ec9efd32dac&from=ja
    """
    msg = EmailMessage()
    msg["From"] = "Indeed <alert@indeed.com>"
    msg["To"] = "ansernawaz786@gmail.com"
    msg["Subject"] = "New jobs matching your search"
    msg["Date"] = "Wed, 15 Oct 2026 12:00:00 +0500"
    msg.set_content(plain_content)

    is_valid, jobs, reason = parse_email_message(msg)

    assert is_valid is True
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Full-Stack Engineer"
    assert jobs[0]["company"] == "Systems Limited"
    assert "Lahore" in jobs[0]["location"]
    assert "200,000" in jobs[0]["salary"]
    assert jobs[0]["source"] == "Indeed Alert"


def test_trusted_indeed_domains_validation():
    assert is_trusted_indeed_sender("donotreply@jobalert.indeed.com") is True
    assert is_trusted_indeed_sender("alert@indeed.com") is True
    assert is_trusted_indeed_sender("messages@indeedemail.com") is True
    assert is_trusted_indeed_sender("attacker@spoofed.indeed.com.evil.com") is False
    assert is_trusted_indeed_sender("hacker@notindeed.com") is False
    assert is_trusted_indeed_sender("") is False


@pytest.mark.anyio
async def test_mustakbil_client_parsing():
    from unittest.mock import AsyncMock
    mock_html = """
    <div class="job-card">
        <a class="jc-title__link" aria-label="Senior React Native Developer at Devsinc in Lahore" href="/jobs/job/12345">
            Senior React Native Developer
        </a>
    </div>
    <div class="job-card">
        <a class="jc-title__link" aria-label="Lead Full Stack Engineer at Arbisoft in Lahore, Pakistan" href="/jobs/job/67890">
            Lead Full Stack Engineer
        </a>
    </div>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    jobs = await fetch_mustakbil_jobs(mock_client, location="Lahore", fetch_depth=10)
    assert len(jobs) == 2
    assert jobs[0].id == "mustakbil_12345"
    assert jobs[0].title == "Senior React Native Developer"
    assert jobs[0].company == "Devsinc"
    assert "Lahore" in jobs[0].location
    assert jobs[0].source == "Mustakbil (Pakistan)"
    assert jobs[0].country == "Pakistan"

    assert jobs[1].id == "mustakbil_67890"
    assert jobs[1].title == "Lead Full Stack Engineer"
    assert jobs[1].company == "Arbisoft"
    assert "Lahore" in jobs[1].location

