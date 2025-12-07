"""
GTT Order Models - Pydantic Data Structures
============================================

Upstox API v3 GTT (Good Till Triggered) order models.
Entry + Target + Stop-Loss with optional Trailing SL.

Author: Antony HFT System
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS / LITERALS
# ═══════════════════════════════════════════════════════════════════════════════

GTTType = Literal["SINGLE", "MULTIPLE"]
TransactionType = Literal["BUY", "SELL"]
ProductType = Literal["I", "D", "CO", "OCO"]  # Intraday, Delivery, Cover, OCO
Strategy = Literal["ENTRY", "TARGET", "STOPLOSS"]
TriggerType = Literal["ABOVE", "BELOW", "IMMEDIATE"]


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class GTTRule(BaseModel):
    """
    GTT Rule - Entry/Target/StopLoss configuration
    
    Strategy Types:
        ENTRY: Entry trigger (ABOVE/BELOW current price)
        TARGET: Profit booking (IMMEDIATE after entry)
        STOPLOSS: Loss limit (IMMEDIATE after entry)
    
    Trailing SL:
        trailing_gap: Price gap for trailing stop-loss
    """
    strategy: Strategy = Field(..., description="ENTRY, TARGET, or STOPLOSS")
    trigger_type: TriggerType = Field(..., description="ABOVE, BELOW, or IMMEDIATE")
    trigger_price: float = Field(..., description="Trigger price level")
    trailing_gap: Optional[float] = Field(None, description="Trailing gap for STOPLOSS")


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class GTTPlaceRequest(BaseModel):
    """
    GTT Place Order Request
    
    Example (Entry + Target + SL):
    {
        "type": "MULTIPLE",
        "quantity": 25,
        "product": "I",
        "rules": [
            {"strategy": "ENTRY", "trigger_type": "ABOVE", "trigger_price": 200},
            {"strategy": "TARGET", "trigger_type": "IMMEDIATE", "trigger_price": 220},
            {"strategy": "STOPLOSS", "trigger_type": "IMMEDIATE", "trigger_price": 190}
        ],
        "instrument_token": "NSE_FO|61755",
        "transaction_type": "BUY"
    }
    """
    type: GTTType = Field(..., description="SINGLE or MULTIPLE")
    quantity: int = Field(..., gt=0, description="Order quantity")
    product: ProductType = Field("I", description="I=Intraday, D=Delivery")
    rules: List[GTTRule] = Field(..., min_length=1, description="GTT rules")
    instrument_token: str = Field(..., description="Instrument key (e.g., NSE_FO|61755)")
    transaction_type: TransactionType = Field(..., description="BUY or SELL")


class GTTModifyRequest(BaseModel):
    """
    GTT Modify Order Request
    
    Requires gtt_order_id from place response
    """
    gtt_order_id: str = Field(..., description="GTT order ID to modify")
    type: GTTType = Field(..., description="SINGLE or MULTIPLE")
    quantity: int = Field(..., gt=0, description="New quantity")
    rules: List[GTTRule] = Field(..., min_length=1, description="Updated rules")


class GTTCancelRequest(BaseModel):
    """GTT Cancel Order Request"""
    gtt_order_id: str = Field(..., description="GTT order ID to cancel")


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class GTTOrderResponse(BaseModel):
    """GTT Order API Response"""
    status: str = Field(..., description="API status")
    data: Optional[dict] = Field(None, description="Response data")
    
    
class GTTOrderData(BaseModel):
    """GTT Order data from response"""
    gtt_order_id: str = Field(..., description="Created GTT order ID")
