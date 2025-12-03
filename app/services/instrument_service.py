import httpx
from typing import List, Dict, Optional
from app.services.upstox_auth import UpstoxAuthService

class InstrumentService:
    
    @staticmethod
    async def get_option_contracts(instrument_key: str) -> List[Dict]:
        """
        Fetch all option contracts for a given instrument key.
        """
        creds = await UpstoxAuthService.get_credentials()
        if not creds or not creds.get("access_token"):
            raise RuntimeError("Access token not found. Please login first.")
        
        access_token = creds['access_token']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.upstox.com/v2/option/contract",
                params={"instrument_key": instrument_key},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to fetch option contracts: {response.text}")
            
            data = response.json()
            return data.get("data", [])

    @classmethod
    async def get_option_chain(cls, instrument_key: str, expiry_date: str, atm_strike: float) -> Dict:
        """
        Get Option Chain for ATM, +2 ITM, +2 OTM.
        """
        contracts = await cls.get_option_contracts(instrument_key)
        
        # Filter by expiry
        expiry_contracts = [c for c in contracts if c.get("expiry") == expiry_date]
        
        if not expiry_contracts:
            raise ValueError(f"No contracts found for expiry {expiry_date}")
            
        # Group by strike price
        # Structure: { strike_price: { "CE": key, "PE": key } }
        strikes_map = {}
        for c in expiry_contracts:
            strike = float(c.get("strike_price"))
            instr_type = c.get("instrument_type") # CE or PE
            key = c.get("instrument_key")
            
            if strike not in strikes_map:
                strikes_map[strike] = {}
            
            strikes_map[strike][instr_type] = key

        # Sort strikes
        sorted_strikes = sorted(strikes_map.keys())
        
        # Find ATM index (closest strike)
        # Using min logic to find closest strike to requested atm_strike
        closest_strike = min(sorted_strikes, key=lambda x: abs(x - atm_strike))
        atm_index = sorted_strikes.index(closest_strike)
        
        # Select range: -2 to +2 (Total 5)
        start_idx = max(0, atm_index - 2)
        end_idx = min(len(sorted_strikes), atm_index + 3) # +3 because slice is exclusive
        
        selected_strikes = sorted_strikes[start_idx:end_idx]
        
        options_data = []
        for strike in selected_strikes:
            strike_data = strikes_map[strike]
            options_data.append({
                "strike_price": strike,
                "ce_instrument_key": strike_data.get("CE"),
                "pe_instrument_key": strike_data.get("PE")
            })
            
        return {
            "underlying_key": instrument_key,
            "atm_strike": closest_strike,
            "options": options_data
        }
