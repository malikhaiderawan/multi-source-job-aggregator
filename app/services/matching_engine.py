import re
from typing import Optional, List, Dict, Any
from app.models.job import JobPosting, MatchScoreBreakdown
from app.models.profile import CandidateProfile
from app.storage.profile_store import PROFILE_STORE
from app.services.location_classifier import classify_location_eligibility

SENIOR_KEYWORDS = ["senior", "lead", "sr", "staff", "principal", "architect", "head", "specialist", "expert"]
MID_KEYWORDS = ["mid", "intermediate", "developer", "engineer"]
JUNIOR_KEYWORDS = ["junior", "jr", "intern", "trainee", "associate", "graduate", "entry"]

# Regex patterns for mobile detection in job title
MOBILE_TITLE_PATTERNS = [
    r"\breact\s*native\b",
    r"\bflutter\b",
    r"\bios\b",
    r"\bandroid\b",
    r"\bmobile\s*(app|developer|engineer|lead|architect|team\s*lead)?\b",
    r"\b(swift|kotlin)\s*(developer|engineer|mobile)\b"
]

def detect_category(title: str, text: str = "") -> str:
    """
    Accurately classifies a job into Mobile, Frontend, Backend, or Full-stack.
    Prioritizes explicit title keywords first to avoid misclassifying backend/full-stack
    roles that merely mention collaborating with mobile teams in their description.
    """
    title_clean = (title or "").lower().strip()
    text_clean = (text or "").lower().strip()

    # 1. Title Mobile check (explicit mobile tech or title)
    for pat in MOBILE_TITLE_PATTERNS:
        if re.search(pat, title_clean):
            return "Mobile"

    # 2. Title Full-stack check (takes precedence over isolated backend/frontend keywords in title)
    if any(k in title_clean for k in ["full stack", "fullstack", "full-stack"]):
        return "Full-stack"

    # 3. Title Frontend check
    if any(k in title_clean for k in ["frontend", "front-end", "ui engineer", "ui developer", "web developer"]):
        return "Frontend"
    if any(k in title_clean for k in ["react", "react.js", "next.js", "nextjs", "vue", "angular"]):
        if not any(b in title_clean for b in ["backend", "back-end", "node", "python"]):
            return "Frontend"

    # 4. Title Backend check
    if any(k in title_clean for k in ["backend", "back-end", "api engineer", "api developer"]):
        return "Backend"
    if any(k in title_clean for k in ["node.js", "nodejs", "express.js", "fastapi", "django"]):
        return "Backend"
    if "python" in title_clean and any(e in title_clean for e in ["developer", "engineer", "lead"]):
        return "Backend"

    # 5. Title General Engineering / Architecture check
    if any(k in title_clean for k in ["software engineer", "solutions architect", "team lead", "technical lead", "engineering manager"]):
        # Check snippet context if available
        if text_clean:
            mobile_signals = sum(bool(re.search(pat, text_clean)) for pat in MOBILE_TITLE_PATTERNS)
            if mobile_signals >= 2 and not any(k in text_clean for k in ["backend microservices", "distributed systems", "devops"]):
                return "Mobile"
        return "Full-stack"

    # 6. Fallback based on snippet text if title was generic (e.g. 'Senior Developer')
    if text_clean:
        # Check if mobile signals dominate
        mobile_matches = sum(bool(re.search(pat, text_clean)) for pat in MOBILE_TITLE_PATTERNS)
        if mobile_matches >= 2:
            return "Mobile"
        if any(k in text_clean for k in ["frontend", "react.js", "next.js", "tailwind", "responsive ui"]):
            if not any(k in text_clean for k in ["full stack", "backend", "databases", "microservices"]):
                return "Frontend"
        if any(k in text_clean for k in ["backend", "node.js", "fastapi", "rest api", "postgresql"]):
            if not any(k in text_clean for k in ["full stack", "frontend", "ui"]):
                return "Backend"

    # Default to Full-stack
    return "Full-stack"

def calculate_match_score(job: JobPosting, profile: Optional[CandidateProfile] = None) -> MatchScoreBreakdown:
    """Calculates comprehensive match score (0-100%) against candidate profile."""
    if profile is None:
        profile = PROFILE_STORE.get_active_profile()

    searchable_text = f"{job.title} {job.description_snippet} {' '.join(job.tags)} {job.location}".lower()

    # 1. Technical Skills Score (Max 40 points)
    matched_skills = []
    for skill in profile.all_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, searchable_text):
            matched_skills.append(skill)

    skills_count = len(matched_skills)
    if skills_count >= 4:
        skills_score = 40
    elif skills_count == 3:
        skills_score = 34
    elif skills_count == 2:
        skills_score = 28
    elif skills_count == 1:
        skills_score = 22
    else:
        if any(term in searchable_text for term in ["developer", "engineer", "software", "web", "mobile", "app", "programmer"]):
            skills_score = 18
        else:
            skills_score = 10

    # 2. Seniority & Experience Score (Max 25 points)
    title_lower = job.title.lower()
    notes = []
    
    is_intern = any(re.search(r"\b" + re.escape(k) + r"\b", title_lower) for k in ["intern", "internship", "trainee", "apprenticeship"])
    is_senior = any(re.search(r"\b" + re.escape(k) + r"\b", title_lower) for k in SENIOR_KEYWORDS)
    is_junior = any(re.search(r"\b" + re.escape(k) + r"\b", title_lower) for k in JUNIOR_KEYWORDS)

    candidate_is_senior = profile.total_years_experience >= 5.0

    if is_intern:
        seniority_score = 0 if candidate_is_senior else 20
        seniority_level = "Internship / Trainee"
        if candidate_is_senior:
            notes.append("Seniority mismatch: Internship/entry-level trainee role is unsuitable for a 6+ years experienced senior engineer.")
        else:
            notes.append("Targeting internship/trainee role.")
    elif is_senior:
        seniority_score = 25 if candidate_is_senior else 18
        seniority_level = "Senior / Lead"
        notes.append(f"Seniority alignment ({profile.total_years_experience:.0f}+ yrs exp candidate).")
    elif is_junior:
        seniority_score = 5 if candidate_is_senior else 25
        seniority_level = "Junior"
        notes.append("Junior role; candidate is significantly overqualified.")
    else:
        seniority_score = 22
        seniority_level = "Mid-Senior"
        notes.append("Standard engineer title; appropriate fit.")

    # 3. Location & Work Mode Score (Max 25 points)
    # Uses verified location eligibility classification
    eligibility = job.location_eligibility or "eligibility_unknown"
    if eligibility in ["lahore_onsite", "lahore_hybrid"]:
        location_score = 25
        notes.append(f"Prime location match: Lahore on-site/hybrid role ({job.location}).")
    elif eligibility == "pakistan_remote":
        location_score = 25
        notes.append(f"Prime location match: Pakistan remote role ({job.location}).")
    elif eligibility in ["pakistan_onsite", "pakistan_hybrid"]:
        # Physical office outside Lahore commute area (e.g. Karachi, Islamabad)
        location_score = 6
        notes.append(f"Workplace in {job.location} (outside Lahore commute area; requires relocation).")
    elif eligibility == "worldwide_remote":
        location_score = 22
        notes.append("Worldwide remote role confirmed open globally including Pakistan.")
    elif eligibility == "eligibility_unknown":
        location_score = 16
        notes.append("Remote role with unspecified regional eligibility; verify employer requirements.")
    elif eligibility == "ineligible_region":
        location_score = 5
        notes.append(f"Restricted location: {job.eligibility_detail or 'Ineligible region'}.")
    else:
        location_score = 10
        notes.append("Location requires presence outside primary target region.")

    # 4. Salary Score (Max 10 points)
    sal = job.salary.lower().strip()
    if sal and sal not in ["not specified", "unspecified", "disclosed in application", "competitive / disclosed on request"]:
        salary_score = 10
        notes.append(f"Disclosed salary: {job.salary}")
    else:
        salary_score = 5

    total_score = min(100, max(0, skills_score + seniority_score + location_score + salary_score))
    if is_intern and candidate_is_senior:
        total_score = min(total_score, 28)

    return MatchScoreBreakdown(
        skills_score=skills_score,
        seniority_score=seniority_score,
        location_score=location_score,
        salary_score=salary_score,
        total_score=total_score,
        matched_skills=matched_skills,
        missing_skills=[],
        notes=notes
    )

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

def extract_contact_email(text: str) -> Optional[str]:
    """Finds genuine recruiter/application contact email from text if present."""
    if not text:
        return None
    matches = EMAIL_REGEX.findall(text)
    for m in matches:
        m_lower = m.lower()
        if any(m_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"]):
            continue
        if any(bad in m_lower for bad in ["example.com", "test.com", "placeholder", "domain.com"]):
            continue
        return m.strip()
    return None

def enrich_job_posting(job: JobPosting, profile: Optional[CandidateProfile] = None) -> JobPosting:
    """
    Enriches job posting with deterministic category detection,
    location eligibility classification, seniority, match score against candidate,
    and auto-extracted contact email if available.
    """
    if not job.original_location:
        job.original_location = job.location

    # Classify location eligibility
    eligibility_code, detail = classify_location_eligibility(
        raw_location=job.location,
        title=job.title,
        snippet=job.description_snippet or "",
        is_remote=job.is_remote
    )
    job.location_eligibility = eligibility_code
    job.eligibility_detail = detail

    category = detect_category(job.title, job.description_snippet or "")
    breakdown = calculate_match_score(job, profile=profile)

    # Extract contact email if present in job text
    if not job.contact_email:
        searchable_text = f"{job.title} {job.description_snippet or ''} {job.location}"
        job.contact_email = extract_contact_email(searchable_text)
    
    title_lower = job.title.lower()
    if any(k in title_lower for k in ["lead", "head", "architect", "principal", "manager"]):
        seniority = "Technical Lead"
    elif any(k in title_lower for k in ["senior", "sr."]):
        seniority = "Senior Engineer"
    elif any(k in title_lower for k in ["intern", "internship", "trainee"]):
        seniority = "Internship / Trainee"
    elif any(k in title_lower for k in ["junior", "associate"]):
        seniority = "Junior Engineer"
    else:
        seniority = "Senior / Mid Engineer"

    job.category = category
    job.seniority_level = seniority
    job.match_score = breakdown.total_score
    job.match_breakdown = breakdown
    return job
