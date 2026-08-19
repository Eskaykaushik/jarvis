from fastapi import APIRouter

from app.models.schemas import SummaryRequest, SummaryResponse
from app.services.summary import handle_summary

router = APIRouter()

_chain = None


def set_chain(chain):
    global _chain
    _chain = chain


@router.post("/summary", response_model=SummaryResponse)
async def summary(request: SummaryRequest):
    return await handle_summary(request, _chain)
