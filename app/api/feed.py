from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Literal
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["Market Data Feed"])

class SubscribeRequest(BaseModel):
    instrument_keys: List[str]
    mode: Literal["full", "full_d30", "ltpc"]

    @field_validator('mode', mode='before')
    @classmethod
    def normalize_mode(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

@router.post("/connect")
async def connect_feed():
    try:
        result = await FeedService.connect()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect_feed():
    try:
        result = await FeedService.disconnect()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe_feed(request: SubscribeRequest):
    try:
        result = await FeedService.subscribe(request.instrument_keys, request.mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe")
async def unsubscribe_feed(request: SubscribeRequest):
    # Reusing SubscribeRequest as it has instrument_keys. Mode is ignored.
    try:
        result = await FeedService.unsubscribe(request.instrument_keys)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscriptions")
async def get_subscriptions():
    try:
        subscriptions = FeedService.get_subscriptions()
        return {"count": len(subscriptions), "subscriptions": subscriptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
