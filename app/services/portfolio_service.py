"""
Portfolio Service - Upstox API v2
=================================

Funds, Positions, Trades, OrderBook APIs.
All async using httpx. Token fetched from DB.

Author: Antony HFT System
"""

import httpx
from typing import Optional, Literal
from app.services.upstox_auth import UpstoxAuthService


class PortfolioService:
    """
    Portfolio Service
    
    Upstox User/Portfolio API endpoints.
    Token is fetched from DB (not .env).
    
    Endpoints:
        GET /user/get-funds-and-margin      - Funds & Margin
        GET /portfolio/short-term-positions - Intraday Positions
        GET /portfolio/long-term-holdings   - Delivery Holdings
        GET /order/trades                   - Trade History
        GET /order/retrieve-all             - Order Book
    """
    
    BASE_URL = "https://api.upstox.com/v2"
    
    @staticmethod
    async def _get_headers() -> dict:
        """Get headers with token from DB"""
        token = await UpstoxAuthService.get_access_token()
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FUNDS & MARGIN
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def get_funds_and_margin(segment: str = "SEC") -> dict:
        """
        Get Funds and Margin
        
        Args:
            segment: SEC (Equity), COM (Commodity)
            
        Returns:
            Available margin, used margin, etc.
            
        Financial Logic:
            Order place பண்ணும் முன் available_margin check பண்ணணும்.
            used_margin < available_margin confirm பண்ணணும்.
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/user/get-funds-and-margin",
                headers=headers,
                params={"segment": segment}
            )
            response.raise_for_status()
            return response.json()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # POSITIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def get_positions() -> dict:
        """
        Get Intraday Positions
        
        Returns:
            All open positions with P&L
            
        Financial Logic:
            quantity > 0 = Long position
            quantity < 0 = Short position
            pnl = (ltp - average_price) * quantity
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/portfolio/short-term-positions",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_holdings() -> dict:
        """
        Get Long-term Holdings (Delivery)
        
        Returns:
            All delivery holdings
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/portfolio/long-term-holdings",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRADES
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def get_trades() -> dict:
        """
        Get Today's Trades
        
        Returns:
            All executed trades for the day
            
        Financial Logic:
            Trade = Order execute ஆன record
            GTT trigger ஆனதும் இங்கே வரும்
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/order/trades",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_trades_by_order(order_id: str) -> dict:
        """
        Get Trades for specific Order
        
        Args:
            order_id: Order ID
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/order/trades",
                headers=headers,
                params={"order_id": order_id}
            )
            response.raise_for_status()
            return response.json()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ORDER BOOK
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def get_order_book() -> dict:
        """
        Get Order Book
        
        Returns:
            All orders (pending, complete, rejected)
            
        Financial Logic:
            status = open/complete/rejected/cancelled
            GTT orders pending இருந்தா trigger ஆகல
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/order/retrieve-all",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_order_details(order_id: str) -> dict:
        """
        Get Order Details
        
        Args:
            order_id: Order ID
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/order/details",
                headers=headers,
                params={"order_id": order_id}
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_order_history(order_id: str) -> dict:
        """
        Get Order History (status changes)
        
        Args:
            order_id: Order ID
        """
        headers = await PortfolioService._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PortfolioService.BASE_URL}/order/history",
                headers=headers,
                params={"order_id": order_id}
            )
            response.raise_for_status()
            return response.json()
