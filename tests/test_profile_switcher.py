import pytest
from app.storage.profile_store import ProfileStore
from app.services.matching_engine import calculate_match_score, detect_category
from app.models.job import JobPosting
from app.services.tailored_generator import generate_tailored_application

def test_profile_store_switching():
    store = ProfileStore()
    profiles = store.list_profiles()
    assert len(profiles) >= 2
    
    # Switch to Haider Nawaz
    activated = store.set_active_profile("haider_nawaz")
    assert activated["id"] == "haider_nawaz"
    assert activated["is_active"] is True

    active = store.get_active_profile()
    assert active.name == "Haider Nawaz"
    assert "Python" in active.all_skills

    # Switch back to Anser Nawaz
    store.set_active_profile("anser_nawaz")
    active_back = store.get_active_profile()
    assert active_back.name == "Anser Nawaz"
    assert "Flutter" in active_back.all_skills

def test_matching_engine_changes_with_profile():
    store = ProfileStore()
    
    job_python = JobPosting(
        title="Senior Python & FastAPI Engineer",
        company="PyCloud",
        location="Worldwide Remote",
        salary="$100k",
        url="https://example.com/py1",
        source="Remotive",
        description_snippet="Looking for Python, FastAPI, Docker, and PostgreSQL developer.",
        is_remote=True
    )

    # When Haider is active
    store.set_active_profile("haider_nawaz")
    score_haider = calculate_match_score(job_python)
    assert "Python" in score_haider.matched_skills
    assert "FastAPI" in score_haider.matched_skills

    # Generator test with Haider
    app_haider = generate_tailored_application(job_python)
    assert app_haider.candidate_name == "Haider Nawaz"
    assert "Haider Nawaz" in app_haider.cover_letter

    # Reset back to Anser Nawaz default
    store.set_active_profile("anser_nawaz")
    app_anser = generate_tailored_application(job_python)
    assert app_anser.candidate_name == "Anser Nawaz"
