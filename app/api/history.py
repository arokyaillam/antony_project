from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["History Service"])

@router.get("/candles")
async def get_candles(
    instrument_key: str,
    interval: str,
    to_date: str,
    from_date: str
):
    """
    Get historical candle data for a single instrument.
    """
    try:
        data = await HistoryService.get_historical_candles(instrument_key, interval, to_date, from_date)
        # Convert to dict if it's an object
        if hasattr(data, 'to_dict'):
            return data.to_dict()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/candles/subscribed")
async def get_subscribed_candles(
    interval: str,
    to_date: str,
    from_date: str
):
    """
    Get historical candle data for ALL currently subscribed instruments.
    """
    try:
        data = await HistoryService.get_subscribed_history(interval, to_date, from_date)
        # Convert individual responses to dicts if needed
        serialized_data = {}
        for k, v in data.items():
            if hasattr(v, 'to_dict'):
                serialized_data[k] = v.to_dict()
            else:
                serialized_data[k] = v
        return serialized_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
