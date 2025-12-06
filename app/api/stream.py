import asyncio
import json
from typing import Dict
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db.redis import RedisClient
from app.services.candle_aggregator import CandleAggregator, parse_raw_tick

router = APIRouter(prefix="/stream", tags=["Live Stream"])


# ═══════════════════════════════════════════════════════════════════════════════
# RAW TICKS SSE - Original market feed
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# 1-MINUTE CANDLE SSE - Aggregated candles
# ═══════════════════════════════════════════════════════════════════════════════

async def candle_event_generator():
    """
    1-Minute Candle SSE Generator
    
    - Redis market_feed stream-ல் இருந்து ticks படிக்கும்
    - CandleAggregator-ல் aggregate பண்ணும்
    - Minute boundary-ல் completed candle emit பண்ணும்
    
    SSE Events:
        event: candle
        data: {Candle1M JSON}
    """
    redis = RedisClient.get_pool()
    last_id = "$"  # Start from new messages
    aggregator = CandleAggregator()
    
    try:
        while True:
            try:
                # Read from market_feed stream
                streams = await redis.xread(
                    streams={"market_feed": last_id},
                    count=10,  # Process up to 10 messages at a time
                    block=1000
                )
                
                if not streams:
                    yield ": keep-alive\n\n"
                    continue
                
                for stream_name, messages in streams:
                    for message_id, fields in messages:
                        last_id = message_id
                        raw_data = fields.get("data")
                        
                        if not raw_data:
                            continue
                        
                        try:
                            data = json.loads(raw_data)
                            feeds = data.get("feeds", {})
                            
                            # Process each instrument in the feed
                            for instrument_key, feed_data in feeds.items():
                                # Skip index feeds (they don't have marketFF)
                                full_feed = feed_data.get("fullFeed", {})
                                market_ff = full_feed.get("marketFF")
                                
                                if not market_ff:
                                    continue
                                
                                # Parse raw tick
                                tick = parse_raw_tick(instrument_key, market_ff)
                                
                                # Add to aggregator - returns candle if minute boundary crossed
                                candle = aggregator.add_tick(instrument_key, tick)
                                
                                if candle:
                                    # Completed candle! Stream it
                                    candle_json = candle.model_dump_json()
                                    yield f"event: candle\ndata: {candle_json}\n\n"
                                    print(f"🕯️ Candle emitted: {instrument_key} @ {candle.timestamp}")
                        
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            continue
                        except Exception as e:
                            print(f"Error processing tick: {e}")
                            continue
                
            except asyncio.CancelledError:
                print("Candle stream client disconnected")
                # Flush all pending candles before exit
                for candle in aggregator.flush_all():
                    candle_json = candle.model_dump_json()
                    yield f"event: candle\ndata: {candle_json}\n\n"
                raise
            except Exception as e:
                print(f"Error in candle stream: {e}")
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        print("Candle stream generator cancelled")
        raise


@router.get("/candles")
async def sse_candle_stream():
    """
    1-Minute Candle SSE Endpoint
    
    Streams completed 1-minute candles with all metrics:
    - Price OHLC + diff
    - Bid/Ask walls (qty > 2000)
    - Spread
    - Greeks + diffs
    - ATP, VTT, OI, IV, TBQ, TSQ + diffs
    
    Usage:
        const source = new EventSource('/api/v1/stream/candles');
        source.addEventListener('candle', (e) => {
            const candle = JSON.parse(e.data);
            console.log(candle.instrument_key, candle.price_diff);
        });
    """
    return StreamingResponse(
        candle_event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

