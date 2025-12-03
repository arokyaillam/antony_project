import asyncio
import json
import random
from app.db.redis import RedisClient

async def mock_data_generator():
    print("Starting Mock Data Generator...")
    redis = await RedisClient.get_pool()
    
    instruments = ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_EQ|RELIANCE"]
    
    try:
        while True:
            data = {
                "instrument_key": random.choice(instruments),
                "ltp": round(random.uniform(10000, 25000), 2),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Push to Redis Stream
            await redis.xadd("market_feed", {"data": json.dumps(data)})
            print(f"Pushed: {data}")
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await RedisClient.close_pool()

if __name__ == "__main__":
    # Need to setup config to load env vars for Redis URL
    from app.core.config import settings
    asyncio.run(mock_data_generator())
