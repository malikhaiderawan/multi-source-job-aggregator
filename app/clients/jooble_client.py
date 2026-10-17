import os
import httpx
import logging
from typing import List
from app.models.job import JobPosting

logger = logging.getLogger("JoobleClient")

async def fetch_jooble_jobs(
    client: httpx.AsyncClient,
    keywords: str = "Full Stack",
    location: str = "Lahore",
    fetch_depth: int = 30
) -> List[JobPosting]:
    """Fetches job postings from Jooble API with support for Pakistan and international regions."""
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        logger.info("Jooble: JOOBLE_API_KEY not configured. Skipping Jooble provider.")
        return []

    url = f"https://jooble.org/api/{api_key}"
    payload = {
        "keywords": keywords,
        "page": "1",
        "resultOnPage": min(fetch_depth, 50),
    }
    if location and location.strip():
        payload["location"] = location.strip()

    try:
        response = await client.post(url, json=payload, timeout=12.0)
        response.raise_for_status()
        raw_data = response.json()
        raw_jobs = raw_data.get("jobs", [])
        
        postings: List[JobPosting] = []
        for raw_job in raw_jobs:
            title = raw_job.get("title", "Untitled Role")
            company = raw_job.get("company") or "Unknown Company"
            loc = raw_job.get("location") or location or "Unspecified Location"
            salary = raw_job.get("salary") or "Not specified"
            link = raw_job.get("link", "")
            snippet = raw_job.get("snippet", "")
            clean_snippet = snippet[:400].replace("<p>", "").replace("</p>", "").replace("<br>", " ") if snippet else ""

            is_remote = any(
                term in loc.lower() or term in title.lower() or term in clean_snippet.lower()
                for term in ["remote", "worldwide", "anywhere", "work from home", "telecommute", "virtual"]
            )

            postings.append(
                JobPosting(
                    id=f"jooble_{raw_job.get('id')}" if raw_job.get("id") else None,
                    title=title,
                    company=company,
                    location=loc,
                    salary=salary,
                    url=link,
                    source="Jooble",
                    description_snippet=clean_snippet,
                    is_remote=is_remote,
                    country="Pakistan" if "pakistan" in loc.lower() or "lahore" in loc.lower() else "International"
                )
            )

        logger.info(f"Jooble: Retrieved {len(postings)} jobs for keywords='{keywords}' | location='{location}'")
        return postings
    except Exception as err:
        logger.warning(f"Jooble fetch error: {err}")
        return []
