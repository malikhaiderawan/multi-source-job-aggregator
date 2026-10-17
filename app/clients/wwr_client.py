import httpx
import logging
import xml.etree.ElementTree as ET
from typing import List
from app.models.job import JobPosting

logger = logging.getLogger("WWRClient")

WWR_FEEDS = {
    "Full-stack": "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "Frontend": "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "Backend": "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "Programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
}

async def fetch_wwr_jobs(
    client: httpx.AsyncClient,
    category: str = "Full-stack",
    fetch_depth: int = 100
) -> List[JobPosting]:
    """Fetches legitimate remote jobs from WeWorkRemotely RSS feeds."""
    feed_url = WWR_FEEDS.get(category, WWR_FEEDS["Full-stack"])

    try:
        response = await client.get(feed_url, timeout=12.0)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        
        postings: List[JobPosting] = []
        items = root.findall(".//item")
        
        for item in items[:fetch_depth]:
            raw_title = item.find("title").text if item.find("title") is not None else "Untitled Role"
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            desc = item.find("description").text if item.find("description") is not None else ""
            
            # WWR titles are usually formatted as "Company Name: Job Title"
            if ":" in raw_title:
                parts = raw_title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                company = "WeWorkRemotely Partner"
                title = raw_title.strip()

            clean_snippet = desc[:400].replace("<p>", "").replace("</p>", "").replace("<br>", " ") if desc else ""

            # Check region if available
            region_el = item.find("region")
            location = region_el.text if region_el is not None and region_el.text else "Worldwide / Remote"

            postings.append(
                JobPosting(
                    id=f"wwr_{hash(link) & 0xffffffff}",
                    title=title,
                    company=company,
                    location=location,
                    salary="Disclosed in application",
                    url=link,
                    source="WeWorkRemotely",
                    posted_date=pub_date,
                    description_snippet=clean_snippet,
                    is_remote=True,
                    category=category,
                    tags=[category, "Remote", "Engineering"]
                )
            )

        logger.info(f"WeWorkRemotely: Retrieved {len(postings)} jobs for category='{category}'")
        return postings
    except Exception as err:
        logger.warning(f"WeWorkRemotely fetch error: {err}")
        return []
