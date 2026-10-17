import re
import urllib.parse
from typing import List, Set, Dict
from app.models.job import JobPosting

def normalize_text(text: str) -> str:
    """Removes special characters and extra whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())

def clean_url(url: str) -> str:
    """Removes marketing tracking parameters (utm_*, ref, etc.) from job URLs."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qsl(parsed.query)
        filtered_params = [
            (k, v) for k, v in query_params 
            if not k.startswith("utm_") and k not in ["ref", "source", "feed", "partner"]
        ]
        clean_query = urllib.parse.urlencode(filtered_params)
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ""
        )).rstrip("/")
    except Exception:
        return url.strip().rstrip("/")

def deduplicate_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    """
    Deduplicates job postings by canonical URL and normalized (title + company) keys.
    When duplicates exist, preserves the posting with the richest data.
    """
    seen_urls: Set[str] = set()
    seen_entity_keys: Dict[str, JobPosting] = {}
    deduped: List[JobPosting] = []

    for job in jobs:
        c_url = clean_url(job.url)
        norm_title = normalize_text(job.title)
        norm_company = normalize_text(job.company)
        entity_key = f"{norm_title}___{norm_company}"

        # If direct URL already processed, skip
        if c_url and c_url in seen_urls:
            continue

        # If identical title & company already seen from another provider
        if entity_key in seen_entity_keys:
            existing = seen_entity_keys[entity_key]
            # Replace if new one has better salary or details
            if existing.salary in ["Not specified", "Unspecified"] and job.salary not in ["Not specified", "Unspecified"]:
                seen_entity_keys[entity_key] = job
            continue

        if c_url:
            seen_urls.add(c_url)
        seen_entity_keys[entity_key] = job

    deduped = list(seen_entity_keys.values())
    return deduped
