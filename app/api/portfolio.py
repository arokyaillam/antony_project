"""
Portfolio API Router
====================

Funds, Positions, Trades, OrderBook endpoints.

Author: Antony HFT System
"""

from fastapi import APIRouter, HTTPException, Query
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


# ═══════════════════════════════════════════════════════════════════════════════
# FUNDS & MARGIN
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/funds")
async def get_funds(segment: str = Query("SEC", description="SEC=Equity, COM=Commodity")):
    """
    Get Funds and Margin
    
    Returns available margin, used margin for order placement validation.
    
    Response:
    ```json
    {
        "available_margin": 50000,
        "used_margin": 10000,
        "payin_amount": 0
    }
    ```
    """
    try:
        return await PortfolioService.get_funds_and_margin(segment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/positions")
async def get_positions():
    """
    Get Intraday Positions
    
    Returns all open positions with real-time P&L.
    
    Response:
    ```json
    {
        "data": [
            {
                "instrument_token": "NSE_FO|61755",
                "quantity": 25,
                "average_price": 200,
                "ltp": 210,
                "pnl": 250
            }
        ]
    }
    ```
    """
    try:
        return await PortfolioService.get_positions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings")
async def get_holdings():
    """
    Get Long-term Holdings (Delivery)
    
    Returns all delivery holdings.
    """
    try:
        return await PortfolioService.get_holdings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TRADES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/trades")
async def get_trades():
    """
    Get Today's Trades
    
    Returns all executed trades for the day.
    """
    try:
        return await PortfolioService.get_trades()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{order_id}")
async def get_trades_by_order(order_id: str):
    """
    Get Trades for specific Order
    """
    try:
        return await PortfolioService.get_trades_by_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER BOOK
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/orders")
async def get_order_book():
    """
    Get Order Book
    
    Returns all orders - pending, complete, rejected.
    """
    try:
        return await PortfolioService.get_order_book()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_details(order_id: str):
    """
    Get Order Details
    """
    try:
        return await PortfolioService.get_order_details(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/history")
async def get_order_history(order_id: str):
    """
    Get Order History (status changes)
    """
    try:
        return await PortfolioService.get_order_history(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
