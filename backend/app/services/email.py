import logging

import resend

from app.config import settings
from app.models.schemas import EmailRequest, EmailResponse

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


async def handle_email(request: EmailRequest) -> EmailResponse:
    params = {
        "from": settings.email_from,
        "to": [request.to],
        "subject": request.subject,
        "text": request.body,
    }

    try:
        result = resend.Emails.send(params)
        logger.info("Email sent to %s: %s", request.to, result.get("id", ""))
        return EmailResponse(
            sent=True,
            message_id=result.get("id", ""),
        )
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return EmailResponse(sent=False, message_id="")
