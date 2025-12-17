
import logging
import asyncio
import upstox_client
from app.services.upstox_auth import UpstoxAuthService
from app.services.feed_service import FeedService

logger = logging.getLogger(__name__)

class HistoryService:
    @staticmethod
    async def get_historical_candles(instrument_key: str, interval: str, to_date: str, from_date: str):
        """
        Fetch historical candle data using Upstox Python SDK.
        Uses HistoryApi or HistoryV3Api.
        """
        try:
            # Normalize interval
            interval_map = {
                "days": "day",
                "1d": "day", 
                "1m": "1minute",
                "30m": "30minute",
                "weeks": "week",
                "months": "month"
            }
            if interval in interval_map:
                interval = interval_map[interval]

            # 1. Get Access Token
            access_token = await UpstoxAuthService.get_access_token()
            
            # 2. Configure SDK
            configuration = upstox_client.Configuration()
            configuration.access_token = access_token
            api_client = upstox_client.ApiClient(configuration)
            
            # 3. Initialize History API
            # Trying HistoryApi first (standard). If user insisted on V3, checking availability.
            # Assuming standard SDK structure.
            if hasattr(upstox_client, 'HistoryApi'):
                api_instance = upstox_client.HistoryApi(api_client)
                # Standard call: get_historical_candle_data(instrument_key, interval, to_date, from_date)
                # API version header might be needed? SDK handles it usually.
                response = api_instance.get_historical_candle_data(
                    instrument_key, interval, to_date, from_date
                )
                return response


            elif hasattr(upstox_client, 'HistoryV3Api'): 
                 # Fallback/User suggestion
                api_instance = upstox_client.HistoryV3Api(api_client)
                # Using the method name from user snippet if it exists
                if hasattr(api_instance, 'get_historical_candle_data1'):
                     response = api_instance.get_historical_candle_data1(
                        instrument_key, interval, to_date, from_date
                     )
                     return response
                else: 
                     # Fallback to standard name
                     response = api_instance.get_historical_candle_data(
                        instrument_key, interval, to_date, from_date
                     )
                     return response
            else:
                # Direct HTTP fallback if SDK classes missing (unlikely if installed)
                raise ImportError("HistoryApi class not found in upstox_client")

        except Exception as e:
            logger.error(f"Error fetching history for {instrument_key}: {e}")
            raise e

    @staticmethod
    async def get_subscribed_history(interval: str, to_date: str, from_date: str):
        """
        Fetch history for ALL currently subscribed instruments.
        """
        subscriptions = FeedService.get_subscriptions()
        results = {}
        
        # Limit concurrency to avoid rate limits? 
        # Upstox might have rate limits. executing sequentially or small batches.
        # For now, sequential to be safe.
        
        for key in subscriptions:
            try:
                data = await HistoryService.get_historical_candles(key, interval, to_date, from_date)
                results[key] = data
            except Exception as e:
                results[key] = {"error": str(e)}
                
        return results
