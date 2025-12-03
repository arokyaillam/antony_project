from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.instrument_service import InstrumentService

router = APIRouter(prefix="/instrument", tags=["Instrument Service"])

class OptionChainRequest(BaseModel):
    instrument_key: str
    expiry_date: str
    atm_strike: float

@router.post("/option-chain")
async def get_option_chain(request: OptionChainRequest):
    try:
        result = await InstrumentService.get_option_chain(
            request.instrument_key,
            request.expiry_date,
            request.atm_strike
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
