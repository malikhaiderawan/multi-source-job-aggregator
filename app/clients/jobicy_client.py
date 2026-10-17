import httpx
import logging
from typing import List
from app.models.job import JobPosting

logger = logging.getLogger("JobicyClient")

async def fetch_jobicy_jobs(
    client: httpx.AsyncClient,
    tag: str = "dev",
    geo: str = "",
    fetch_depth: int = 50
) -> List[JobPosting]:
    """Fetches remote job postings from Jobicy API v2."""
    url = "https://jobicy.com/api/v2/remote-jobs"
    params = {"count": min(max(1, fetch_depth), 50)}

    if tag and tag.lower() in ["dev", "engineering", "design", "product", "data-science"]:
        params["tag"] = tag.lower()
    else:
        # Default to software development category
        params["tag"] = "dev"

    if geo:
        params["geo"] = geo.lower()

    try:
        response = await client.get(url, params=params, timeout=12.0)
        # If tag error, retry without tag
        if response.status_code == 400 and "tag" in params:
            params.pop("tag", None)
            response = await client.get(url, params=params, timeout=12.0)

        response.raise_for_status()
        raw_data = response.json()
        raw_jobs = raw_data.get("jobs", [])

        postings: List[JobPosting] = []
        for raw_job in raw_jobs:
            title = raw_job.get("jobTitle", "Untitled Role")
            company = raw_job.get("companyName") or "Unknown Company"
            location = raw_job.get("jobGeo") or raw_job.get("jobCountry") or "Worldwide / Remote"

            salary_min = raw_job.get("annualSalaryMin")
            salary_max = raw_job.get("annualSalaryMax")
            currency = raw_job.get("salaryCurrency", "USD").strip()

            if salary_min and salary_max:
                salary_str = f"{currency} {salary_min:,} - {salary_max:,} / yr"
            elif salary_min:
                salary_str = f"From {currency} {salary_min:,} / yr"
            elif salary_max:
                salary_str = f"Up to {currency} {salary_max:,} / yr"
            else:
                salary_str = "Not specified"

            link = raw_job.get("url", "")
            posted = raw_job.get("pubDate", "")
            snippet = raw_job.get("jobExcerpt") or raw_job.get("jobDescription", "")
            clean_snippet = snippet[:400].replace("<p>", "").replace("</p>", "").replace("<br>", " ") if snippet else ""

            postings.append(
                JobPosting(
                    id=f"jobicy_{raw_job.get('id')}",
                    title=title,
                    company=company,
                    location=location,
                    salary=salary_str,
                    url=link,
                    source="Jobicy",
                    posted_date=posted,
                    description_snippet=clean_snippet,
                    is_remote=True,
                    country=raw_job.get("jobCountry", "Remote"),
                    tags=raw_job.get("jobIndustry", [])
                )
            )
        logger.info(f"Jobicy: Retrieved {len(postings)} jobs (tag={params.get('tag', '')})")
        return postings
    except Exception as err:
        logger.warning(f"Jobicy fetch error: {err}")
        return []
