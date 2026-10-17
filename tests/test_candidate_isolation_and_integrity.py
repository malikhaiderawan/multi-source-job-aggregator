import os
import glob
import json
import pytest
import threading
from fastapi.testclient import TestClient
from main import app
from app.models.job import JobPosting, ApplicationTrackerItem
from app.storage.tracker_store import TrackerStore, LEGACY_UNASSIGNED_ID
from app.storage.profile_store import ProfileStore, validate_profile_inputs
from app.storage.file_utils import atomic_write_json, file_lock

client = TestClient(app)

def test_tracker_candidate_isolation(tmp_path):
    """Proves Candidate A and Candidate B see only their own tracker items."""
    test_file = str(tmp_path / "tracker_test.json")
    store = TrackerStore(filepath=test_file)

    job1 = JobPosting(
        id="job_iso_1",
        title="React Native Developer",
        company="Company A",
        location="Lahore",
        salary="PKR 400k",
        url="https://example.com/1",
        source="Jooble"
    )

    item_a = ApplicationTrackerItem(
        id="track_cand_a_job1",
        candidate_id="cand_a",
        job=job1,
        status="saved",
        notes="Candidate A private notes"
    )

    item_b = ApplicationTrackerItem(
        id="track_cand_b_job2",
        candidate_id="cand_b",
        job=job1,
        status="interview",
        notes="Candidate B private notes"
    )

    store.save_or_update(item_a, expected_candidate_id="cand_a")
    store.save_or_update(item_b, expected_candidate_id="cand_b")

    # Candidate A only sees Candidate A's items
    cand_a_apps = store.list_applications(candidate_id="cand_a")
    assert len(cand_a_apps) == 1
    assert cand_a_apps[0].id == "track_cand_a_job1"
    assert cand_a_apps[0].notes == "Candidate A private notes"

    # Candidate B only sees Candidate B's items
    cand_b_apps = store.list_applications(candidate_id="cand_b")
    assert len(cand_b_apps) == 1
    assert cand_b_apps[0].id == "track_cand_b_job2"
    assert cand_b_apps[0].status == "interview"

def test_independent_tracking_of_same_job(tmp_path):
    """Proves two candidates can independently track the exact same job without overwriting."""
    test_file = str(tmp_path / "tracker_shared_job.json")
    store = TrackerStore(filepath=test_file)

    same_job = JobPosting(
        id="shared_job_555",
        title="Full Stack Tech Lead",
        company="Innovatech",
        location="Remote",
        salary="$130k",
        url="https://innovatech.com/jobs/555",
        source="Remotive"
    )

    item_a = ApplicationTrackerItem(
        id="track_user1_shared_job_555",
        candidate_id="user1",
        job=same_job,
        status="applied"
    )
    item_b = ApplicationTrackerItem(
        id="track_user2_shared_job_555",
        candidate_id="user2",
        job=same_job,
        status="saved"
    )

    store.save_or_update(item_a)
    store.save_or_update(item_b)

    # Verify both exist independently
    app_a = store.get_application("track_user1_shared_job_555", candidate_id="user1")
    app_b = store.get_application("track_user2_shared_job_555", candidate_id="user2")

    assert app_a is not None and app_a.status == "applied"
    assert app_b is not None and app_b.status == "saved"

    # Candidate A updating status does NOT affect candidate B
    store.update_status("track_user1_shared_job_555", "interview", candidate_id="user1")
    assert store.get_application("track_user1_shared_job_555", candidate_id="user1").status == "interview"
    assert store.get_application("track_user2_shared_job_555", candidate_id="user2").status == "saved"

def test_cross_candidate_access_rejection(tmp_path):
    """Proves cross-candidate access returns non-disclosing None/404 or rejects."""
    test_file = str(tmp_path / "tracker_security.json")
    store = TrackerStore(filepath=test_file)

    job = JobPosting(
        id="job_sec_1",
        title="Backend Engineer",
        company="SecureTech",
        location="Lahore",
        salary="PKR 450k",
        url="https://securetech.com/1",
        source="Jobicy"
    )
    item_alice = ApplicationTrackerItem(
        id="track_alice_1",
        candidate_id="alice",
        job=job,
        status="saved"
    )
    store.save_or_update(item_alice)

    # Bob attempts to read Alice's application -> returns None (non-disclosing)
    bob_view = store.get_application("track_alice_1", candidate_id="bob")
    assert bob_view is None

    # Bob attempts to update Alice's application status -> returns None
    bob_update = store.update_status("track_alice_1", "rejected", candidate_id="bob")
    assert bob_update is None
    # Verify status unchanged
    assert store.get_application("track_alice_1", candidate_id="alice").status == "saved"

    # Bob attempts to delete Alice's application -> returns False
    bob_delete = store.delete("track_alice_1", candidate_id="bob")
    assert bob_delete is False
    assert store.get_application("track_alice_1", candidate_id="alice") is not None

    # Bob attempts to overwrite Alice's tracker item ID -> raises PermissionError
    malicious_item = ApplicationTrackerItem(
        id="track_alice_1",
        candidate_id="bob",
        job=job,
        status="rejected"
    )
    with pytest.raises(PermissionError, match="Cannot modify or overwrite a tracker record owned by another candidate"):
        store.save_or_update(malicious_item)

def test_legacy_tracker_migration_and_backup(tmp_path):
    """Proves legacy tracker records without candidate_id are backed up and quarantined to legacy_unassigned."""
    test_file = str(tmp_path / "legacy_tracker.json")
    
    # Write legacy unmigrated record
    legacy_data = {
        "legacy_item_1": {
            "id": "legacy_item_1",
            "job": {
                "id": "legacy_job_99",
                "title": "Legacy Mobile Dev",
                "company": "Old Corp",
                "location": "Lahore",
                "salary": "Not specified",
                "url": "https://example.com/legacy",
                "source": "Jooble"
            },
            "status": "applied",
            "notes": "Applied in early testing"
            # Note: candidate_id is intentionally omitted
        }
    }
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(legacy_data, f)

    # Initializing TrackerStore should trigger migration and create backup
    store = TrackerStore(filepath=test_file)

    # Verify backup exists
    backups = glob.glob(f"{test_file}.bak.*")
    assert len(backups) == 1, "Backup file was not created before migration"

    # Verify original record migrated to legacy_unassigned
    unassigned = store.list_legacy_unassigned()
    assert len(unassigned) == 1
    assert unassigned[0].id == "legacy_item_1"
    assert unassigned[0].candidate_id == LEGACY_UNASSIGNED_ID
    assert "Legacy unassigned record migrated" in unassigned[0].notes

    # Verify standard candidate query does NOT see the legacy record
    assert len(store.list_applications(candidate_id="anser_nawaz")) == 0

    # Test explicit assignment workflow
    assigned = store.assign_legacy_record("legacy_item_1", target_candidate_id="anser_nawaz")
    assert assigned is not None
    assert assigned.candidate_id == "anser_nawaz"
    assert len(store.list_applications(candidate_id="anser_nawaz")) == 1

def test_profile_input_validation():
    """Proves profile validation rejects blank names, malformed IDs, and invalid emails."""
    # Blank name
    with pytest.raises(ValueError, match="Candidate name cannot be blank"):
        validate_profile_inputs("user_1", {
            "name": "   ",
            "headline": "Developer",
            "total_years_experience": 4.0
        })

    # Malformed profile ID with spaces
    with pytest.raises(ValueError, match="Invalid profile ID"):
        validate_profile_inputs("bad id with spaces", {
            "name": "John Doe",
            "headline": "Developer",
            "total_years_experience": 4.0
        })

    # Malformed email
    with pytest.raises(ValueError, match="Invalid email address format"):
        validate_profile_inputs("john_doe", {
            "name": "John Doe",
            "headline": "Developer",
            "email": "not-an-email",
            "total_years_experience": 4.0
        })

    # Malformed phone characters
    with pytest.raises(ValueError, match="Invalid phone number format"):
        validate_profile_inputs("john_doe", {
            "name": "John Doe",
            "headline": "Developer",
            "phone": "abc-call-me-now",
            "total_years_experience": 4.0
        })

    # Valid profile with optional contact details
    valid = validate_profile_inputs("john_doe", {
        "name": "John Doe",
        "headline": "Senior Engineer",
        "email": "john.doe@example.com",
        "phone": "+92 300 1234567",
        "total_years_experience": 5.5
    })
    assert valid["name"] == "John Doe"
    assert valid["total_years_experience"] == 5.5

def test_atomic_write_recovery_on_failure(tmp_path):
    """Proves atomic write protects against partial/corrupted files if a write fails."""
    target_file = str(tmp_path / "data.json")
    initial_data = {"key": "safe_value"}
    atomic_write_json(target_file, initial_data)

    # Attempt to write non-serializable object
    class NonSerializable:
        pass

    with pytest.raises(TypeError):
        atomic_write_json(target_file, {"bad": NonSerializable()})

    # Verify original file remains completely intact
    with open(target_file, "r", encoding="utf-8") as f:
        restored = json.load(f)
    assert restored == initial_data

def test_concurrent_writes_with_locking(tmp_path):
    """Proves multi-threaded concurrent writes to TrackerStore succeed without corruption."""
    test_file = str(tmp_path / "concurrent_tracker.json")
    store = TrackerStore(filepath=test_file)

    def worker(worker_id: int):
        for i in range(10):
            job = JobPosting(
                id=f"job_w{worker_id}_{i}",
                title=f"Engineer {worker_id}-{i}",
                company="Corp",
                location="Lahore",
                url="https://example.com",
                source="Jooble"
            )
            item = ApplicationTrackerItem(
                id=f"track_w{worker_id}_{i}",
                candidate_id=f"cand_{worker_id}",
                job=job,
                status="saved"
            )
            store.save_or_update(item)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All 50 records should be safely present
    all_raw = store._read_data()
    assert len(all_raw) == 50
