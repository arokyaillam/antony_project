"""
1-Minute Candle Models - Pydantic Data Structures
==================================================

TBT (Tick-by-Tick) data-ஐ 1-minute candle-ஆக aggregate செய்த data structures.
Frontend இதை வைத்து metrics/conditions எழுதலாம்.

Author: Antony HFT System
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-MODELS - அடிப்படை கூறுகள்
# ═══════════════════════════════════════════════════════════════════════════════

class WallInfo(BaseModel):
    """
    Bid/Ask Wall Information
    
    2000+ qty உள்ள significant order levels
    இவை support/resistance levels-ஆக act பண்ணும்
    """
    price: float = Field(..., description="Wall price level")
    qty: int = Field(..., description="Quantity at this level (>2000)")


class BidAskSnapshot(BaseModel):
    """
    30-Depth Bid/Ask Summary at candle close
    
    Walls, spreads, மற்றும் order book imbalance info
    """
    # Qty > 2000 walls
    bid_walls: List[WallInfo] = Field(default_factory=list, description="Bid walls with qty > 2000")
    ask_walls: List[WallInfo] = Field(default_factory=list, description="Ask walls with qty > 2000")
    
    # Best bid/ask (Top of book)
    best_bid_price: float = Field(0.0, description="Best (highest) bid price")
    best_bid_qty: int = Field(0, description="Quantity at best bid")
    best_ask_price: float = Field(0.0, description="Best (lowest) ask price")
    best_ask_qty: int = Field(0, description="Quantity at best ask")
    
    # Spread = Ask - Bid
    spread: float = Field(0.0, description="Bid-Ask spread")
    
    # Total 30-depth quantities
    total_bid_qty: int = Field(0, description="Sum of all 30 bid quantities")
    total_ask_qty: int = Field(0, description="Sum of all 30 ask quantities")


class GreeksSnapshot(BaseModel):
    """
    Option Greeks at a specific moment
    
    Delta, Theta, Gamma, Vega, Rho values
    """
    delta: float = Field(0.0, description="Delta - Price sensitivity to underlying")
    theta: float = Field(0.0, description="Theta - Time decay")
    gamma: float = Field(0.0, description="Gamma - Delta's rate of change")
    vega: float = Field(0.0, description="Vega - Volatility sensitivity")
    rho: float = Field(0.0, description="Rho - Interest rate sensitivity")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN 1-MINUTE CANDLE MODEL
# ═══════════════════════════════════════════════════════════════════════════════

class Candle1M(BaseModel):
    """
    1-Minute Candle - TBT data-ல் இருந்து aggregate செய்தது
    
    Frontend இதை வைத்து எல்லா metrics/conditions எழுதலாம்
    
    Time Alignment:
        9:30:00 - 9:30:59.999 → timestamp = 9:30:00
        9:31:00 - 9:31:59.999 → timestamp = 9:31:00
    """
    
    # 🔑 Identification
    instrument_key: str = Field(..., description="Instrument key (e.g., NSE_FO|61755)")
    timestamp: datetime = Field(..., description="Candle close time (IST, minute-aligned)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1️⃣ PRICE - OHLC + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    open: float = Field(..., description="Opening price of candle")
    high: float = Field(..., description="Highest price in candle")
    low: float = Field(..., description="Lowest price in candle")
    close: float = Field(..., description="Closing price of candle")
    
    # Previous Close (CP) from Upstox
    prev_close: float = Field(0.0, description="Previous day's close price")
    
    # Price Change = Close - Open (1-min candle's own change)
    price_diff: float = Field(0.0, description="Price change in this minute (close - open)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2️⃣ BID/ASK ANALYSIS - 30-Depth (2000+ Walls, Spread)
    # ═══════════════════════════════════════════════════════════════════════════
    bid_ask: BidAskSnapshot = Field(default_factory=BidAskSnapshot, description="Bid/Ask snapshot at close")
    
    # Spread change during candle
    spread_diff: float = Field(0.0, description="Spread change (close_spread - open_spread)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3️⃣ OPTION GREEKS + Diffs
    # ═══════════════════════════════════════════════════════════════════════════
    greeks: GreeksSnapshot = Field(default_factory=GreeksSnapshot, description="Greeks at candle close")
    
    # Greek changes during this 1-min candle
    delta_diff: float = Field(0.0, description="Delta change")
    theta_diff: float = Field(0.0, description="Theta change")
    gamma_diff: float = Field(0.0, description="Gamma change")
    vega_diff: float = Field(0.0, description="Vega change")
    rho_diff: float = Field(0.0, description="Rho change")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4️⃣ ATP (Average Trade Price) + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    atp: float = Field(0.0, description="Average Trade Price at close")
    atp_diff: float = Field(0.0, description="ATP change from candle open")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5️⃣ VTT (Volume Traded Today) + Volume in this minute
    # ═══════════════════════════════════════════════════════════════════════════
    vtt: int = Field(0, description="Volume Traded Today (cumulative)")
    volume_1m: int = Field(0, description="Volume traded in this 1-min candle")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 6️⃣ OI (Open Interest) + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    oi: int = Field(0, description="Open Interest at close")
    oi_diff: int = Field(0, description="OI change in this 1-min")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 7️⃣ IV (Implied Volatility) + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    iv: float = Field(0.0, description="Implied Volatility at close")
    iv_diff: float = Field(0.0, description="IV change from candle open")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 8️⃣ TBQ (Total Bid Quantity) + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    tbq: int = Field(0, description="Total Bid Quantity at close")
    tbq_diff: int = Field(0, description="TBQ change")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 9️⃣ TSQ (Total Sell Quantity) + Diff
    # ═══════════════════════════════════════════════════════════════════════════
    tsq: int = Field(0, description="Total Sell Quantity at close")
    tsq_diff: int = Field(0, description="TSQ change")


# ═══════════════════════════════════════════════════════════════════════════════
# RAW TICK MODEL - For parsing incoming TBT data
# ═══════════════════════════════════════════════════════════════════════════════

class BidAskQuote(BaseModel):
    """Single bid/ask level from 30-depth"""
    bidQ: str = "0"  # Upstox sends as string
    bidP: float = 0.0
    askQ: str = "0"
    askP: float = 0.0


class RawTick(BaseModel):
    """
    Raw tick data from Upstox WebSocket
    
    Used for parsing incoming TBT data before aggregation
    """
    instrument_key: str
    ltp: float = 0.0
    ltt: int = 0  # Last Trade Time in ms
    ltq: int = 0  # Last Trade Qty
    cp: float = 0.0  # Previous Close
    
    # 30-Depth Order Book
    bid_ask_quote: List[BidAskQuote] = Field(default_factory=list)
    
    # Greeks
    delta: float = 0.0
    theta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    
    # Market Data
    atp: float = 0.0
    vtt: int = 0
    oi: int = 0
    iv: float = 0.0
    tbq: int = 0
    tsq: int = 0
