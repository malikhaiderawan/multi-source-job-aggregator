import pytest
from app.models.job import JobPosting
from app.services.matching_engine import enrich_job_posting, detect_category

def test_detect_category_mobile():
    cat = detect_category("Senior React Native Developer", "Cross-platform mobile apps for iOS and Android")
    assert cat == "Mobile"

def test_detect_category_frontend():
    cat = detect_category("Next.js / React Frontend Engineer", "Building modern responsive user interfaces with TypeScript")
    assert cat == "Frontend"

def test_detect_category_backend():
    cat = detect_category("Node.js Backend Developer", "Building REST APIs and microservices with Express")
    assert cat == "Backend"

def test_detect_category_fullstack():
    cat = detect_category("Senior Full Stack Engineer", "End-to-end web architecture, databases, cloud")
    assert cat == "Full-stack"

def test_matching_score_senior_role():
    job = JobPosting(
        title="Senior React Native & Node.js Developer",
        company="Global Tech",
        location="Worldwide Remote",
        salary="$90,000 - $120,000",
        url="https://example.com/job1",
        source="Remotive",
        description_snippet="Looking for a Senior Engineer with 5+ years experience in React Native, Node.js, TypeScript, and REST APIs.",
        is_remote=True
    )
    enriched = enrich_job_posting(job)
    assert enriched.match_score >= 80
    assert enriched.seniority_level == "Senior Engineer"
    assert "React Native" in enriched.match_breakdown.matched_skills
    assert "Node.js" in enriched.match_breakdown.matched_skills
    assert enriched.category == "Mobile"

def test_matching_score_lahore_local():
    job = JobPosting(
        title="Technical Lead - Mobile Applications",
        company="Lahore Systems",
        location="Lahore, Pakistan",
        salary="PKR 450,000 / month",
        url="https://example.com/job-lahore",
        source="Jooble",
        description_snippet="Leading our mobile engineering team in Lahore. Flutter, React Native, architecture, code reviews.",
        is_remote=False
    )
    enriched = enrich_job_posting(job)
    assert enriched.match_score >= 80
    assert enriched.seniority_level == "Technical Lead"
    assert "Lahore" in enriched.location
    assert enriched.match_breakdown.location_score == 25

def test_matching_score_intern_role_penalized_for_senior():
    job = JobPosting(
        title="Mobile App Development Intern",
        company="Grupo Island",
        location="Lahore Johar Town",
        salary="Rs 20,000 - Rs 50,000 a month",
        url="https://pk.indeed.com/viewjob?jk=3e81f5077ab92797",
        source="Indeed Alert"
    )
    enriched = enrich_job_posting(job)
    assert enriched.seniority_level == "Internship / Trainee"
    # Anser Nawaz has 6+ years exp, so internship score must be strictly capped
    assert enriched.match_score <= 30
    assert enriched.match_breakdown.seniority_score == 0

def test_matching_score_non_lahore_onsite_location_penalized():
    job = JobPosting(
        title="Backend Developer",
        company="Slicon Systems",
        location="Karachi",
        salary="Rs 70,000 - Rs 100,000 a month",
        url="https://pk.indeed.com/viewjob?jk=e363a7acfd5c1c6e",
        source="Indeed Alert"
    )
    enriched = enrich_job_posting(job)
    assert enriched.location_eligibility == "pakistan_onsite"
    # Karachi on-site is not in commuting distance of Lahore, so location score should not be 25
    assert enriched.match_breakdown.location_score == 6
    assert enriched.match_score <= 60
