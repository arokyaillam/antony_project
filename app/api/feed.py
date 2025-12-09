from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional
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

class UpdateSubscriptionsRequest(BaseModel):
    """Request model for update-subscriptions - mode is optional, defaults to 'full'"""
    instrument_keys: List[str]
    mode: Literal["full", "full_d30", "ltpc"] = "full"  # Optional with default

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

@router.post("/update-subscriptions")
async def update_subscriptions(request: UpdateSubscriptionsRequest):
    """
    Dynamic subscription management endpoint.
    Pass the new list of instrument keys - it will:
    1. Subscribe to new keys (not currently subscribed)
    2. Unsubscribe from old keys (not in the new list)
    
    இது ஒரே call-ல sub/unsub இரண்டையும் handle பண்ணும்.
    """
    try:
        result = await FeedService.update_subscriptions(
            request.instrument_keys, 
            request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_feed_status():
    try:
        is_connected = FeedService.is_connected()
        return {"connected": is_connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



