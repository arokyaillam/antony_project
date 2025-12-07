"""
Order Service - Upstox API v3
=============================

Regular order placement (not GTT).
Supports Sandbox mode for testing.
Token fetched from DB.

Author: Antony HFT System
"""

import httpx
from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.upstox_auth import UpstoxAuthService


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderRequest(BaseModel):
    """
    Order Place Request
    
    https://upstox.com/developer/api-documentation/v3/place-order
    """
    quantity: int = Field(..., gt=0, description="Order quantity")
    product: Literal["I", "D"] = Field("I", description="I=Intraday, D=Delivery")
    validity: Literal["DAY", "IOC"] = Field("DAY", description="Order validity")
    price: float = Field(0, description="Price (0 for market order)")
    instrument_token: str = Field(..., description="Instrument key")
    order_type: Literal["MARKET", "LIMIT", "SL", "SL-M"] = Field("MARKET")
    transaction_type: Literal["BUY", "SELL"] = Field(...)
    disclosed_quantity: int = Field(0, description="Disclosed quantity")
    trigger_price: float = Field(0, description="Trigger price for SL orders")
    is_amo: bool = Field(False, description="After Market Order")


class OrderModifyRequest(BaseModel):
    """Order Modify Request"""
    order_id: str = Field(..., description="Order ID to modify")
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None)
    order_type: Optional[Literal["MARKET", "LIMIT", "SL", "SL-M"]] = Field(None)
    trigger_price: Optional[float] = Field(None)
    validity: Optional[Literal["DAY", "IOC"]] = Field(None)


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class OrderService:
    """
    Order Service
    
    Regular order operations with Sandbox support.
    Token is fetched from DB (not .env).
    
    Sandbox Mode:
        UPSTOX_SANDBOX_MODE=true → Uses sandbox token
        Real money risk இல்ல, testing-க்கு use பண்ணலாம்
    
    Sandbox Enabled APIs:
        - Place Order
        - Modify Order
        - Cancel Order
    """
    
    BASE_URL = "https://api.upstox.com/v3/order"
    
    @staticmethod
    async def _get_headers() -> dict:
        """Get headers with token from DB (or sandbox token if sandbox mode)"""
        if settings.UPSTOX_SANDBOX_MODE and settings.UPSTOX_SANDBOX_TOKEN:
            token = settings.UPSTOX_SANDBOX_TOKEN
        else:
            token = await UpstoxAuthService.get_access_token()
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    @staticmethod
    def is_sandbox() -> bool:
        """Check if running in sandbox mode"""
        return settings.UPSTOX_SANDBOX_MODE
    
    @staticmethod
    async def place_order(request: OrderRequest) -> dict:
        """
        Place Order
        
        Sandbox supported ✓
        
        Args:
            request: Order details
            
        Returns:
            Order ID and status
            
        Financial Logic:
            MARKET order = Instant execution at current price
            LIMIT order = Execute only at specified price
            SL order = Stop-loss trigger
        """
        headers = await OrderService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OrderService.BASE_URL}/place",
                headers=headers,
                json=request.model_dump()
            )
            response.raise_for_status()
            result = response.json()
            
            # Add sandbox indicator
            result["sandbox_mode"] = OrderService.is_sandbox()
            return result
    
    @staticmethod
    async def modify_order(request: OrderModifyRequest) -> dict:
        """
        Modify Order
        
        Sandbox supported ✓
        """
        # Build payload with only provided fields
        payload = {"order_id": request.order_id}
        if request.quantity:
            payload["quantity"] = request.quantity
        if request.price:
            payload["price"] = request.price
        if request.order_type:
            payload["order_type"] = request.order_type
        if request.trigger_price:
            payload["trigger_price"] = request.trigger_price
        if request.validity:
            payload["validity"] = request.validity
            
        headers = await OrderService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{OrderService.BASE_URL}/modify",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            result["sandbox_mode"] = OrderService.is_sandbox()
            return result
    
    @staticmethod
    async def cancel_order(order_id: str) -> dict:
        """
        Cancel Order
        
        Sandbox supported ✓
        """
        headers = await OrderService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{OrderService.BASE_URL}/cancel",
                headers=headers,
                params={"order_id": order_id}
            )
            response.raise_for_status()
            result = response.json()
            result["sandbox_mode"] = OrderService.is_sandbox()
            return result
    
    @staticmethod
    async def place_multi_order(orders: list[OrderRequest]) -> dict:
        """
        Place Multiple Orders
        
        Sandbox supported ✓
        Max 10 orders at once
        """
        headers = await OrderService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OrderService.BASE_URL}/multi/place",
                headers=headers,
                json=[o.model_dump() for o in orders]
            )
            response.raise_for_status()
            result = response.json()
            result["sandbox_mode"] = OrderService.is_sandbox()
            return result
