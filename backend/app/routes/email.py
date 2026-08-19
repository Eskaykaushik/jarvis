from fastapi import APIRouter

from app.models.schemas import EmailRequest, EmailResponse
from app.services.email import handle_email

router = APIRouter()


@router.post("/email/send", response_model=EmailResponse)
async def send_email(request: EmailRequest):
    return await handle_email(request)
