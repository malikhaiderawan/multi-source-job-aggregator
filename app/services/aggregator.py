import asyncio
import time
import logging
from typing import List, Optional, Dict
from app.clients.base_client import create_async_client
from app.clients.jooble_client import fetch_jooble_jobs
from app.clients.remotive_client import fetch_remotive_jobs
from app.clients.jobicy_client import fetch_jobicy_jobs
from app.clients.arbeitnow_client import fetch_arbeitnow_jobs
from app.clients.wwr_client import fetch_wwr_jobs
from app.clients.mustakbil_client import fetch_mustakbil_jobs
from app.models.job import JobPosting, JobListResponse
from app.services.deduplicator import deduplicate_jobs
from app.services.matching_engine import enrich_job_posting
from app.storage.tracker_store import TRACKER_STORE
from app.storage.profile_store import PROFILE_STORE
from app.storage.linkedin_job_store import LINKEDIN_JOB_STORE

logger = logging.getLogger("AggregatorService")

async def aggregate_all_jobs(
    keyword: str = "",
    location: str = "",
    category: str = "All",
    eligibility: Optional[str] = None,
    min_score: int = 0,
    limit: int = 50,
    candidate_id: Optional[str] = None
) -> JobListResponse:
    """
    Asynchronously queries all permitted providers, normalizes results,
    deduplicates, enriches with the selected candidate's match score and location eligibility,
    and returns sorted postings.
    """
    start_time = time.time()
    
    # Resolve active candidate and profile for candidate-specific scoring and tracking
    if candidate_id:
        target_profile = PROFILE_STORE.get_profile(candidate_id) or PROFILE_STORE.get_active_profile()
        active_candidate_id = candidate_id
    else:
        active_meta = PROFILE_STORE.get_active_profile_meta()
        active_candidate_id = active_meta.get("id", "anser_nawaz")
        target_profile = PROFILE_STORE.get_active_profile()

    logger.info(f"Aggregating jobs for candidate '{active_candidate_id}': keyword='{keyword}', location='{location}', category='{category}', eligibility='{eligibility}'")

    async with create_async_client() as client:
        # Dedicated query planning covering Anser Nawaz's verified roles:
        # Full-stack, Frontend, Backend, and Mobile (React Native / Flutter / iOS / Android)
        tasks = []
        if category == "Mobile":
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "react native", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "flutter", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "mobile", category="software-dev", fetch_depth=40))
            tasks.append(fetch_arbeitnow_jobs(client, search_query=keyword or "mobile", fetch_depth=50))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="react native", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="ios", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="flutter", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="android", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query=keyword or "mobile", page=2, fetch_depth=50))
            tasks.append(fetch_wwr_jobs(client, category="Programming", fetch_depth=100))
            tasks.append(fetch_wwr_jobs(client, category="Full-stack", fetch_depth=100))
            tasks.append(fetch_jobicy_jobs(client, tag="dev", fetch_depth=40))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Mobile Developer React Native Flutter", location=location or "Lahore", fetch_depth=20))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "React Native Remote", location="", fetch_depth=25))
        elif category == "Frontend":
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "react", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "frontend", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "next.js", category="software-dev", fetch_depth=40))
            tasks.append(fetch_arbeitnow_jobs(client, search_query=keyword or "frontend", fetch_depth=50))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="react", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="next.js", fetch_depth=30))
            tasks.append(fetch_wwr_jobs(client, category="Frontend", fetch_depth=100))
            tasks.append(fetch_jobicy_jobs(client, tag="dev", fetch_depth=30))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Frontend React Next.js Developer", location=location or "Lahore", fetch_depth=20))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "React Next.js Developer Remote", location="", fetch_depth=25))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Web Developer Remote", location="", fetch_depth=25))
        elif category == "Backend":
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "node", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "backend", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "python", category="software-dev", fetch_depth=40))
            tasks.append(fetch_arbeitnow_jobs(client, search_query=keyword or "backend", fetch_depth=50))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="node.js", fetch_depth=30))
            tasks.append(fetch_wwr_jobs(client, category="Backend", fetch_depth=100))
            tasks.append(fetch_jobicy_jobs(client, tag="dev", fetch_depth=30))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Backend Node.js Python Developer", location=location or "Lahore", fetch_depth=20))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Node.js FastAPI Remote", location="", fetch_depth=25))
        else:  # "Full-stack" or "All"
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "full stack", category="software-dev", fetch_depth=40))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "react", category="software-dev", fetch_depth=30))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "react native", category="software-dev", fetch_depth=30))
            tasks.append(fetch_remotive_jobs(client, search_query=keyword or "node", category="software-dev", fetch_depth=30))
            tasks.append(fetch_jobicy_jobs(client, tag="dev", fetch_depth=50))
            tasks.append(fetch_arbeitnow_jobs(client, search_query=keyword, fetch_depth=50))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="mobile", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, search_query="react", fetch_depth=30))
            tasks.append(fetch_arbeitnow_jobs(client, page=2, search_query=keyword, fetch_depth=50))
            tasks.append(fetch_wwr_jobs(client, category="Full-stack", fetch_depth=100))
            tasks.append(fetch_wwr_jobs(client, category="Programming", fetch_depth=100))
            tasks.append(fetch_wwr_jobs(client, category="Frontend", fetch_depth=100))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Senior Full Stack Developer", location=location or "Lahore", fetch_depth=20))
            tasks.append(fetch_jooble_jobs(client, keywords=keyword or "Senior Full Stack Developer Remote", location="", fetch_depth=25))
            tasks.append(fetch_jooble_jobs(client, keywords="React Native Remote", location="", fetch_depth=20))
            tasks.append(fetch_jooble_jobs(client, keywords="Web Developer Remote", location="", fetch_depth=20))

        # Local Pakistan / Lahore IT portal (Mustakbil)
        tasks.append(fetch_mustakbil_jobs(client, location=location or "Lahore", fetch_depth=35))

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_postings: List[JobPosting] = []
    for res in batch_results:
        if isinstance(res, list):
            raw_postings.extend(res)
        elif isinstance(res, Exception):
            logger.error(f"Provider task encountered exception: {res}")

    # Include verified ingested LinkedIn Job Alert postings
    stored_linkedin_jobs = LINKEDIN_JOB_STORE.get_all_jobs()
    if stored_linkedin_jobs:
        raw_postings.extend(stored_linkedin_jobs)

    # 1. Deduplicate
    unique_postings = deduplicate_jobs(raw_postings)

    # 2. Enrich and Score against candidate Profile
    enriched_postings: List[JobPosting] = []
    
    # Retrieve current tracked applications scoped strictly to the selected candidate
    tracked_apps = TRACKER_STORE.list_applications(candidate_id=active_candidate_id)
    tracked_map = {item.job.id: item.status for item in tracked_apps if item.job and item.job.id}

    for job in unique_postings:
        enriched = enrich_job_posting(job, profile=target_profile)
        # Attach tracker status if tracked by this candidate
        if enriched.id and enriched.id in tracked_map:
            enriched.application_status = tracked_map[enriched.id]
        enriched_postings.append(enriched)

    # 3. Calculate category facet counts across all postings matching keyword, location, min_score, and eligibility
    # This prevents the category facet counts from collapsing/disappearing when a specific category is active.
    categories_facet: Dict[str, int] = {}
    for job in enriched_postings:
        # Check eligibility filter
        if eligibility and eligibility != "all":
            if eligibility == "lahore_local" and job.location_eligibility not in ["lahore_onsite", "lahore_hybrid"]:
                continue
            elif eligibility == "pakistan_all" and job.location_eligibility not in ["lahore_onsite", "lahore_hybrid", "pakistan_remote", "pakistan_onsite", "pakistan_hybrid"]:
                continue
            elif eligibility == "worldwide_remote" and job.location_eligibility != "worldwide_remote":
                continue
            elif eligibility == "remote_eligible" and job.location_eligibility not in ["worldwide_remote", "pakistan_remote"]:
                continue
            elif eligibility == "eligibility_unknown" and job.location_eligibility != "eligibility_unknown":
                continue
            elif job.location_eligibility != eligibility:
                continue

        # Check location filter
        if location and location.strip():
            loc_q = location.lower().strip()
            job_loc = job.location.lower()
            if loc_q in ["lahore", "pakistan"]:
                if job.location_eligibility not in ["lahore_onsite", "lahore_hybrid", "pakistan_remote", "pakistan_onsite", "pakistan_hybrid"]:
                    continue
            elif loc_q in ["remote", "worldwide"]:
                if job.location_eligibility not in ["worldwide_remote", "pakistan_remote"]:
                    continue
            elif loc_q not in job_loc:
                continue

        # Check min score filter
        if min_score > 0 and job.match_score < min_score:
            continue

        # Check keyword filter
        if keyword and keyword.strip():
            kw = keyword.lower().strip()
            searchable = f"{job.title} {job.company} {job.description_snippet} {' '.join(job.tags)}".lower()
            if kw not in searchable:
                continue

        cat_name = job.category or "Full-stack"
        categories_facet[cat_name] = categories_facet.get(cat_name, 0) + 1

    categories_facet["All"] = sum(categories_facet.values())

    # 4. Apply Filters to produce result set
    filtered_postings: List[JobPosting] = []
    for job in enriched_postings:
        # Category filter
        if category and category != "All" and job.category != category:
            continue

        # Explicit location eligibility filter if provided
        if eligibility and eligibility != "all":
            if eligibility == "lahore_local":
                if job.location_eligibility not in ["lahore_onsite", "lahore_hybrid"]:
                    continue
            elif eligibility == "pakistan_all":
                if job.location_eligibility not in ["lahore_onsite", "lahore_hybrid", "pakistan_remote", "pakistan_onsite", "pakistan_hybrid"]:
                    continue
            elif eligibility == "worldwide_remote":
                if job.location_eligibility != "worldwide_remote":
                    continue
            elif eligibility == "remote_eligible":
                if job.location_eligibility not in ["worldwide_remote", "pakistan_remote"]:
                    continue
            elif eligibility == "eligibility_unknown":
                if job.location_eligibility != "eligibility_unknown":
                    continue
            elif job.location_eligibility != eligibility:
                continue

        # Location text filter
        if location and location.strip():
            loc_q = location.lower().strip()
            job_loc = job.location.lower()
            if loc_q in ["lahore", "pakistan"]:
                if job.location_eligibility not in [
                    "lahore_onsite",
                    "lahore_hybrid",
                    "pakistan_remote",
                    "pakistan_onsite",
                    "pakistan_hybrid"
                ]:
                    continue
            elif loc_q in ["remote", "worldwide"]:
                if job.location_eligibility not in ["worldwide_remote", "pakistan_remote"]:
                    continue
            else:
                if loc_q not in job_loc:
                    continue

        # Min match score filter
        if min_score > 0 and job.match_score < min_score:
            continue

        # Keyword filter if specified
        if keyword and keyword.strip():
            kw = keyword.lower().strip()
            searchable = f"{job.title} {job.company} {job.description_snippet} {' '.join(job.tags)}".lower()
            if kw not in searchable:
                continue

        filtered_postings.append(job)

    # 5. Sort by Match Score Descending (Highest relevance first)
    filtered_postings.sort(key=lambda j: j.match_score, reverse=True)

    # Compute breakdowns for UI badges
    providers_count: Dict[str, int] = {}
    eligibility_count: Dict[str, int] = {}
    for j in filtered_postings:
        providers_count[j.source] = providers_count.get(j.source, 0) + 1
        eligibility_count[j.location_eligibility] = eligibility_count.get(j.location_eligibility, 0) + 1

    final_results = filtered_postings[:limit]
    elapsed = round((time.time() - start_time) * 1000, 2)
    logger.info(f"Aggregator finished: returned {len(final_results)} of {len(filtered_postings)} jobs in {elapsed}ms")

    return JobListResponse(
        total_count=len(filtered_postings),
        count=len(final_results),
        results=final_results,
        categories_count=categories_facet,
        providers_count=providers_count,
        eligibility_count=eligibility_count
    )
