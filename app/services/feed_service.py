import asyncio
import json
import ssl
import websockets
import uuid
from typing import List, Literal
from app.core.config import settings
from app.services.upstox_auth import UpstoxAuthService
from app.db.redis import RedisClient

class FeedService:
    _websocket = None
    _is_running = False
    _task = None
    _subscriptions = set()
    
    # Protected keys - இவை எப்போதும் subscribed-ஆ இருக்கும், unsubscribe ஆகாது
    # Index keys are always protected from unsubscription
    _protected_keys = {
        "NSE_INDEX|Nifty 50",
        "NSE_INDEX|Nifty Bank",
        "NSE_INDEX|India VIX"
    }

    @classmethod
    async def get_authorized_url(cls):
        creds = await UpstoxAuthService.get_credentials()
        if not creds or not creds.get('access_token'):
            raise ValueError("Access token not found. Please login first.")
        
        access_token = creds['access_token']
        
        # Get authorized URL via API
        # Updated to V3 endpoint as per error UDAPI1153
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            if response.status_code != 200:
                raise RuntimeError(f"Failed to authorize feed: {response.text}")
            
            data = response.json()
            return data['data']['authorized_redirect_uri']

    @classmethod
    async def connect(cls):
        if cls._is_running:
            return {"message": "Feed already running"}

        try:
            ws_url = await cls.get_authorized_url()
            cls._is_running = True
            cls._task = asyncio.create_task(cls._run_loop(ws_url))
            return {"message": "Feed connecting..."}
        except Exception as e:
            cls._is_running = False
            raise e

    @classmethod
    async def disconnect(cls):
        cls._is_running = False
        if cls._websocket:
            await cls._websocket.close()
            cls._websocket = None
        if cls._task:
            cls._task.cancel()
            try:
                await cls._task
            except asyncio.CancelledError:
                pass
            cls._task = None
        return {"message": "Feed disconnected"}

    @classmethod
    async def subscribe(cls, instrument_keys: List[str], mode: Literal["full", "full_d30", "ltpc"]):
        if not cls._websocket or not cls._is_running:
            raise RuntimeError("WebSocket is not connected. Call /connect first.")
        
        # Filter out already subscribed keys
        new_keys = [key for key in instrument_keys if key not in cls._subscriptions]
        
        if not new_keys:
            return {"message": "All instruments are already subscribed"}
        
        # Construct subscription message
        payload = {
            "guid": str(uuid.uuid4()),
            "method": "sub",
            "data": {
                "mode": mode,
                "instrumentKeys": new_keys
            }
        }
        
        # Send as binary (UTF-8 encoded) as per Upstox requirements
        await cls._websocket.send(json.dumps(payload).encode('utf-8'))
        cls._subscriptions.update(new_keys)
        return {"message": f"Subscribed to {len(new_keys)} new instruments in {mode} mode"}

    @classmethod
    async def unsubscribe(cls, instrument_keys: List[str]):
        if not cls._websocket or not cls._is_running:
            raise RuntimeError("WebSocket is not connected.")
        
        payload = {
            "guid": str(uuid.uuid4()),
            "method": "unsub",
            "data": {
                "instrumentKeys": instrument_keys
            }
        }
        
        # Send as binary (UTF-8 encoded)
        await cls._websocket.send(json.dumps(payload).encode('utf-8'))
        cls._subscriptions.difference_update(instrument_keys)
        return {"message": f"Unsubscribed from {len(instrument_keys)} instruments"}

    @classmethod
    def get_subscriptions(cls) -> List[str]:
        return list(cls._subscriptions)

    @classmethod
    async def update_subscriptions(
        cls, 
        new_instrument_keys: List[str], 
        mode: Literal["full", "full_d30", "ltpc"] = "full"
    ) -> dict:
        """
        Dynamic subscription management: 
        - Subscribe to new keys that aren't currently subscribed
        - Unsubscribe from old keys that are no longer in the new list
        - PROTECTED: Index keys are never unsubscribed
        
        புதிய option keys வந்தா subscribe பண்ணும், 
        பழைய keys இல்லன்னா unsubscribe பண்ணும்.
        Index keys எப்போதும் protected - அவை unsubscribe ஆகாது!
        """
        if not cls._websocket or not cls._is_running:
            raise RuntimeError("WebSocket is not connected. Call /connect first.")
        
        new_keys_set = set(new_instrument_keys)
        current_keys = cls._subscriptions
        
        # DEBUG: Log current state
        print(f"DEBUG update_subscriptions:")
        print(f"  - Current subscriptions ({len(current_keys)}): {list(current_keys)}")
        print(f"  - New keys requested ({len(new_keys_set)}): {list(new_keys_set)}")
        
        # Keys to subscribe (in new but not in current)
        keys_to_subscribe = new_keys_set - current_keys
        
        # Keys to unsubscribe (in current but not in new)
        # IMPORTANT: Exclude protected keys (Index keys) from unsubscription
        keys_to_unsubscribe = (current_keys - new_keys_set) - cls._protected_keys
        
        result = {
            "subscribed": [],
            "unsubscribed": [],
            "already_subscribed": list(new_keys_set & current_keys),
            "protected_keys": list(cls._protected_keys & current_keys)  # Show which keys are protected
        }
        
        # Unsubscribe from old option keys first (NOT index keys)
        if keys_to_unsubscribe:
            unsub_payload = {
                "guid": str(uuid.uuid4()),
                "method": "unsub",
                "data": {
                    "instrumentKeys": list(keys_to_unsubscribe)
                }
            }
            await cls._websocket.send(json.dumps(unsub_payload).encode('utf-8'))
            cls._subscriptions.difference_update(keys_to_unsubscribe)
            result["unsubscribed"] = list(keys_to_unsubscribe)
            print(f"Unsubscribed from {len(keys_to_unsubscribe)} instruments: {list(keys_to_unsubscribe)}")
        
        # Subscribe to new keys
        if keys_to_subscribe:
            sub_payload = {
                "guid": str(uuid.uuid4()),
                "method": "sub",
                "data": {
                    "mode": mode,
                    "instrumentKeys": list(keys_to_subscribe)
                }
            }
            await cls._websocket.send(json.dumps(sub_payload).encode('utf-8'))
            cls._subscriptions.update(keys_to_subscribe)
            result["subscribed"] = list(keys_to_subscribe)
            print(f"Subscribed to {len(keys_to_subscribe)} instruments in {mode} mode: {list(keys_to_subscribe)}")
        
        result["current_subscriptions"] = list(cls._subscriptions)
        result["total_count"] = len(cls._subscriptions)
        
        return result

    @classmethod
    async def _run_loop(cls, ws_url: str):
        redis_client = RedisClient.get_pool()
        ssl_context = ssl.create_default_context()
        
        # Try to import Protobuf (User must place the file in app/proto/)
        try:
            from app.proto import MarketDataFeedV3_pb2 as MarketDataFeed_pb2
            from google.protobuf.json_format import MessageToDict
            HAS_PROTOBUF = True
        except ImportError:
            HAS_PROTOBUF = False
            print("Warning: MarketDataFeedV3_pb2 not found. Protobuf decoding disabled.")
        
        try:
            async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
                cls._websocket = websocket
                print("WebSocket Connected")
                
                async for message in websocket:
                    if not cls._is_running:
                        break
                    
                    try:
                        data_dict = {}
                        
                        if isinstance(message, bytes):
                            print(f"DEBUG: Received {len(message)} bytes")
                            # Binary -> Protobuf
                            if HAS_PROTOBUF:
                                feed_response = MarketDataFeed_pb2.FeedResponse()
                                feed_response.ParseFromString(message)
                                data_dict = MessageToDict(feed_response)
                            else:
                                print("Received binary data but Protobuf module missing.")
                                continue
                        else:
                            print(f"DEBUG: Received JSON: {message[:50]}...")
                            # Text -> JSON
                            data_dict = json.loads(message)
                        
                        # Publish to Redis
                        if data_dict:
                            msg_type = data_dict.get('type')
                            feeds = data_dict.get('feeds', {})
                            print(f"DEBUG: Decoded Message Type: {msg_type}")
                            if feeds:
                                print(f"DEBUG: Received updates for {len(feeds)} instruments: {list(feeds.keys())}")
                            else:
                                print("DEBUG: No feeds in message")
                                
                            print("DEBUG: Publishing to Redis stream 'market_feed'")
                            await redis_client.xadd("market_feed", {"data": json.dumps(data_dict)})
                        
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        
        except Exception as e:
            print(f"WebSocket connection error: {e}")
        finally:
            cls._is_running = False
            cls._websocket = None
            print("WebSocket Disconnected")
