import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db.redis import RedisClient

router = APIRouter(prefix="/stream", tags=["Live Stream"])

async def event_generator():
    redis = RedisClient.get_pool()
    last_id = "$"  # Start reading from new messages only
    
    try:
        while True:
            try:
                # Read new messages from the stream
                streams = await redis.xread(
                    streams={"market_feed": last_id},
                    count=1,
                    block=1000  # Block for 1 second max
                )
                
                if not streams:
                    # Send a keep-alive comment to prevent timeout
                    yield ": keep-alive\n\n"
                    await asyncio.sleep(1)
                    continue

                for stream_name, messages in streams:
                    for message_id, fields in messages:
                        last_id = message_id
                        data = fields.get("data")
                        if data:
                            print(f"DEBUG: SSE yielding data: {data[:50]}...")
                            yield f"data: {data}\n\n"
                            
            except asyncio.CancelledError:
                print("Stream client disconnected")
                raise
            except Exception as e:
                print(f"Error reading stream: {e}")
                await asyncio.sleep(1) # Wait before retrying
                
    except asyncio.CancelledError:
        print("Stream generator cancelled")
        raise

@router.get("/live")
async def sse_stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
