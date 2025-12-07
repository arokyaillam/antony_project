"""
GTT Order API Router
====================

FastAPI endpoints for GTT (Good Till Triggered) orders.
Place, Modify, Cancel, and Get GTT orders.

Author: Antony HFT System
"""

from fastapi import APIRouter, HTTPException
from app.models.gtt import GTTPlaceRequest, GTTModifyRequest, GTTCancelRequest
from app.services.gtt_service import GTTService

router = APIRouter(prefix="/gtt", tags=["GTT Orders"])


@router.post("/place")
async def place_gtt_order(request: GTTPlaceRequest):
    """
    Place GTT Order
    
    Creates a GTT order with Entry + Target + Stop-Loss.
    
    Example Request:
    ```json
    {
        "type": "MULTIPLE",
        "quantity": 25,
        "product": "I",
        "rules": [
            {"strategy": "ENTRY", "trigger_type": "ABOVE", "trigger_price": 200},
            {"strategy": "TARGET", "trigger_type": "IMMEDIATE", "trigger_price": 220},
            {"strategy": "STOPLOSS", "trigger_type": "IMMEDIATE", "trigger_price": 190}
        ],
        "instrument_token": "NSE_FO|61755",
        "transaction_type": "BUY"
    }
    ```
    
    With Trailing SL:
    ```json
    {
        "strategy": "STOPLOSS",
        "trigger_type": "IMMEDIATE", 
        "trigger_price": 190,
        "trailing_gap": 5
    }
    ```
    """
    try:
        result = await GTTService.place_order(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modify")
async def modify_gtt_order(request: GTTModifyRequest):
    """
    Modify GTT Order
    
    Update quantity, trigger prices, or add trailing SL.
    
    Example Request:
    ```json
    {
        "gtt_order_id": "GTT-C25280200137522",
        "type": "MULTIPLE",
        "quantity": 50,
        "rules": [
            {"strategy": "ENTRY", "trigger_type": "ABOVE", "trigger_price": 210},
            {"strategy": "TARGET", "trigger_type": "IMMEDIATE", "trigger_price": 230},
            {"strategy": "STOPLOSS", "trigger_type": "IMMEDIATE", "trigger_price": 195, "trailing_gap": 5}
        ]
    }
    ```
    """
    try:
        result = await GTTService.modify_order(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel")
async def cancel_gtt_order(request: GTTCancelRequest):
    """
    Cancel GTT Order
    
    Example Request:
    ```json
    {
        "gtt_order_id": "GTT-C25280200137522"
    }
    ```
    """
    try:
        result = await GTTService.cancel_order(request.gtt_order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{gtt_order_id}")
async def get_gtt_order(gtt_order_id: str):
    """
    Get GTT Order Details
    
    Returns order status, rules, and execution details.
    """
    try:
        result = await GTTService.get_order(gtt_order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_all_gtt_orders():
    """
    Get All GTT Orders
    
    Returns list of all GTT orders for the authenticated user.
    """
    try:
        result = await GTTService.get_all_orders()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
