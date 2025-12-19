
from typing import Dict, Optional

# Mock class matching generic structure
class MockTick:
    def __init__(self, key, ltp, atp, vtt, ltt):
        self.instrument_key = key
        self.ltp = ltp
        self.atp = atp
        self.vtt = vtt
        self.ltt = ltt

def calculate_vwap(state, tick):
    key = tick.instrument_key
    current_vtt = tick.vtt
    ltp = tick.ltp
    atp = tick.atp
    
    if key not in state:
        total_value = atp * current_vtt
        state[key] = {
            "total_value": total_value,
            "total_vol": current_vtt,
            "prev_vtt": current_vtt
        }
        return { "vwap": atp, "volume": current_vtt }
    else:
        inst_state = state[key]
        prev_vtt = inst_state["prev_vtt"]
        delta_vol = current_vtt - prev_vtt
        
        if delta_vol <= 0:
            if delta_vol < 0: # Reset
                 inst_state["total_value"] = tick.atp * current_vtt
                 inst_state["total_vol"] = current_vtt
                 inst_state["prev_vtt"] = current_vtt
                 return { "vwap": tick.atp, "volume": current_vtt }
            return { "vwap": inst_state["total_value"] / inst_state["total_vol"], "volume": inst_state["total_vol"] }
        
        inst_state["total_value"] += ltp * delta_vol
        inst_state["total_vol"] += delta_vol
        inst_state["prev_vtt"] = current_vtt
        
        new_vwap = inst_state["total_value"] / inst_state["total_vol"]
        return { "vwap": round(new_vwap, 2), "volume": inst_state["total_vol"] }

def run_test():
    print("Running Simple Verify...")
    state = {}
    key = "TEST"
    
    # Tick 1
    t1 = MockTick(key, 100.0, 100.0, 500, 1000)
    r1 = calculate_vwap(state, t1)
    print(f"T1: {r1}")
    if r1['vwap'] != 100.0:
        print("FAIL T1")
        return
        
    # Tick 2
    # Price 110, Vol goes 500 -> 600 (Delta 100)
    # Value += 110 * 100 = 11000
    # Total Value = 50000 + 11000 = 61000
    # Total Vol = 600
    # VWAP = 61000 / 600 = 101.666
    t2 = MockTick(key, 110.0, 100.0, 600, 2000)
    r2 = calculate_vwap(state, t2)
    print(f"T2: {r2}")
    
    if r2['vwap'] != 101.67:
        print(f"FAIL T2: Got {r2['vwap']}")
        return

    print("SUCCESS")

if __name__ == "__main__":
    run_test()
