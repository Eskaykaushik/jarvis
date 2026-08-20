from fastapi import APIRouter

from app.auth.deps import AuthenticatedUser
from app.models.schemas import EmailRequest, EmailResponse
from app.services.email import handle_email

router = APIRouter()


@router.post("/email/send", response_model=EmailResponse)
async def send_email(request: EmailRequest, user_id: AuthenticatedUser):
    return await handle_email(request)
