"""
Order Update Stream Service
============================

Upstox Portfolio WebSocket stream for real-time order updates.
GTT trigger, execution, rejection notifications.

Author: Antony HFT System
"""

import ssl
import json
import asyncio
import logging
import websockets
import upstox_client
from typing import AsyncGenerator, Optional, Callable
from app.services.upstox_auth import UpstoxAuthService

logger = logging.getLogger(__name__)


class OrderUpdateService:
    """
    Order Update WebSocket Service
    
    Connects to Upstox Portfolio Stream and yields order updates.
    
    Usage:
        async for update in OrderUpdateService.stream_updates():
            print(update)
    
    Financial Logic:
        GTT order execute ஆனவுடன் இங்கே notification வரும்.
        Order status: PENDING → OPEN → COMPLETE / REJECTED
    """
    
    _running: bool = False
    _websocket = None
    
    @staticmethod
    async def _get_configuration() -> upstox_client.Configuration:
        """Get Upstox SDK configuration with access token from DB"""
        configuration = upstox_client.Configuration()
        # Token from database, not env file!
        configuration.access_token = await UpstoxAuthService.get_access_token()
        return configuration
    
    @staticmethod
    async def _get_authorize_url() -> str:
        """
        Get authorized WebSocket URL from Upstox API
        
        Returns:
            Authorized redirect URI for WebSocket connection
        """
        configuration = await OrderUpdateService._get_configuration()
        api_instance = upstox_client.WebsocketApi(
            upstox_client.ApiClient(configuration)
        )
        
        response = api_instance.get_portfolio_stream_feed_authorize(
            api_version='2.0'
        )
        
        return response.data.authorized_redirect_uri
    
    @staticmethod
    async def stream_updates() -> AsyncGenerator[dict, None]:
        """
        Stream order updates via WebSocket
        
        Yields:
            Order update dict with status, order_id, etc.
        
        Example output:
            {
                "order_id": "123456",
                "status": "complete",
                "transaction_type": "BUY",
                "quantity": 25,
                "price": 200
            }
        """
        # SSL context (disable verification for Upstox)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        OrderUpdateService._running = True
        
        while OrderUpdateService._running:
            try:
                # Get fresh authorized URL (using token from DB)
                ws_url = await OrderUpdateService._get_authorize_url()
                logger.info(f"Connecting to order update stream...")
                
                async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
                    OrderUpdateService._websocket = websocket
                    logger.info("Order update stream connected")
                    
                    while OrderUpdateService._running:
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(), 
                                timeout=30.0
                            )
                            
                            # Parse and yield
                            try:
                                data = json.loads(message)
                                yield data
                            except json.JSONDecodeError:
                                yield {"raw": message}
                                
                        except asyncio.TimeoutError:
                            # Send ping to keep alive
                            try:
                                await websocket.ping()
                            except Exception:
                                break
                                
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket closed: {e}, reconnecting...")
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Order stream error: {e}")
                await asyncio.sleep(5)
        
        logger.info("Order update stream stopped")
    
    @staticmethod
    async def stop():
        """Stop the order update stream"""
        OrderUpdateService._running = False
        if OrderUpdateService._websocket:
            try:
                await OrderUpdateService._websocket.close()
            except Exception:
                pass
