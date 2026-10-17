import httpx
import logging
from typing import List
from app.models.job import JobPosting

logger = logging.getLogger("RemotiveClient")

async def fetch_remotive_jobs(
    client: httpx.AsyncClient,
    search_query: str = "",
    category: str = "",
    fetch_depth: int = 50
) -> List[JobPosting]:
    """Fetches remote job postings from Remotive API."""
    url = "https://remotive.com/api/remote-jobs"
    params = {}
    if search_query:
        params["search"] = search_query
    if category:
        params["category"] = category

    try:
        response = await client.get(url, params=params, timeout=12.0)
        response.raise_for_status()
        raw_data = response.json()
        raw_jobs = raw_data.get("jobs", [])
        
        postings: List[JobPosting] = []
        for raw_job in raw_jobs[:fetch_depth]:
            title = raw_job.get("title", "Untitled Role")
            company = raw_job.get("company_name") or "Unknown Company"
            location = raw_job.get("candidate_required_location") or "Worldwide / Remote"
            salary = raw_job.get("salary") or "Not specified"
            link = raw_job.get("url", "")
            posted = raw_job.get("publication_date", "")
            snippet = raw_job.get("description", "")
            # Clean snippet from raw HTML if present
            clean_snippet = snippet[:400].replace("<p>", "").replace("</p>", "").replace("<br>", " ") if snippet else ""

            postings.append(
                JobPosting(
                    id=f"remotive_{raw_job.get('id')}",
                    title=title,
                    company=company,
                    location=location,
                    salary=salary if salary.strip() else "Not specified",
                    url=link,
                    source="Remotive",
                    posted_date=posted,
                    description_snippet=clean_snippet,
                    is_remote=True,
                    country="Remote",
                    tags=raw_job.get("tags", [])
                )
            )
        logger.info(f"Remotive: Retrieved {len(postings)} jobs for query='{search_query}'")
        return postings
    except Exception as err:
        logger.warning(f"Remotive fetch error: {err}")
        return []
