import asyncio
from typing import List, Dict
from app.services.instrument_service import InstrumentService

# Mocking the network call
async def mock_get_contracts(instrument_key: str) -> List[Dict]:
    contracts = []
    
    # Simulate Nifty (Gap 50)
    if "Nifty 50" in instrument_key:
        base = 21000
        for i in range(20): # 21000 to 22000
            strike = base + (i * 50)
            contracts.append({
                "expiry": "2024-02-29",
                "strike_price": float(strike),
                "instrument_type": "CE",
                "instrument_key": f"NIFTY|{strike}|CE"
            })
            contracts.append({
                "expiry": "2024-02-29",
                "strike_price": float(strike),
                "instrument_type": "PE",
                "instrument_key": f"NIFTY|{strike}|PE"
            })
            
    # Simulate BankNifty (Gap 100)
    elif "Bank" in instrument_key:
        base = 45000
        for i in range(20): # 45000 to 47000
            strike = base + (i * 100)
            contracts.append({
                "expiry": "2024-02-29",
                "strike_price": float(strike),
                "instrument_type": "CE",
                "instrument_key": f"BANKNIFTY|{strike}|CE"
            })
            contracts.append({
                "expiry": "2024-02-29",
                "strike_price": float(strike),
                "instrument_type": "PE",
                "instrument_key": f"BANKNIFTY|{strike}|PE"
            })
            
    return contracts

# Monkey patch the method
InstrumentService.get_option_contracts = mock_get_contracts

async def test_logic():
    print("--- Testing Nifty 50 (Gap 50) ---")
    # ATM Request: 21520 -> Closest should be 21500
    result = await InstrumentService.get_option_chain("NSE_INDEX|Nifty 50", "2024-02-29", 21520)
    print(f"Requested ATM: 21520")
    print(f"Calculated ATM: {result['atm_strike']}")
    print("Strikes Selected:")
    for opt in result['options']:
        print(f"  {opt['strike_price']}")
        
    print("\n--- Testing BankNifty (Gap 100) ---")
    # ATM Request: 46080 -> Closest should be 46100
    result = await InstrumentService.get_option_chain("NSE_INDEX|Nifty Bank", "2024-02-29", 46080)
    print(f"Requested ATM: 46080")
    print(f"Calculated ATM: {result['atm_strike']}")
    print("Strikes Selected:")
    for opt in result['options']:
        print(f"  {opt['strike_price']}")

if __name__ == "__main__":
    asyncio.run(test_logic())
