"""
Order API Router
================

Regular order endpoints with Sandbox support.

Author: Antony HFT System
"""

from typing import List
from fastapi import APIRouter, HTTPException
from app.services.order_service import OrderService, OrderRequest, OrderModifyRequest

router = APIRouter(prefix="/order", tags=["Orders"])


@router.get("/mode")
async def get_order_mode():
    """
    Get Current Order Mode
    
    Returns whether orders are running in sandbox or live mode.
    """
    return {
        "sandbox_mode": OrderService.is_sandbox(),
        "message": "⚠️ SANDBOX MODE - No real money" if OrderService.is_sandbox() else "🔴 LIVE MODE - Real money"
    }


@router.post("/place")
async def place_order(request: OrderRequest):
    """
    Place Order
    
    ⚠️ Sandbox supported - check mode before trading
    
    Example:
    ```json
    {
        "quantity": 25,
        "product": "I",
        "validity": "DAY",
        "price": 0,
        "instrument_token": "NSE_FO|61755",
        "order_type": "MARKET",
        "transaction_type": "BUY"
    }
    ```
    """
    try:
        return await OrderService.place_order(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modify")
async def modify_order(request: OrderModifyRequest):
    """
    Modify Order
    
    ⚠️ Sandbox supported
    """
    try:
        return await OrderService.modify_order(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{order_id}")
async def cancel_order(order_id: str):
    """
    Cancel Order
    
    ⚠️ Sandbox supported
    """
    try:
        return await OrderService.cancel_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/place-multi")
async def place_multi_order(orders: List[OrderRequest]):
    """
    Place Multiple Orders (max 10)
    
    ⚠️ Sandbox supported
    """
    if len(orders) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 orders allowed")
    
    try:
        return await OrderService.place_multi_order(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
