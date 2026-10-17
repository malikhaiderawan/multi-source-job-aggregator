import httpx
import logging
from datetime import datetime
from typing import List
from app.models.job import JobPosting

logger = logging.getLogger("ArbeitnowClient")

async def fetch_arbeitnow_jobs(
    client: httpx.AsyncClient,
    search_query: str = "",
    remote_only: bool = False,
    fetch_depth: int = 50,
    page: int = 1
) -> List[JobPosting]:
    """Fetches job postings from Arbeitnow API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {}
    if page > 1:
        params["page"] = page

    try:
        response = await client.get(url, params=params, timeout=12.0)
        response.raise_for_status()
        raw_data = response.json()
        raw_jobs = raw_data.get("data", [])

        postings: List[JobPosting] = []
        for raw_job in raw_jobs:
            title = raw_job.get("title", "Untitled Role")
            company = raw_job.get("company_name") or "Unknown Company"
            is_remote = bool(raw_job.get("remote", False))
            loc = raw_job.get("location", "")
            if is_remote and loc:
                location = f"{loc} (Remote Friendly)"
            elif is_remote:
                location = "Remote / Anywhere"
            else:
                location = loc or "Unspecified"

            tags = raw_job.get("tags", [])
            link = raw_job.get("url", "")
            created_epoch = raw_job.get("created_at")
            if created_epoch:
                try:
                    posted_date = datetime.fromtimestamp(created_epoch).strftime("%Y-%m-%d")
                except Exception:
                    posted_date = str(created_epoch)
            else:
                posted_date = None

            raw_desc = raw_job.get("description", "")
            clean_snippet = raw_desc[:400].replace("<p>", "").replace("</p>", "").replace("<br>", " ") if raw_desc else ""

            # Check query filter if specified
            if search_query:
                q = search_query.lower()
                text_block = f"{title} {' '.join(tags)} {company} {raw_desc[:500]}".lower()
                if q not in text_block:
                    continue

            postings.append(
                JobPosting(
                    id=f"arbeitnow_{raw_job.get('slug')}",
                    title=title,
                    company=company,
                    location=location,
                    salary="Competitive / Disclosed on request",
                    url=link,
                    source="Arbeitnow",
                    posted_date=posted_date,
                    description_snippet=clean_snippet,
                    is_remote=is_remote,
                    tags=tags
                )
            )

            if len(postings) >= fetch_depth:
                break

        logger.info(f"Arbeitnow: Retrieved {len(postings)} jobs (page={page}, query='{search_query}')")
        return postings
    except Exception as err:
        logger.warning(f"Arbeitnow fetch error: {err}")
        return []
