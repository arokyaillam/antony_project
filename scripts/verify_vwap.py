import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.vwap_service import VwapService
from app.models.candle import RawTick

def test_vwap_logic():
    print("Testing VWAP Logic...")
    
    # 1. Initial State
    state = {}
    instrument_key = "NSE_FO|12345"
    
    # 2. First Tick (Seeding)
    # Broker says: LTP=100, ATP=100, VTT=500
    # Our VWAP should match ATP = 100
    tick1 = RawTick(
        instrument_key=instrument_key,
        ltp=100.0,
        atp=100.0,
        vtt=500,
        ltt=1000,
        ltq=1,
        cp=90.0,
        iv=0,
        oi=0,
        tbq=0,
        tsq=0
    )
    
    result1 = VwapService._calculate_vwap(state, tick1)
    
    vwap_val = result1['vwap']
    print(f"Tick 1 VWAP: {vwap_val}")
    
    if vwap_val != 100.0:
        print(f"FAIL: VWAP mismatch. Got {vwap_val}")
        raise AssertionError("VWAP mismatch")
    print("PASS 1")
    
    st = state[instrument_key]
    if st['total_value'] != 50000.0:
        print(f"FAIL: Value mismatch. Got {st['total_value']}")
        raise AssertionError("Val mismatch")
    print("PASS 2")
    
    assert st['total_vol'] == 500
    print("PASS 3")
    
    # 3. Second Tick 
    tick2 = RawTick(
        instrument_key=instrument_key,
        ltp=110.0,
        atp=100.0, 
        vtt=600,
        ltt=2000,
        ltq=1,
        cp=90.0
    )
    
    result2 = VwapService._calculate_vwap(state, tick2)
    print(f"Tick 2 Result: {result2}")
    
    assert result2['volume'] == 600
    # Val = 50000 + (110 * 100) = 61000
    # Vol = 600
    # VWAP = 61000 / 600 = 101.6666...
    assert result2['vwap'] == 101.67, f"Expected 101.67, got {result2['vwap']}"
    
    # 4. Third Tick
    tick3 = RawTick(
        instrument_key=instrument_key,
        ltp=120.0,
        atp=100.0,
        vtt=600, 
        ltt=3000,
        ltq=0,
        cp=90.0
    )
    
    result3 = VwapService._calculate_vwap(state, tick3)
    print(f"Tick 3 Result: {result3}")
    
    assert result3['vwap'] == 101.67
    assert result3['volume'] == 600
    
    print("VWAP Logic Verified Successfully!")

if __name__ == "__main__":
    try:
        test_vwap_logic()
    except AssertionError as e:
        print(f"Assertion Failed: {e}")
    except Exception as e:
        print(f"Error: {e}")
