import os
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("JobIntegrationGateway")

# Initialize FastAPI App
app = FastAPI(
    title="Anser Nawaz Career & Job Discovery Gateway",
    description="Customized Job Aggregator & Application Assistant for Anser Nawaz (6+ Years Senior Full-Stack & Mobile Developer)",
    version="2.0.0"
)

# CORS Configuration
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ebazhanov.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular API Routers
from app.api.v1.routes_jobs import router as jobs_router
from app.api.v1.routes_tracker import router as tracker_router
from app.api.v1.routes_generate import router as generate_router
from app.api.v1.routes_email import router as email_router
from app.api.v1.routes_profiles import router as profiles_router

app.include_router(jobs_router)
app.include_router(tracker_router)
app.include_router(generate_router)
app.include_router(email_router)
app.include_router(profiles_router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "job-discovery-gateway-v2",
        "candidate": "Anser Nawaz",
        "experience": "6+ years"
    }

if __name__ == "__main__":
    from app.services.aggregator import aggregate_all_jobs

    async def run_cli_diagnostic():
        print("\n" + "=" * 65)
        print("🚀 RUNNING JOB AGGREGATION & MATCHING ENGINE DIAGNOSTIC")
        print("=" * 65)
        
        response = await aggregate_all_jobs(keyword="", location="Lahore", limit=10)
        print(f"\n📊 Retrieved {response.count} of {response.total_count} postings:")
        print(f"Categories Breakdown: {response.categories_count}")
        print(f"Providers Breakdown:  {response.providers_count}\n")

        for idx, job in enumerate(response.results, 1):
            print(f"{idx}. [{job.match_score}% MATCH] [{job.category}] {job.title}")
            print(f"   • Company:  {job.company}")
            print(f"   • Location: {job.location}")
            print(f"   • Source:   {job.source}")
            print(f"   • Salary:   {job.salary}")
            print(f"   • Seniority:{job.seniority_level}")
            if job.match_breakdown:
                print(f"   • Skills:   {', '.join(job.match_breakdown.matched_skills)}")
            print(f"   • URL:      {job.url}")
            print("-" * 65)

    asyncio.run(run_cli_diagnostic())