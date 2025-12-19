import asyncio
import json
import logging
from typing import Dict, Optional, Set, AsyncGenerator

from app.db.redis import RedisClient
from app.services.candle_aggregator import parse_raw_tick
from app.models.candle import RawTick

logger = logging.getLogger(__name__)

class VwapService:
    """
    VWAP (Volume Weighted Average Price) Calculation Service
    
    Logic:
        VWAP = Total Traded Value / Total Traded Volume
        
    State Management:
        - When a new instrument is seen, we seed from the broker's ATP and VTT.
        - Initial Total Value = ATP * VTT
        - On subsequent ticks:
            Delta Volume = Current VTT - Prev VTT
            Delta Value = LTP * Delta Volume
            New Total Value += Delta Value
            New Total Volume += Delta Volume
            New VWAP = New Total Value / New Total Volume
    """
    
    @classmethod
    async def stream_vwap(cls, instrument_filter: Optional[Set[str]] = None) -> AsyncGenerator[str, None]:
        """
        Streams VWAP updates via SSE.
        
        Yields:
             Server-Sent Event data string: "data: {...}\n\n"
        """
        redis = RedisClient.get_pool()
        last_id = "$"
        
        # Local state: { instrument_key: {"total_value": float, "total_vol": int, "prev_vtt": int} }
        state: Dict[str, Dict] = {}
        
        try:
            while True:
                try:
                    streams = await redis.xread(
                        streams={"market_feed": last_id},
                        count=100,
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
                                    # Filter if needed
                                    if instrument_filter and instrument_key not in instrument_filter:
                                        continue
                                    
                                    full_feed = feed_data.get("fullFeed", {})
                                    market_ff = full_feed.get("marketFF")
                                    
                                    if not market_ff:
                                        continue
                                    
                                    # Parse tick using existing helper
                                    tick: RawTick = parse_raw_tick(instrument_key, market_ff)
                                    
                                    # Calculate VWAP
                                    vwap_data = cls._calculate_vwap(state, tick)
                                    
                                    if vwap_data:
                                        yield f"data: {json.dumps(vwap_data)}\n\n"
                                        
                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                logger.error(f"Error processing tick for VWAP: {e}")
                                continue
                                
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in VWAP stream loop: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("VWAP stream cancelled")
            raise

    @staticmethod
    def _calculate_vwap(state: Dict[str, Dict], tick: RawTick) -> Optional[Dict]:
        """
        Calculates incremental VWAP.
        updates `state` in-place.
        """
        key = tick.instrument_key
        
        # Retrieve current cumulative volume (VTT) from tick
        current_vtt = tick.vtt
        ltp = tick.ltp
        atp = tick.atp  # Broker's VWAP (used for seeding)
        
        if key not in state:
            # Seed state from this first tick
            # Total Value = ATP * VTT
            total_value = atp * current_vtt
            
            state[key] = {
                "total_value": total_value,
                "total_vol": current_vtt,
                "prev_vtt": current_vtt
            }
            
            # For the very first tick, our calculated VWAP is just the ATP
            return {
                "instrument_key": key,
                "timestamp": tick.ltt,
                "vwap": atp,
                "ltp": ltp,
                "volume": current_vtt
            }
        
        else:
            inst_state = state[key]
            prev_vtt = inst_state["prev_vtt"]
            
            # Calculate Delta Volume
            delta_vol = current_vtt - prev_vtt
            
            # If no volume change or negative (reset?), just return current state or skip
            if delta_vol <= 0:
                # If delta_vol < 0, it means VTT reset (new session?). Re-seed.
                if delta_vol < 0:
                     inst_state["total_value"] = tick.atp * current_vtt
                     inst_state["total_vol"] = current_vtt
                     inst_state["prev_vtt"] = current_vtt
                     return {
                        "instrument_key": key,
                        "timestamp": tick.ltt,
                        "vwap": tick.atp,
                        "ltp": ltp,
                        "volume": current_vtt
                    }
                
                # No volume traded in this tick, VWAP doesn't change
                return {
                    "instrument_key": key,
                    "timestamp": tick.ltt,
                    "vwap": inst_state["total_value"] / inst_state["total_vol"] if inst_state["total_vol"] > 0 else 0,
                    "ltp": ltp,
                    "volume": inst_state["total_vol"]
                }
            
            # Update State
            # Add value of new trades: LTP * DeltaVol
            inst_state["total_value"] += ltp * delta_vol
            inst_state["total_vol"] += delta_vol
            inst_state["prev_vtt"] = current_vtt
            
            # Calculate New VWAP
            new_vwap = inst_state["total_value"] / inst_state["total_vol"]
            
            return {
                "instrument_key": key,
                "timestamp": tick.ltt,
                "vwap": round(new_vwap, 2),
                "ltp": ltp,
                "volume": inst_state["total_vol"]
            }
