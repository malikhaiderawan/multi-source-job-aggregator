import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from app.storage.profile_store import PROFILE_STORE

logger = logging.getLogger("RoutesProfiles")
router = APIRouter(prefix="/api/v1/profiles", tags=["Candidate Profiles"])

class CreateProfileRequest(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (e.g. haider_nawaz)")
    name: str = Field(..., description="Full legal or professional name")
    headline: str = Field(..., description="Target role headline")
    email: Optional[str] = Field(default="", description="Optional candidate email")
    phone: Optional[str] = Field(default="", description="Optional candidate phone")
    location: Optional[str] = Field(default="Lahore, Pakistan", description="Candidate location")
    github: Optional[str] = Field(default="", description="GitHub profile URL")
    linkedin: Optional[str] = Field(default="", description="LinkedIn profile URL")
    total_years_experience: float = Field(..., ge=0, description="Years of professional experience")
    all_skills: List[str] = Field(..., description="List of technical skills")
    target_locations: List[str] = Field(default_factory=lambda: ["Lahore", "Pakistan", "Remote", "Worldwide"])
    activate: bool = Field(default=True, description="Whether to activate profile immediately")

@router.get("")
async def list_profiles() -> List[dict]:
    """Lists all candidate profiles and indicates the active profile."""
    return PROFILE_STORE.list_profiles()

@router.get("/active")
async def get_active_profile() -> dict:
    """Returns the currently active candidate profile."""
    return PROFILE_STORE.get_active_profile_meta()

@router.post("")
async def create_candidate_profile(payload: CreateProfileRequest):
    """Creates a new candidate profile with strict input validation."""
    profile_data = {
        "name": payload.name,
        "headline": payload.headline,
        "email": payload.email or "",
        "phone": payload.phone or "",
        "location": payload.location or "Lahore, Pakistan",
        "github": payload.github or "",
        "linkedin": payload.linkedin or "",
        "total_years_experience": payload.total_years_experience,
        "categories": {
            "Custom": payload.all_skills
        },
        "all_skills": payload.all_skills,
        "target_locations": payload.target_locations,
        "work_history": [
            {
                "company": "Professional Experience",
                "role": payload.headline,
                "period": f"{payload.total_years_experience:.0f}+ Years",
                "highlights": [f"Specializing in {', '.join(payload.all_skills[:4])}"]
            }
        ],
        "featured_projects": []
    }
    try:
        saved = PROFILE_STORE.save_profile(payload.id, profile_data, activate=payload.activate)
        return saved
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"Unexpected error creating candidate profile: {err}")
        raise HTTPException(status_code=500, detail="Failed to create candidate profile.")

@router.put("/{profile_id}/activate")
async def activate_profile(profile_id: str):
    """Activates a candidate profile so that all match scores and tailored documents use it."""
    activated = PROFILE_STORE.set_active_profile(profile_id)
    if not activated:
        raise HTTPException(status_code=404, detail="Profile ID not found")
    return activated

@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """Deletes a custom candidate profile (default profile is protected)."""
    if profile_id == "anser_nawaz":
        raise HTTPException(status_code=400, detail="Default profile 'anser_nawaz' is protected and cannot be deleted.")

    if not PROFILE_STORE.has_profile(profile_id):
        raise HTTPException(status_code=404, detail="Profile not found.")

    success = PROFILE_STORE.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete profile.")
    return {"message": "Profile deleted", "profile_id": profile_id}
