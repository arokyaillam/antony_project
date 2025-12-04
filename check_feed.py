import asyncio
import json
import ssl
import websockets
import uuid
from app.db.postgres import PostgresClient
from app.services.upstox_auth import UpstoxAuthService
from app.core.config import settings

# Import Protobuf
try:
    from app.proto import MarketDataFeedV3_pb2 as MarketDataFeed_pb2
    from google.protobuf.json_format import MessageToDict
    HAS_PROTOBUF = True
    print("Protobuf module loaded successfully.")
except ImportError:
    HAS_PROTOBUF = False
    print("Warning: MarketDataFeedV3_pb2 not found. Protobuf decoding disabled.")

async def main():
    print("Initializing Postgres...")
    await PostgresClient.create_pool()
    
    try:
        print("Getting credentials...")
        creds = await UpstoxAuthService.get_credentials()
        if not creds or not creds.get('access_token'):
            print("Error: Access token not found in DB. Please login via the app first.")
            return

        access_token = creds['access_token']
        print(f"Access Token found (starts with): {access_token[:10]}...")

        # Get authorized URL
        import httpx
        print("Getting authorized WebSocket URL...")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            if response.status_code != 200:
                print(f"Failed to authorize feed: {response.text}")
                return
            
            data = response.json()
            ws_url = data['data']['authorized_redirect_uri']
            print(f"Authorized URL: {ws_url}")

        # Connect
        ssl_context = ssl.create_default_context()
        print("Connecting to WebSocket...")
        async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
            print("WebSocket Connected!")

            # Subscribe
            instrument_keys = ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"]
            payload = {
                "guid": str(uuid.uuid4()),
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": instrument_keys
                }
            }
            print(f"Subscribing to: {instrument_keys} in full mode")
            print(f"Payload: {json.dumps(payload)}")
            # Convert data to binary and send over WebSocket (matching user sample)
            binary_data = json.dumps(payload).encode('utf-8')
            await websocket.send(binary_data)

            print("Listening for messages...")
            while True:
                message = await websocket.recv()
                
                if isinstance(message, bytes):
                    print(f"\nReceived BINARY message ({len(message)} bytes)")
                    if HAS_PROTOBUF:
                        try:
                            feed_response = MarketDataFeed_pb2.FeedResponse()
                            feed_response.ParseFromString(message)
                            data_dict = MessageToDict(feed_response)
                            
                            msg_type = data_dict.get('type')
                            feeds = data_dict.get('feeds', {})
                            
                            print(f"Decoded Type: {msg_type}")
                            if feeds:
                                print(f"Feeds: {list(feeds.keys())}")
                                # Print first feed details
                                first_key = list(feeds.keys())[0]
                                print(f"Sample Data ({first_key}): {feeds[first_key]}")
                            else:
                                print("No feeds in message")
                                print(f"Full Data: {data_dict}")
                                
                        except Exception as e:
                            print(f"Error decoding protobuf: {e}")
                    else:
                        print("Protobuf not available, cannot decode.")
                else:
                    print(f"\nReceived TEXT message: {message}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await PostgresClient.close_pool()

if __name__ == "__main__":
    asyncio.run(main())
