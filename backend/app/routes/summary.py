import logging

from fastapi import APIRouter, HTTPException

from app.auth.deps import AuthenticatedUser
from app.cache.redis_cache import RedisUnavailableError
from app.models.schemas import SummaryRequest, SummaryResponse
from app.services.summary import handle_summary

router = APIRouter()
logger = logging.getLogger(__name__)

_chain = None


def set_chain(chain):
    global _chain
    _chain = chain


@router.post("/summary", response_model=SummaryResponse)
async def summary(request: SummaryRequest, user_id: AuthenticatedUser):
    try:
        return await handle_summary(request, _chain, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RedisUnavailableError as e:
        logger.error("Summary unavailable: %s", e)
        raise HTTPException(status_code=503, detail="Cache service is unavailable. Please try again later.")
    except RuntimeError as e:
        logger.error("Summary failed: %s", e)
        raise HTTPException(status_code=503, detail="All providers failed. Please try again.")
    except Exception:
        logger.exception("Unexpected summary error")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
