import pytest
from app.models.job import JobPosting
from app.services.deduplicator import deduplicate_jobs, clean_url

def test_clean_url():
    raw_url = "https://example.com/job/123?utm_source=linkedin&utm_medium=cpc&ref=aggregator"
    cleaned = clean_url(raw_url)
    assert cleaned == "https://example.com/job/123"

def test_deduplicate_exact_url():
    job1 = JobPosting(
        title="Senior Full Stack Engineer",
        company="Acme Corp",
        location="Remote",
        salary="Not specified",
        url="https://example.com/jobs/senior-fullstack?utm_source=feed",
        source="Remotive"
    )
    job2 = JobPosting(
        title="Senior Full Stack Engineer",
        company="Acme Corp",
        location="Remote",
        salary="$120k",
        url="https://example.com/jobs/senior-fullstack?ref=partner",
        source="Jobicy"
    )
    deduped = deduplicate_jobs([job1, job2])
    assert len(deduped) == 1

def test_deduplicate_title_and_company():
    job1 = JobPosting(
        title="Lead Mobile App Developer",
        company="Tech Innovations",
        location="Worldwide",
        salary="Not specified",
        url="https://source1.com/post/1",
        source="Arbeitnow"
    )
    job2 = JobPosting(
        title="Lead Mobile App Developer",
        company="Tech Innovations",
        location="Worldwide",
        salary="$100k - $130k",
        url="https://source2.com/different/url/2",
        source="WeWorkRemotely"
    )
    deduped = deduplicate_jobs([job1, job2])
    assert len(deduped) == 1
    # Preserves posting with disclosed salary
    assert deduped[0].salary == "$100k - $130k"
