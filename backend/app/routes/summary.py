import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import SummaryRequest, SummaryResponse
from app.services.summary import handle_summary

router = APIRouter()
logger = logging.getLogger(__name__)

_chain = None


def set_chain(chain):
    global _chain
    _chain = chain


@router.post("/summary", response_model=SummaryResponse)
async def summary(request: SummaryRequest):
    try:
        return await handle_summary(request, _chain)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error("Summary failed: %s", e)
        raise HTTPException(status_code=503, detail="All providers failed. Please try again.")
    except Exception as e:
        logger.error("Summary error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
