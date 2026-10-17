import re
from typing import Tuple, Optional

# Explicit exclusion patterns: regional restrictions that exclude candidates from Pakistan
INELIGIBLE_REGION_PATTERNS = [
    r"\b(us|usa|u\.s\.|u\.s\.a\.)\s*(only|citizens?|residents?|based)\b",
    r"\bunited\s*states\s*(only|residents?|citizens?|based)\b",
    r"\b(us|usa)\s*(or|and)\s*canada\b",
    r"\b(canada|canadian)\s*(only|residents?|citizens?|based)\b",
    r"\b(uk|united\s*kingdom)\s*(only|residents?|citizens?|based)\b",
    r"\b(eu|europe|european\s*union)\s*(only|residents?|citizens?|based)\b",
    r"\b(germany|german)\s*(only|residents?|based)\b",
    r"\blatam\s*(only|based)\b",
    r"\blatin\s*america\s*(only|based)\b",
    r"\bnorth\s*america\s*(only|based)\b",
    r"\b(emea)\s*(only|based)\b",
    r"\b(australia|nz|new\s*zealand)\s*(only|based)\b",
    r"\btimezone[s]?\s*:\s*(est|pst|cst|mst|gmt|cet|bst)\s*only\b",
    r"\b(authorized|eligible)\s*to\s*work\s*in\s*the\s*(us|usa|united\s*states|eu|uk|canada)\b"
]

# Explicit confirmed worldwide remote phrases
WORLDWIDE_CONFIRMED_PHRASES = [
    "anywhere in the world",
    "worldwide",
    "work from anywhere",
    "anywhere",
    "global",
    "remote - worldwide",
    "worldwide / remote",
    "all countries",
    "worldwide (remote)",
    "remote (worldwide)"
]

def classify_location_eligibility(
    raw_location: Optional[str],
    title: str = "",
    snippet: str = "",
    is_remote: bool = False
) -> Tuple[str, str]:
    """
    Deterministically classifies a job posting's geographic eligibility
    for a Lahore, Pakistan based candidate.

    Returns:
        tuple (eligibility_code, detail_explanation)

    Eligibility codes:
        - 'lahore_onsite': On-site in Lahore, Pakistan
        - 'lahore_hybrid': Hybrid in Lahore, Pakistan
        - 'pakistan_remote': Explicitly targeting or based in Pakistan as a remote position
        - 'worldwide_remote': Confirmed global remote open worldwide including Pakistan
        - 'ineligible_region': Explicit regional restrictions (e.g., US-only, EU-only) excluding Pakistan
        - 'eligibility_unknown': Listed simply as remote or missing without explicit geographic declaration
    """
    loc_clean = (raw_location or "").strip().lower()
    title_clean = (title or "").strip().lower()
    snippet_clean = (snippet or "").strip().lower()

    # 1. Check for Missing or Empty Location
    if not loc_clean or loc_clean in ["not specified", "unspecified", "unknown", "none"]:
        if is_remote:
            return (
                "eligibility_unknown",
                "Location omitted by provider; remote flag set but regional eligibility unknown."
            )
        return (
            "eligibility_unknown",
            "Location information missing or unstated by provider."
        )

    # 2. Check for Lahore On-site or Hybrid
    is_lahore = "lahore" in loc_clean or "lahore" in title_clean
    if is_lahore:
        is_hybrid = any(h in loc_clean or h in title_clean or h in snippet_clean[:200] for h in ["hybrid", "partially remote", "flexible"])
        if is_hybrid:
            return (
                "lahore_hybrid",
                f"Hybrid position based in Lahore, Pakistan ({raw_location.strip()})."
            )
        # Check if explicitly remote from Lahore
        if is_remote or "remote" in loc_clean:
            return (
                "pakistan_remote",
                f"Remote position specifically targeting or based in Lahore, Pakistan ({raw_location.strip()})."
            )
        return (
            "lahore_onsite",
            f"On-site position based in Lahore, Pakistan ({raw_location.strip()})."
        )

    # 3. Check for other Pakistan Locations (Karachi, Islamabad, Rawalpindi, Pakistan-wide)
    is_pakistan = any(p in loc_clean for p in ["pakistan", "islamabad", "karachi", "rawalpindi", "faisalabad", "peshawar"])
    if is_pakistan:
        if is_remote or "remote" in loc_clean:
            return (
                "pakistan_remote",
                f"Remote position explicitly open to candidates in Pakistan ({raw_location.strip()})."
            )
        is_hybrid = any(h in loc_clean or h in title_clean for h in ["hybrid", "partially remote"])
        if is_hybrid:
            return (
                "pakistan_hybrid",
                f"Hybrid position based in Pakistan ({raw_location.strip()})."
            )
        return (
            "pakistan_onsite",
            f"On-site position based in Pakistan ({raw_location.strip()})."
        )

    # 4. Check for Explicitly Ineligible Regions
    searchable_text = f"{loc_clean} {title_clean} {snippet_clean[:300]}"
    for pattern in INELIGIBLE_REGION_PATTERNS:
        match = re.search(pattern, searchable_text)
        if match:
            # Verify no overriding global declaration
            if not any(w in loc_clean for w in ["worldwide", "anywhere", "pakistan"]):
                matched_restriction = match.group(0).strip()
                return (
                    "ineligible_region",
                    f"Restricted to '{matched_restriction}'. Applicants from Pakistan are not eligible."
                )

    # 5. Check for Specific Country Lists excluding Pakistan (e.g. 'Europe, USA, UK, Canada, Australia...')
    if is_remote and any(c in loc_clean for c in ["usa", "uk", "canada", "germany", "europe", "australia"]):
        if not any(w in loc_clean for w in ["worldwide", "anywhere", "pakistan", "global"]):
            return (
                "ineligible_region",
                f"Regional restriction: listed for ({raw_location.strip()}), excluding Pakistan."
            )

    # 6. Check for Confirmed Worldwide Remote
    is_worldwide = any(phrase in loc_clean for phrase in WORLDWIDE_CONFIRMED_PHRASES) or \
                   any(phrase in title_clean for phrase in ["worldwide", "anywhere in the world"])
    if is_worldwide:
        return (
            "worldwide_remote",
            f"Worldwide remote role confirmed open to global applicants including Pakistan ({raw_location.strip()})."
        )

    # 7. Ambiguous Remote
    if is_remote or "remote" in loc_clean:
        return (
            "eligibility_unknown",
            f"Listed simply as remote ({raw_location.strip()}); employer has not explicitly confirmed Pakistan eligibility."
        )

    # 8. Unclassified foreign on-site position
    return (
        "ineligible_region",
        f"On-site role outside Pakistan ({raw_location.strip()})."
    )
