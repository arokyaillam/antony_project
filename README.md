# 🚀 Antony HFT - High-Frequency Trading System

> **Real-time options trading analytics for NSE/BSE with tick-by-tick data aggregation**

## 📊 Overview

Antony HFT is a high-frequency algorithmic trading backend for the Indian Stock Market (NSE/BSE). It provides real-time market data ingestion, 1-minute candle aggregation with advanced metrics, and SSE streaming for frontend consumption.

## ⚡ Key Features

| Feature | Description |
|---------|-------------|
| **Real-time WebSocket** | Upstox API V3 with Protobuf decoding |
| **1-Minute Candles** | OHLC + Greeks + OI + IV + Walls |
| **SSE Streaming** | Live candle stream to frontend |
| **Wall Detection** | Bid/Ask qty > 2000 detection |
| **Dynamic Subscriptions** | Auto-manage option strikes |

## 🛠️ Tech Stack

```
Backend:     FastAPI (Python 3.12)
Package:     UV (not pip)
Hot Cache:   Redis Streams
Cold Store:  PostgreSQL (asyncpg)
Broker:      Upstox API V3 (Protobuf/WebSocket)
Validation:  Pydantic V2
```

## 📁 Project Structure

```
antony_project/
├── app/
│   ├── api/
│   │   ├── auth.py          # Upstox OAuth
│   │   ├── feed.py          # Feed control endpoints
│   │   ├── stream.py        # SSE endpoints (/live, /candles)
│   │   └── instrument.py    # Option chain mapping
│   ├── services/
│   │   ├── feed_service.py      # WebSocket management
│   │   ├── candle_aggregator.py # TBT → 1M candle
│   │   └── upstox_auth.py       # Token management
│   ├── models/
│   │   └── candle.py        # Pydantic: Candle1M, RawTick
│   ├── db/
│   │   ├── redis.py         # Redis client
│   │   └── postgres.py      # PostgreSQL client
│   └── main.py              # FastAPI app
├── docker-compose.yml       # Redis + Postgres
├── pyproject.toml           # Dependencies
└── Dockerfile
```

## 🔥 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/login` | Upstox OAuth login URL |
| GET | `/callback` | OAuth callback handler |

### Feed Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feed/connect` | Start WebSocket |
| POST | `/api/v1/feed/disconnect` | Stop WebSocket |
| POST | `/api/v1/feed/subscribe` | Subscribe instruments |

### Streaming (SSE)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stream/live` | Raw tick stream |
| GET | `/api/v1/stream/candles` | 1-min candle stream |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Redis + Postgres status |

## 📈 Candle1M Model

```python
{
  "instrument_key": "NSE_FO|41908",
  "timestamp": "2025-12-05T12:05:00+05:30",
  
  # Price
  "open": 180.0, "high": 182.5, "low": 179.5, "close": 181.0,
  "price_diff": 1.0,
  
  # Bid/Ask Walls (qty > 2000)
  "bid_ask": {
    "bid_walls": [{"price": 180.0, "qty": 5000}],
    "ask_walls": [{"price": 182.0, "qty": 3500}],
    "spread": 0.15
  },
  
  # Greeks
  "greeks": {"delta": 0.45, "theta": -15.5, "gamma": 0.001, "vega": 12.5},
  "delta_diff": 0.02,
  
  # Volume & OI
  "vtt": 50000000, "volume_1m": 125000,
  "oi": 5000000, "oi_diff": 1500,
  
  # IV
  "iv": 0.18, "iv_diff": 0.002,
  
  # Pressure
  "tbq": 1500000, "tsq": 1200000
}
```

## 🚀 Quick Start

```bash
# 1. Clone & Setup
git clone <repo>
cd antony_project

# 2. Start Redis + Postgres
docker-compose up -d

# 3. Install dependencies
uv sync

# 4. Set environment variables
cp .env.example .env
# Edit .env with Upstox credentials

# 5. Run server
uv run uvicorn app.main:app --port 8000 --reload
```

## 🔐 Environment Variables

```env
UPSTOX_API_KEY=your_api_key
UPSTOX_API_SECRET=your_secret
UPSTOX_REDIRECT_URI=http://localhost:8000/callback
UPSTOX_ACCESS_TOKEN=

REDIS_URL=redis://localhost:6379
POSTGRES_USER=antony
POSTGRES_PASSWORD=antony123
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=antony_hft
```

## 📡 Frontend Integration

```javascript
// Connect to SSE candle stream
const source = new EventSource('/api/v1/stream/candles');

source.addEventListener('candle', (e) => {
  const candle = JSON.parse(e.data);
  console.log(candle.instrument_key, candle.price_diff);
  console.log('Bid Walls:', candle.bid_ask.bid_walls);
  console.log('Delta:', candle.greeks.delta);
});
```

## 📝 License

MIT License - Antony HFT

---

**Built with ❤️ for Indian Markets**
