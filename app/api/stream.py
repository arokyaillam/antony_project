import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db.redis import RedisClient
from app.services.candle_aggregator import CandleAggregator, parse_raw_tick

router = APIRouter(prefix="/stream", tags=["Live Stream"])


# ═══════════════════════════════════════════════════════════════════════════════
# RAW TICKS SSE - Original market feed
# ═══════════════════════════════════════════════════════════════════════════════

async def event_generator():
    """Raw market feed SSE generator"""
    redis = RedisClient.get_pool()
    last_id = "$"
    
    try:
        while True:
            try:
                streams = await redis.xread(
                    streams={"market_feed": last_id},
                    count=1,
                    block=1000
                )
                
                if not streams:
                    yield ": keep-alive\n\n"
                    await asyncio.sleep(1)
                    continue

                for stream_name, messages in streams:
                    for message_id, fields in messages:
                        last_id = message_id
                        data = fields.get("data")
                        if data:
                            yield f"data: {data}\n\n"
                            
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        raise


@router.get("/live")
async def sse_stream():
    """Raw market feed SSE endpoint"""
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ═══════════════════════════════════════════════════════════════════════════════
# 1-MINUTE CANDLE SSE - Aggregated candles
# ═══════════════════════════════════════════════════════════════════════════════

async def candle_event_generator():
    """
    1-Minute Candle SSE Generator
    
    Reads ticks from Redis, aggregates into 1-minute candles,
    and emits completed candles at minute boundaries.
    """
    redis = RedisClient.get_pool()
    last_id = "$"
    aggregator = CandleAggregator()
    
    try:
        while True:
            try:
                streams = await redis.xread(
                    streams={"market_feed": last_id},
                    count=10,
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
                            
                            for instrument_key, feed_data in feeds.items():
                                full_feed = feed_data.get("fullFeed", {})
                                market_ff = full_feed.get("marketFF")
                                
                                if not market_ff:
                                    continue
                                
                                tick = parse_raw_tick(instrument_key, market_ff)
                                candle = aggregator.add_tick(instrument_key, tick)
                                
                                if candle:
                                    candle_json = candle.model_dump_json()
                                    yield f"event: candle\ndata: {candle_json}\n\n"
                        
                        except json.JSONDecodeError:
                            continue
                        except Exception:
                            continue
                
            except asyncio.CancelledError:
                for candle in aggregator.flush_all():
                    candle_json = candle.model_dump_json()
                    yield f"event: candle\ndata: {candle_json}\n\n"
                raise
            except Exception:
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        raise


@router.get("/candles")
async def sse_candle_stream():
    """
    1-Minute Candle SSE Endpoint
    
    Streams completed 1-minute candles with metrics:
    - Price OHLC + diff
    - Bid/Ask walls (qty > 2000)
    - Spread, Greeks, ATP, VTT, OI, IV, TBQ, TSQ + diffs
    """
    return StreamingResponse(
        candle_event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
