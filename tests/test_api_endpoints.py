import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["candidate"] == "Anser Nawaz"

def test_jobs_endpoint():
    res = client.get("/api/v1/jobs?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "total_count" in data
    assert len(data["results"]) <= 5

def test_tracker_flow_and_approval():
    test_job = {
        "id": "job_integration_test_101",
        "title": "Senior React Native Engineer",
        "company": "Tech Global",
        "location": "Lahore, Pakistan",
        "salary": "PKR 550,000",
        "url": "https://example.com/job/test101",
        "source": "Jooble",
        "category": "Mobile",
        "seniority_level": "Senior Engineer",
        "match_score": 92
    }

    # 1. Track job
    track_payload = {
        "id": "track_test_101",
        "job": test_job,
        "status": "pending_approval"
    }
    create_res = client.post("/api/v1/tracker", json=track_payload)
    assert create_res.status_code == 200
    assert create_res.json()["status"] == "pending_approval"

    # 2. Get list
    list_res = client.get("/api/v1/tracker?status=pending_approval")
    assert list_res.status_code == 200
    assert any(item["id"] == "track_test_101" for item in list_res.json())

    # 3. Update status
    patch_res = client.patch("/api/v1/tracker/track_test_101/status", json={"status": "interview"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "interview"

    # 4. Generate tailored application
    gen_res = client.post("/api/v1/generate/application", json={"job": test_job})
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["candidate_name"] == "Anser Nawaz"
    assert "Tech Global" in gen_data["cover_letter"]
    assert len(gen_data["tailored_cv_bullet_points"]) >= 3

    # 5. Test Email Approval Gate: Unapproved must fail with 400
    unapproved_res = client.post("/api/v1/email/approve-and-send", json={
        "tracker_id": "track_test_101",
        "recipient_email": "recruiter@techglobal.com",
        "subject": "Application: Senior React Native Engineer - Anser Nawaz",
        "body_text": gen_data["recruiter_email"],
        "approved": False
    })
    assert unapproved_res.status_code == 400
    assert "approval required" in unapproved_res.json()["detail"].lower()

    # 6. Test Email Approval Gate: Approved must succeed
    approved_res = client.post("/api/v1/email/approve-and-send", json={
        "tracker_id": "track_test_101",
        "recipient_email": "recruiter@techglobal.com",
        "subject": "Application: Senior React Native Engineer - Anser Nawaz",
        "body_text": gen_data["recruiter_email"],
        "approved": True
    })
    assert approved_res.status_code == 200
    assert approved_res.json()["status"] in ["simulated", "sent"]

    # 7. Delete cleanup
    del_res = client.delete("/api/v1/tracker/track_test_101")
    assert del_res.status_code == 200
