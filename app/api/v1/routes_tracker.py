import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.job import ApplicationTrackerItem
from app.storage.tracker_store import TRACKER_STORE
from app.storage.profile_store import PROFILE_STORE

logger = logging.getLogger("RoutesTracker")
router = APIRouter(prefix="/api/v1/tracker", tags=["Application Tracker"])

class StatusUpdateRequest(BaseModel):
    status: str

class LegacyAssignRequest(BaseModel):
    target_candidate_id: str = Field(..., description="Target candidate profile ID to assign this legacy record to")

def _resolve_candidate_id(provided_id: Optional[str]) -> str:
    """
    Resolves and validates candidate ID against existing profiles.
    Falls back to active profile if none is provided.
    """
    if provided_id and provided_id.strip():
        clean_id = provided_id.strip()
        if not PROFILE_STORE.has_profile(clean_id):
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        return clean_id
    active_meta = PROFILE_STORE.get_active_profile_meta()
    return active_meta.get("id", "anser_nawaz")

@router.get("", response_model=List[ApplicationTrackerItem])
async def list_applications(
    candidate_id: Optional[str] = Query(None, description="Optional candidate profile ID; defaults to active candidate"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Retrieves tracked applications scoped strictly to the selected candidate.
    """
    effective_candidate_id = _resolve_candidate_id(candidate_id)
    return TRACKER_STORE.list_applications(candidate_id=effective_candidate_id, status=status)

@router.post("", response_model=ApplicationTrackerItem)
async def create_or_update_application(
    item: ApplicationTrackerItem,
    candidate_id: Optional[str] = Query(None, description="Authorized candidate context")
):
    """
    Saves or updates a job application in the tracker scoped strictly to the candidate.
    Guards against cross-candidate overwrites and verifies candidate existence.
    """
    effective_candidate_id = _resolve_candidate_id(candidate_id or item.candidate_id)
    
    if item.candidate_id != effective_candidate_id:
        raise HTTPException(
            status_code=400,
            detail="Mismatched candidate ID: item candidate_id does not match the active or specified candidate context."
        )

    if not PROFILE_STORE.has_profile(item.candidate_id):
        raise HTTPException(status_code=400, detail="Candidate profile does not exist.")

    try:
        return TRACKER_STORE.save_or_update(item, expected_candidate_id=effective_candidate_id)
    except PermissionError as perm_err:
        raise HTTPException(status_code=403, detail=str(perm_err))

@router.get("/legacy/unassigned", response_model=List[ApplicationTrackerItem])
async def list_legacy_unassigned():
    """
    Explicit review workflow: Lists legacy records without candidate assignment.
    """
    return TRACKER_STORE.list_legacy_unassigned()

@router.post("/legacy/{tracker_id}/assign", response_model=ApplicationTrackerItem)
async def assign_legacy_record(tracker_id: str, payload: LegacyAssignRequest):
    """
    Explicit review workflow: Safely assigns a legacy unassigned record to a candidate.
    """
    if not PROFILE_STORE.has_profile(payload.target_candidate_id):
        raise HTTPException(status_code=404, detail="Target candidate profile not found.")
    
    try:
        updated = TRACKER_STORE.assign_legacy_record(tracker_id, payload.target_candidate_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Legacy record not found.")
        return updated
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))

@router.get("/{tracker_id}", response_model=ApplicationTrackerItem)
async def get_application(
    tracker_id: str,
    candidate_id: Optional[str] = Query(None, description="Optional candidate profile ID; defaults to active candidate")
):
    """
    Retrieves a specific tracked job application scoped to the active/specified candidate.
    Returns non-disclosing 404 if item does not exist or belongs to another candidate.
    """
    effective_candidate_id = _resolve_candidate_id(candidate_id)
    item = TRACKER_STORE.get_application(tracker_id, candidate_id=effective_candidate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tracked application not found")
    return item

@router.patch("/{tracker_id}/status", response_model=ApplicationTrackerItem)
async def update_application_status(
    tracker_id: str,
    payload: StatusUpdateRequest,
    candidate_id: Optional[str] = Query(None, description="Optional candidate profile ID; defaults to active candidate")
):
    """
    Updates application status scoped to the candidate owner.
    """
    valid_statuses = ["saved", "pending_approval", "applied", "interview", "rejected", "follow_up"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    effective_candidate_id = _resolve_candidate_id(candidate_id)
    updated = TRACKER_STORE.update_status(tracker_id, payload.status, candidate_id=effective_candidate_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated

@router.delete("/{tracker_id}")
async def delete_application(
    tracker_id: str,
    candidate_id: Optional[str] = Query(None, description="Optional candidate profile ID; defaults to active candidate")
):
    """
    Deletes an application from the tracker scoped to the candidate owner.
    """
    effective_candidate_id = _resolve_candidate_id(candidate_id)
    success = TRACKER_STORE.delete(tracker_id, candidate_id=effective_candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application removed from tracker", "tracker_id": tracker_id}
