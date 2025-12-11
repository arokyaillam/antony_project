import json
from datetime import datetime
from app.models.candle import Candle1M
from app.db.postgres import PostgresClient

class CandlePersistenceService:
    """
    Service to persist Candle data to PostgreSQL
    """
    
    @staticmethod
    async def save_candle(candle: Candle1M):
        """
        Save a single candle to candles_json table as JSONB
        """
        pool = PostgresClient.get_pool()
        
        # Serialize Pydantic model to dict, handling datetime
        candle_data = candle.model_dump(mode='json')
        
        query = """
            INSERT INTO candles_json (instrument_key, timestamp, data)
            VALUES ($1, $2, $3)
        """
        
        async with pool.acquire() as conn:
            await conn.execute(
                query,
                candle.instrument_key,
                candle.timestamp,
                json.dumps(candle_data)
            )

    @staticmethod
    async def save_candles_batch(candles: list[Candle1M]):
        """
        Save multiple candles efficiently
        """
        if not candles:
            return

        pool = PostgresClient.get_pool()
        query = """
            INSERT INTO candles_json (instrument_key, timestamp, data)
            VALUES ($1, $2, $3)
        """
        
        values = [
            (c.instrument_key, c.timestamp, json.dumps(c.model_dump(mode='json')))
            for c in candles
        ]
        
        async with pool.acquire() as conn:
            await conn.executemany(query, values)
