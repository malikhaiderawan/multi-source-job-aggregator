import os
import re
import json
import logging
from typing import List, Optional, Dict
from app.models.profile import CandidateProfile, ANSER_PROFILE
from app.storage.file_utils import file_lock, atomic_write_json

logger = logging.getLogger("ProfileStore")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "candidate_profiles.json")

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PHONE_REGEX = re.compile(r'^[0-9+\-()\s]{7,25}$')
PROFILE_ID_REGEX = re.compile(r'^[a-zA-Z0-9_\-]+$')

def validate_profile_inputs(profile_id: str, profile_data: dict) -> dict:
    """
    Strict input validation for candidate profiles.
    Rejects blank names, malformed IDs, and invalid emails without exposing internal stack traces.
    Keeps phone and contact details optional, normalizing without inventing arbitrary codes.
    """
    clean_id = (profile_id or "").strip()
    if not clean_id or not PROFILE_ID_REGEX.match(clean_id) or len(clean_id) > 64:
        raise ValueError("Invalid profile ID: must be 1-64 alphanumeric characters, underscores, or hyphens.")

    name = (profile_data.get("name") or "").strip()
    if not name or len(name) < 2:
        raise ValueError("Candidate name cannot be blank and must be at least 2 characters.")

    headline = (profile_data.get("headline") or "").strip()
    if not headline:
        raise ValueError("Candidate headline cannot be blank.")

    exp = profile_data.get("total_years_experience")
    if exp is None:
        raise ValueError("Total years of experience is required.")
    try:
        exp_float = float(exp)
        if exp_float < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Total years of experience must be a non-negative number.")

    # Email validation: optional, but if provided, must be valid
    email = (profile_data.get("email") or "").strip()
    if email:
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email address format.")

    # Phone validation: optional, but if provided, must contain valid phone characters
    phone = (profile_data.get("phone") or "").strip()
    if phone:
        if not PHONE_REGEX.match(phone):
            raise ValueError("Invalid phone number format.")

    # Normalize sanitized fields
    sanitized = dict(profile_data)
    sanitized["name"] = name
    sanitized["headline"] = headline
    sanitized["total_years_experience"] = exp_float
    sanitized["email"] = email
    sanitized["phone"] = phone
    if "all_skills" in sanitized and isinstance(sanitized["all_skills"], list):
        sanitized["all_skills"] = [str(s).strip() for s in sanitized["all_skills"] if str(s).strip()]

    return sanitized


class ProfileStore:
    def __init__(self, filepath: Optional[str] = None):
        self.profiles_file = filepath or PROFILES_FILE
        self.data_dir = os.path.dirname(self.profiles_file)
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.profiles_file):
            self._initialize_default_profiles()

    def _initialize_default_profiles(self):
        default_profiles = {
            "anser_nawaz": {
                "id": "anser_nawaz",
                "is_active": True,
                "profile": ANSER_PROFILE.model_dump()
            },
            "haider_nawaz": {
                "id": "haider_nawaz",
                "is_active": False,
                "profile": {
                    "name": "Haider Nawaz",
                    "headline": "Full-Stack Software Engineer & Python / Cloud Specialist (4+ Years Exp)",
                    "email": "haidernawaz@example.com",
                    "phone": "+92 300 1234567",
                    "location": "Lahore, Pakistan",
                    "github": "https://github.com/HaiderNawaz",
                    "linkedin": "https://linkedin.com/in/haidernawaz",
                    "total_years_experience": 4.0,
                    "categories": {
                        "Frontend": ["React.js", "Next.js", "TypeScript", "JavaScript", "Tailwind CSS"],
                        "Backend": ["Python", "FastAPI", "Django", "Node.js", "REST APIs", "PostgreSQL"],
                        "Full-stack": ["Full Stack", "Docker", "AWS", "Databases", "Microservices"],
                        "Mobile": ["React Native", "Cross-Platform"]
                    },
                    "all_skills": [
                        "Python", "FastAPI", "Django", "React.js", "Next.js", "TypeScript",
                        "Node.js", "PostgreSQL", "Docker", "AWS", "REST APIs", "Git"
                    ],
                    "target_locations": ["Lahore", "Pakistan", "Remote", "Worldwide"],
                    "work_history": [
                        {
                            "company": "Tech Innovations",
                            "role": "Full-Stack Engineer",
                            "period": "2022 - Present",
                            "highlights": [
                                "Building scalable web platforms with Next.js, FastAPI, and PostgreSQL.",
                                "Containerizing applications using Docker and deploying on cloud infrastructure."
                            ]
                        }
                    ],
                    "featured_projects": [
                        {
                            "title": "Cloud Scale SaaS",
                            "stack": ["FastAPI", "React", "PostgreSQL", "Docker"],
                            "description": "Multi-tenant cloud management platform.",
                            "platforms": ["Web"]
                        }
                    ]
                }
            }
        }
        with file_lock(self.profiles_file):
            atomic_write_json(self.profiles_file, default_profiles)

    def _read_data(self) -> Dict[str, dict]:
        with file_lock(self.profiles_file, shared=True):
            try:
                if not os.path.exists(self.profiles_file):
                    self._initialize_default_profiles()
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading profiles file: {e}")
                return {}

    def _write_data(self, data: Dict[str, dict]):
        with file_lock(self.profiles_file, shared=False):
            atomic_write_json(self.profiles_file, data)

    def list_profiles(self) -> List[dict]:
        data = self._read_data()
        return list(data.values())

    def get_profile(self, profile_id: str) -> Optional[CandidateProfile]:
        data = self._read_data()
        meta = data.get(profile_id)
        if meta and "profile" in meta:
            return CandidateProfile(**meta["profile"])
        return None

    def has_profile(self, profile_id: str) -> bool:
        data = self._read_data()
        return profile_id in data

    def get_active_profile(self) -> CandidateProfile:
        data = self._read_data()
        for p in data.values():
            if p.get("is_active"):
                return CandidateProfile(**p.get("profile", {}))
        return ANSER_PROFILE

    def get_active_profile_meta(self) -> dict:
        data = self._read_data()
        for p in data.values():
            if p.get("is_active"):
                return p
        return {"id": "anser_nawaz", "is_active": True, "profile": ANSER_PROFILE.model_dump()}

    def set_active_profile(self, profile_id: str) -> Optional[dict]:
        with file_lock(self.profiles_file, shared=False):
            data = self._read_data()
            if profile_id not in data:
                return None
            for pid in data:
                data[pid]["is_active"] = (pid == profile_id)
            self._write_data(data)
            return data[profile_id]

    def save_profile(self, profile_id: str, profile_data: dict, activate: bool = False) -> dict:
        clean_id = (profile_id or "").strip()
        validated_data = validate_profile_inputs(clean_id, profile_data)

        with file_lock(self.profiles_file, shared=False):
            data = self._read_data()
            if activate:
                for pid in data:
                    data[pid]["is_active"] = False

            data[clean_id] = {
                "id": clean_id,
                "is_active": activate if clean_id not in data else data[clean_id].get("is_active", False),
                "profile": validated_data
            }
            if activate:
                data[clean_id]["is_active"] = True

            self._write_data(data)
            return data[clean_id]

    def delete_profile(self, profile_id: str) -> bool:
        clean_id = (profile_id or "").strip()
        if clean_id == "anser_nawaz":
            return False  # Protect default profile from deletion

        with file_lock(self.profiles_file, shared=False):
            data = self._read_data()
            if clean_id in data:
                was_active = data[clean_id].get("is_active", False)
                del data[clean_id]
                if was_active and "anser_nawaz" in data:
                    data["anser_nawaz"]["is_active"] = True
                self._write_data(data)
                return True
            return False

PROFILE_STORE = ProfileStore()
