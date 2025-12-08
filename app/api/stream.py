import asyncio
import json
from typing import Optional, Set
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.db.redis import RedisClient
from app.services.candle_aggregator import CandleAggregator, parse_raw_tick

router = APIRouter(prefix="/stream", tags=["Live Stream"])


# ═══════════════════════════════════════════════════════════════════════════════
# RAW TICKS SSE - Original market feed
# ═══════════════════════════════════════════════════════════════════════════════

async def event_generator(instrument_filter: Optional[Set[str]] = None):
    """
    Raw market feed SSE generator
    
    Args:
        instrument_filter: Optional set of instrument keys to include.
                          If None, all instruments are returned.
    """
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
                            # If no filter, send all
                            if not instrument_filter:
                                yield f"data: {data}\n\n"
                            else:
                                # Parse and filter feeds
                                try:
                                    parsed = json.loads(data)
                                    feeds = parsed.get("feeds", {})
                                    filtered_feeds = {
                                        k: v for k, v in feeds.items() 
                                        if k in instrument_filter
                                    }
                                    if filtered_feeds:
                                        parsed["feeds"] = filtered_feeds
                                        yield f"data: {json.dumps(parsed)}\n\n"
                                except json.JSONDecodeError:
                                    yield f"data: {data}\n\n"
                            
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        raise


@router.get("/live")
async def sse_stream(
    instruments: Optional[str] = Query(
        None, 
        description="Comma-separated instrument keys to filter. Example: NSE_FO|61755,NSE_FO|61756"
    )
):
    """
    Raw market feed SSE endpoint
    
    Query Parameters:
        instruments: Comma-separated instrument keys (optional)
            - If provided: Only returns ticks for specified instruments
            - If omitted: Returns ticks for ALL instruments
    
    Examples:
        # எல்லா instruments
        GET /api/v1/stream/live
        
        # Options மட்டும்
        GET /api/v1/stream/live?instruments=NSE_FO|61755,NSE_FO|61756
    """
    instrument_filter: Optional[Set[str]] = None
    if instruments:
        instrument_filter = set(instruments.split(","))
    
    return StreamingResponse(
        event_generator(instrument_filter), 
        media_type="text/event-stream"
    )



# ═══════════════════════════════════════════════════════════════════════════════
# 1-MINUTE CANDLE SSE - Aggregated candles
# ═══════════════════════════════════════════════════════════════════════════════

async def candle_event_generator(instrument_filter: Optional[Set[str]] = None):
    """
    1-Minute Candle SSE Generator
    
    Reads ticks from Redis, aggregates into 1-minute candles,
    and emits completed candles at minute boundaries.
    
    Args:
        instrument_filter: Optional set of instrument keys to include.
                          If None, all instruments are processed.
                          Example: {"NSE_FO|61755", "NSE_FO|61756"}
    
    Usage:
        # எல்லா instruments
        /api/v1/stream/candles
        
        # Specific instruments மட்டும்
        /api/v1/stream/candles?instruments=NSE_FO|61755,NSE_FO|61756
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
                                # 🔥 Filter: Skip if not in filter set
                                if instrument_filter and instrument_key not in instrument_filter:
                                    continue
                                
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
async def sse_candle_stream(
    instruments: Optional[str] = Query(
        None, 
        description="Comma-separated instrument keys to filter. Example: NSE_FO|61755,NSE_FO|61756"
    )
):
    """
    1-Minute Candle SSE Endpoint
    
    Streams completed 1-minute candles with metrics:
    - Price OHLC + diff
    - Bid/Ask walls (qty > 2000)
    - Spread, Greeks, ATP, VTT, OI, IV, TBQ, TSQ + diffs
    
    Query Parameters:
        instruments: Comma-separated instrument keys (optional)
            - If provided: Only streams candles for specified instruments
            - If omitted: Streams candles for ALL instruments
    
    Examples:
        # எல்லா instruments
        GET /api/v1/stream/candles
        
        # Options மட்டும் (index தவிர)
        GET /api/v1/stream/candles?instruments=NSE_FO|61755,NSE_FO|61756
        
        # ஒரே ஒரு instrument
        GET /api/v1/stream/candles?instruments=NSE_FO|61755
    """
    # Parse comma-separated instruments into a set
    instrument_filter: Optional[Set[str]] = None
    if instruments:
        instrument_filter = set(instruments.split(","))
    
    return StreamingResponse(
        candle_event_generator(instrument_filter), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER UPDATE SSE - Portfolio stream for order updates
# ═══════════════════════════════════════════════════════════════════════════════

async def order_update_generator():
    """
    Order Update SSE Generator
    
    Bridges Upstox Portfolio WebSocket to SSE for frontend.
    Streams order execution updates, GTT triggers, etc.
    """
    from app.services.order_update_service import OrderUpdateService
    
    try:
        async for update in OrderUpdateService.stream_updates():
            yield f"event: order\ndata: {json.dumps(update)}\n\n"
    except asyncio.CancelledError:
        await OrderUpdateService.stop()
        raise
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.get("/orders")
async def sse_order_stream():
    """
    Order Update SSE Endpoint
    
    Streams real-time order updates:
    - Order placed/modified/cancelled
    - GTT trigger events
    - Order execution (complete/rejected)
    
    Example events:
    ```
    event: order
    data: {"order_id": "123", "status": "complete", "quantity": 25}
    ```
    
    Financial Logic:
        GTT order execute ஆனவுடன் இங்கே notification வரும்.
        Order status: PENDING → OPEN → COMPLETE / REJECTED
    """
    return StreamingResponse(
        order_update_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

