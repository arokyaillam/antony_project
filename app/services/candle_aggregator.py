"""
Candle Aggregator - TBT to 1-Minute Candle Conversion
======================================================

TBT (Tick-by-Tick) data-ஐ 1-minute candle-ஆக aggregate செய்யும் logic.
Uses `toolz` for functional programming utilities.

Time Alignment:
    9:30:00 - 9:30:59.999 → 9:30:00 candle
    9:31:00 - 9:31:59.999 → 9:31:00 candle

Author: Antony HFT System
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from toolz import curry, pipe, groupby, valmap
import pytz

from app.models.candle import (
    Candle1M, 
    WallInfo, 
    BidAskSnapshot, 
    GreeksSnapshot,
    RawTick,
    BidAskQuote
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

IST = pytz.timezone('Asia/Kolkata')
MINUTE_MS = 60_000  # 60 seconds in milliseconds
WALL_THRESHOLD = 2000  # Qty > 2000 = Wall


# ═══════════════════════════════════════════════════════════════════════════════
# TIME UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def floor_minute_ms(timestamp_ms: int) -> int:
    """
    Timestamp-ஐ minute boundary-க்கு floor பண்ணும் (milliseconds)
    
    Example:
        9:30:45.123 → 9:30:00.000
        9:31:00.001 → 9:31:00.000
    """
    return (timestamp_ms // MINUTE_MS) * MINUTE_MS


def ms_to_datetime(timestamp_ms: int) -> datetime:
    """Milliseconds → IST datetime"""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=IST)


def floor_minute_datetime(timestamp_ms: int) -> datetime:
    """
    Timestamp-ஐ minute-aligned IST datetime-ஆக மாற்றும்
    
    Example:
        9:30:45.123 → datetime(9:30:00) IST
    """
    floored_ms = floor_minute_ms(timestamp_ms)
    return ms_to_datetime(floored_ms)


# ═══════════════════════════════════════════════════════════════════════════════
# RAW DATA EXTRACTION - Upstox JSON → RawTick
# ═══════════════════════════════════════════════════════════════════════════════

def parse_raw_tick(instrument_key: str, market_data: Dict[str, Any]) -> RawTick:
    """
    Upstox WebSocket JSON → RawTick model
    
    Args:
        instrument_key: "NSE_FO|61755"
        market_data: The 'marketFF' dict from Upstox response
    """
    ltpc = market_data.get('ltpc', {})
    option_greeks = market_data.get('optionGreeks', {})
    market_level = market_data.get('marketLevel', {})
    bid_ask_list = market_level.get('bidAskQuote', [])
    
    # Parse bid/ask quotes
    quotes = [
        BidAskQuote(
            bidQ=q.get('bidQ', '0'),
            bidP=float(q.get('bidP', 0)),
            askQ=q.get('askQ', '0'),
            askP=float(q.get('askP', 0))
        )
        for q in bid_ask_list
    ]
    
    return RawTick(
        instrument_key=instrument_key,
        ltp=float(ltpc.get('ltp', 0)),
        ltt=int(ltpc.get('ltt', 0)),
        ltq=int(ltpc.get('ltq', 0)) if ltpc.get('ltq') else 0,
        cp=float(ltpc.get('cp', 0)),
        bid_ask_quote=quotes,
        delta=float(option_greeks.get('delta', 0)),
        theta=float(option_greeks.get('theta', 0)),
        gamma=float(option_greeks.get('gamma', 0)),
        vega=float(option_greeks.get('vega', 0)),
        rho=float(option_greeks.get('rho', 0)),
        atp=float(market_data.get('atp', 0)),
        vtt=int(market_data.get('vtt', 0)) if market_data.get('vtt') else 0,
        oi=int(market_data.get('oi', 0)) if market_data.get('oi') else 0,
        iv=float(market_data.get('iv', 0)),
        tbq=int(market_data.get('tbq', 0)) if market_data.get('tbq') else 0,
        tsq=int(market_data.get('tsq', 0)) if market_data.get('tsq') else 0,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WALL DETECTION - 30-Depth Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def extract_walls(quotes: List[BidAskQuote], threshold: int = WALL_THRESHOLD) -> tuple[List[WallInfo], List[WallInfo]]:
    """
    30-Depth quotes-ல் இருந்து walls (qty > threshold) extract பண்ணும்
    
    Returns:
        (bid_walls, ask_walls)
    """
    bid_walls = []
    ask_walls = []
    
    for q in quotes:
        bid_qty = int(q.bidQ)
        ask_qty = int(q.askQ)
        
        if bid_qty > threshold:
            bid_walls.append(WallInfo(price=q.bidP, qty=bid_qty))
        
        if ask_qty > threshold:
            ask_walls.append(WallInfo(price=q.askP, qty=ask_qty))
    
    return bid_walls, ask_walls


def build_bid_ask_snapshot(quotes: List[BidAskQuote]) -> BidAskSnapshot:
    """
    Quotes list → BidAskSnapshot model
    
    - Walls (qty > 2000)
    - Best bid/ask
    - Spread
    - Total quantities
    """
    if not quotes:
        return BidAskSnapshot()
    
    # Extract walls
    bid_walls, ask_walls = extract_walls(quotes)
    
    # Best bid/ask (first in list = top of book)
    first = quotes[0]
    best_bid_price = first.bidP
    best_bid_qty = int(first.bidQ)
    best_ask_price = first.askP
    best_ask_qty = int(first.askQ)
    
    # Spread
    spread = best_ask_price - best_bid_price
    
    # Total quantities
    total_bid_qty = sum(int(q.bidQ) for q in quotes)
    total_ask_qty = sum(int(q.askQ) for q in quotes)
    
    return BidAskSnapshot(
        bid_walls=bid_walls,
        ask_walls=ask_walls,
        best_bid_price=best_bid_price,
        best_bid_qty=best_bid_qty,
        best_ask_price=best_ask_price,
        best_ask_qty=best_ask_qty,
        spread=round(spread, 2),
        total_bid_qty=total_bid_qty,
        total_ask_qty=total_ask_qty,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CANDLE BUILDER - Multiple Ticks → Candle1M
# ═══════════════════════════════════════════════════════════════════════════════

def build_candle(instrument_key: str, minute_ts: int, ticks: List[RawTick]) -> Candle1M:
    """
    ஒரு minute's ticks → Candle1M object
    
    Args:
        instrument_key: Instrument identifier
        minute_ts: Floored minute timestamp in ms
        ticks: List of ticks within this minute
    
    Logic:
        First tick = Open values
        Last tick = Close values
        Max/Min = High/Low
        Diffs = Close - Open
    """
    if not ticks:
        raise ValueError("Cannot build candle from empty tick list")
    
    first = ticks[0]
    last = ticks[-1]
    
    # OHLC from LTP
    prices = [t.ltp for t in ticks]
    open_price = first.ltp
    high_price = max(prices)
    low_price = min(prices)
    close_price = last.ltp
    
    # Price diff
    price_diff = round(close_price - open_price, 2)
    
    # Bid/Ask snapshot from last tick
    bid_ask = build_bid_ask_snapshot(last.bid_ask_quote)
    
    # Spread diff (if first tick also has quotes)
    open_spread = 0.0
    if first.bid_ask_quote:
        first_snapshot = build_bid_ask_snapshot(first.bid_ask_quote)
        open_spread = first_snapshot.spread
    spread_diff = round(bid_ask.spread - open_spread, 2)
    
    # Greeks
    greeks = GreeksSnapshot(
        delta=last.delta,
        theta=last.theta,
        gamma=last.gamma,
        vega=last.vega,
        rho=last.rho,
    )
    
    # Greek diffs
    delta_diff = round(last.delta - first.delta, 4)
    theta_diff = round(last.theta - first.theta, 4)
    gamma_diff = round(last.gamma - first.gamma, 6)
    vega_diff = round(last.vega - first.vega, 4)
    rho_diff = round(last.rho - first.rho, 4)
    
    # ATP diff
    atp_diff = round(last.atp - first.atp, 2)
    
    # Volume in this minute
    volume_1m = last.vtt - first.vtt
    
    # OI diff
    oi_diff = last.oi - first.oi
    
    # IV diff
    iv_diff = round(last.iv - first.iv, 6)
    
    # TBQ/TSQ diffs
    tbq_diff = last.tbq - first.tbq
    tsq_diff = last.tsq - first.tsq
    
    return Candle1M(
        instrument_key=instrument_key,
        timestamp=floor_minute_datetime(minute_ts),
        
        # 1. Price
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        prev_close=last.cp,
        price_diff=price_diff,
        
        # 2. Bid/Ask
        bid_ask=bid_ask,
        spread_diff=spread_diff,
        
        # 3. Greeks
        greeks=greeks,
        delta_diff=delta_diff,
        theta_diff=theta_diff,
        gamma_diff=gamma_diff,
        vega_diff=vega_diff,
        rho_diff=rho_diff,
        
        # 4. ATP
        atp=last.atp,
        atp_diff=atp_diff,
        
        # 5. VTT / Volume
        vtt=last.vtt,
        volume_1m=volume_1m,
        
        # 6. OI
        oi=last.oi,
        oi_diff=oi_diff,
        
        # 7. IV
        iv=last.iv,
        iv_diff=iv_diff,
        
        # 8. TBQ
        tbq=last.tbq,
        tbq_diff=tbq_diff,
        
        # 9. TSQ
        tsq=last.tsq,
        tsq_diff=tsq_diff,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATOR CLASS - Real-time Candle Building
# ═══════════════════════════════════════════════════════════════════════════════

class CandleAggregator:
    """
    Real-time candle aggregator
    
    Ticks-ஐ collect பண்ணி, minute boundary-ல candle emit பண்ணும்
    
    Usage:
        aggregator = CandleAggregator()
        
        # Add each incoming tick
        candle = aggregator.add_tick(instrument_key, raw_tick)
        
        # If minute boundary crossed, returns completed Candle1M
        # Otherwise returns None
    """
    
    def __init__(self):
        # {instrument_key: {current_minute_ts: [ticks]}}
        self._buffers: Dict[str, Dict[int, List[RawTick]]] = {}
        # {instrument_key: last_completed_minute_ts}
        self._last_candle_minute: Dict[str, int] = {}
    
    def add_tick(self, instrument_key: str, tick: RawTick) -> Optional[Candle1M]:
        """
        Tick add பண்ணி, minute boundary cross ஆனா candle return பண்ணும்
        
        Returns:
            Candle1M if minute boundary crossed, else None
        """
        tick_minute = floor_minute_ms(tick.ltt)
        
        # Initialize buffer for new instrument
        if instrument_key not in self._buffers:
            self._buffers[instrument_key] = {}
        
        buffer = self._buffers[instrument_key]
        
        # Check if we crossed into a new minute
        completed_candle = None
        
        if instrument_key in self._last_candle_minute:
            last_minute = self._last_candle_minute[instrument_key]
            
            # New minute started - emit previous candle
            if tick_minute > last_minute and last_minute in buffer:
                ticks = buffer[last_minute]
                if ticks:
                    completed_candle = build_candle(instrument_key, last_minute, ticks)
                # Clear old buffer
                del buffer[last_minute]
        
        # Add tick to current minute buffer
        if tick_minute not in buffer:
            buffer[tick_minute] = []
        buffer[tick_minute].append(tick)
        
        # Update last candle minute
        self._last_candle_minute[instrument_key] = tick_minute
        
        return completed_candle
    
    def flush(self, instrument_key: str) -> Optional[Candle1M]:
        """
        Force emit current candle (use at market close or disconnect)
        
        Returns:
            Candle1M if buffer has data, else None
        """
        if instrument_key not in self._buffers:
            return None
        
        buffer = self._buffers[instrument_key]
        
        if not buffer:
            return None
        
        # Get the most recent minute's data
        latest_minute = max(buffer.keys())
        ticks = buffer[latest_minute]
        
        if not ticks:
            return None
        
        candle = build_candle(instrument_key, latest_minute, ticks)
        
        # Clear buffer
        buffer.clear()
        
        return candle
    
    def flush_all(self) -> List[Candle1M]:
        """
        Flush all instruments (use at market close)
        
        Returns:
            List of all pending candles
        """
        candles = []
        for instrument_key in list(self._buffers.keys()):
            candle = self.flush(instrument_key)
            if candle:
                candles.append(candle)
        return candles


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH AGGREGATION - For historical/batch processing (using toolz)
# ═══════════════════════════════════════════════════════════════════════════════

def aggregate_ticks_batch(instrument_key: str, ticks: List[RawTick]) -> List[Candle1M]:
    """
    Batch of ticks → List of 1-minute candles
    
    Uses toolz for functional grouping:
    1. Group ticks by floored minute
    2. Build candle for each group
    
    Args:
        instrument_key: Instrument identifier
        ticks: List of all ticks
    
    Returns:
        List of Candle1M, sorted by timestamp
    """
    if not ticks:
        return []
    
    # Group by minute using toolz
    grouped = pipe(
        ticks,
        lambda ts: groupby(lambda t: floor_minute_ms(t.ltt), ts),
        lambda g: valmap(lambda tick_list: build_candle(instrument_key, min(t.ltt for t in tick_list), tick_list), g)
    )
    
    # Sort by timestamp and return
    candles = list(grouped.values())
    candles.sort(key=lambda c: c.timestamp)
    
    return candles
