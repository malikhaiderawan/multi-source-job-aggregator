import re
import html
import logging
from typing import List
import httpx
from app.models.job import JobPosting

logger = logging.getLogger("MustakbilClient")

MUSTAKBIL_LAHORE_URL = "https://www.mustakbil.com/jobs/pakistan/lahore/information-technology"
MUSTAKBIL_PAKISTAN_URL = "https://www.mustakbil.com/jobs/pakistan/information-technology"

TITLE_REGEX = re.compile(
    r'class=[\"\']jc-title__link[\"\'][^>]*aria-label=[\"\'](.+?)[\"\'][^>]*href=[\"\'](/jobs/job/(\d+))[\"\']',
    re.IGNORECASE
)

async def fetch_mustakbil_jobs(
    client: httpx.AsyncClient,
    location: str = "Lahore",
    fetch_depth: int = 30
) -> List[JobPosting]:
    """
    Fetches real-time tech and engineering jobs from Mustakbil (Pakistan's direct tech portal).
    Provides native Lahore on-site and hybrid jobs without requiring third-party API keys.
    """
    target_urls = [MUSTAKBIL_LAHORE_URL]
    if location and "lahore" not in location.lower():
        target_urls.append(MUSTAKBIL_PAKISTAN_URL)

    postings: List[JobPosting] = []
    seen_ids = set()

    for url in target_urls:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code != 200:
                continue

            matches = TITLE_REGEX.findall(response.text)
            for raw_aria, href, job_id in matches:
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                # Parse 'Role at Company in Location' or 'Role | Company | Location'
                # aria-label pattern: e.g. "Software Engineer at Devsinc in Lahore"
                clean_aria = html.unescape(raw_aria).strip()
                m = re.match(r'^(.*?)\s+at\s+(.*?)\s+in\s+(.*?)$', clean_aria, re.IGNORECASE)
                if m:
                    title, company, loc = m.groups()
                else:
                    parts = clean_aria.split("|")
                    if len(parts) >= 3:
                        title, company, loc = parts[0], parts[1], parts[2]
                    elif len(parts) == 2:
                        title, company, loc = parts[0], parts[1], "Lahore"
                    else:
                        title, company, loc = clean_aria, "Pakistani Employer", "Lahore"

                title = title.strip()
                company = company.strip()
                loc = loc.strip() or "Lahore"
                full_url = f"https://www.mustakbil.com{href}"

                is_remote = any(k in title.lower() or k in loc.lower() for k in ["remote", "online", "work from home"])

                postings.append(
                    JobPosting(
                        id=f"mustakbil_{job_id}",
                        title=title,
                        company=company,
                        location=f"{loc}, Pakistan" if "pakistan" not in loc.lower() else loc,
                        salary="Disclosed in Application",
                        url=full_url,
                        source="Mustakbil (Pakistan)",
                        description_snippet=f"Local technology opportunity in {loc}, Pakistan via Mustakbil. Hiring organization: {company}.",
                        is_remote=is_remote,
                        country="Pakistan"
                    )
                )

                if len(postings) >= fetch_depth:
                    break

        except Exception as err:
            logger.warning(f"Error fetching Mustakbil jobs from {url}: {err}")

    logger.info(f"Mustakbil: Fetched {len(postings)} local Pakistan positions.")
    return postings
