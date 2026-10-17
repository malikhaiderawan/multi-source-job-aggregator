from fastapi import APIRouter
from app.models.job import ApplicationGenerateRequest, ApplicationGenerateResponse
from app.services.tailored_generator import generate_tailored_application

router = APIRouter(prefix="/api/v1/generate", tags=["Application Generator"])

@router.post("/application", response_model=ApplicationGenerateResponse)
async def generate_application(payload: ApplicationGenerateRequest):
    """
    Generates tailored CV suggestions, customized cover letter, and recruiter email
    drawn directly and factually from Anser Nawaz's 6+ years of verified development experience.
    """
    return generate_tailored_application(payload.job, tone=payload.custom_tone or "professional")
