"""
GTT Order Service - Upstox API v3 Integration
==============================================

Async service for GTT (Good Till Triggered) orders.
Place, Modify, Cancel, and Get GTT orders.

Author: Antony HFT System
"""

import httpx
from typing import Optional
from app.core.config import settings
from app.models.gtt import GTTPlaceRequest, GTTModifyRequest


class GTTService:
    """
    GTT Order Service
    
    Upstox API v3 GTT endpoints wrapper.
    Uses httpx for async HTTP calls.
    
    Endpoints:
        POST   /v3/order/gtt/place  - Place new GTT order
        PUT    /v3/order/gtt/modify - Modify existing order
        DELETE /v3/order/gtt/cancel - Cancel order
        GET    /v3/order/gtt        - Get order details
    """
    
    BASE_URL = "https://api.upstox.com/v3/order/gtt"
    
    @staticmethod
    def _get_headers() -> dict:
        """
        Get authorization headers
        
        Uses access token from settings/env
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.UPSTOX_ACCESS_TOKEN}"
        }
    
    @staticmethod
    async def place_order(request: GTTPlaceRequest) -> dict:
        """
        Place GTT Order
        
        Creates Entry + Target + StopLoss combo order.
        
        Args:
            request: GTT place order request
            
        Returns:
            API response with gtt_order_id
            
        Financial Logic:
            MULTIPLE GTT = ஒரே order-ல Entry, Target, SL set பண்ணலாம்
            Entry trigger ஆனவுடன் Target/SL active ஆகும்
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GTTService.BASE_URL}/place",
                headers=GTTService._get_headers(),
                json=request.model_dump()
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def modify_order(request: GTTModifyRequest) -> dict:
        """
        Modify GTT Order
        
        Update quantity, trigger prices, or trailing gap.
        
        Args:
            request: GTT modify request with gtt_order_id
            
        Returns:
            API response
            
        Financial Logic:
            Trailing SL: trailing_gap add பண்ணி modify பண்ணலாம்
            Price move ஆகும் போது SL auto adjust ஆகும்
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{GTTService.BASE_URL}/modify",
                headers=GTTService._get_headers(),
                json=request.model_dump()
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def cancel_order(gtt_order_id: str) -> dict:
        """
        Cancel GTT Order
        
        Args:
            gtt_order_id: Order ID to cancel
            
        Returns:
            API response
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="DELETE",
                url=f"{GTTService.BASE_URL}/cancel",
                headers=GTTService._get_headers(),
                json={"gtt_order_id": gtt_order_id}
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_order(gtt_order_id: str) -> dict:
        """
        Get GTT Order Details
        
        Args:
            gtt_order_id: Order ID to fetch
            
        Returns:
            Order details including status, rules, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GTTService.BASE_URL,
                headers=GTTService._get_headers(),
                params={"gtt_order_id": gtt_order_id}
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_all_orders() -> dict:
        """
        Get All GTT Orders
        
        Returns:
            List of all GTT orders for the user
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GTTService.BASE_URL,
                headers=GTTService._get_headers()
            )
            response.raise_for_status()
            return response.json()
