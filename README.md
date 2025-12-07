# 🚀 Antony HFT - High-Frequency Trading System

> **Real-time options trading analytics for NSE/BSE with tick-by-tick data aggregation**

## 📊 Overview

Antony HFT is a high-frequency algorithmic trading backend for the Indian Stock Market (NSE/BSE). It provides real-time market data ingestion, 1-minute candle aggregation, GTT order management, and SSE streaming.

## ⚡ Key Features

| Feature | Description |
|---------|-------------|
| **Real-time WebSocket** | Upstox API V3 with Protobuf decoding |
| **1-Minute Candles** | OHLC + Greeks + OI + IV + Walls |
| **SSE Streaming** | Live candle/order stream to frontend |
| **GTT Orders** | Entry + Target + Stop-Loss + Trailing SL |
| **Order Updates** | Real-time execution notifications |
| **Instrument Filter** | Query param filtering for streams |

## 🛠️ Tech Stack

```
Backend:     FastAPI (Python 3.12)
Package:     UV (not pip)
Hot Cache:   Redis Streams
Cold Store:  PostgreSQL (asyncpg)
Broker:      Upstox API V3 (Protobuf/WebSocket)
HTTP:        httpx (async)
Validation:  Pydantic V2
```

## 📁 Project Structure

```
antony_project/
├── app/
│   ├── api/
│   │   ├── auth.py          # Upstox OAuth
│   │   ├── feed.py          # Feed control endpoints
│   │   ├── stream.py        # SSE (/live, /candles, /orders)
│   │   ├── gtt.py           # GTT order endpoints
│   │   └── instrument.py    # Option chain mapping
│   ├── services/
│   │   ├── feed_service.py         # WebSocket management
│   │   ├── candle_aggregator.py    # TBT → 1M candle
│   │   ├── gtt_service.py          # GTT order service
│   │   ├── order_update_service.py # Order WebSocket
│   │   └── upstox_auth.py          # Token management
│   ├── models/
│   │   ├── candle.py        # Candle1M, RawTick
│   │   └── gtt.py           # GTT order models
│   ├── db/
│   │   ├── redis.py
│   │   └── postgres.py
│   └── main.py
├── docker-compose.yml
└── pyproject.toml
```

## 🔥 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/login` | Upstox OAuth URL |
| GET | `/callback` | OAuth callback |

### Feed Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feed/connect` | Start WebSocket |
| POST | `/api/v1/feed/disconnect` | Stop WebSocket |
| POST | `/api/v1/feed/subscribe` | Subscribe instruments |

### GTT Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/gtt/place` | Place GTT order |
| PUT | `/api/v1/gtt/modify` | Modify order |
| DELETE | `/api/v1/gtt/cancel` | Cancel order |
| GET | `/api/v1/gtt/{id}` | Get order details |
| GET | `/api/v1/gtt/` | Get all orders |

### Streaming (SSE)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stream/live` | Raw tick stream |
| GET | `/api/v1/stream/candles` | 1-min candle stream |
| GET | `/api/v1/stream/orders` | Order execution updates |

#### Stream Filtering
```bash
# All instruments (default)
GET /api/v1/stream/candles

# Specific instruments only
GET /api/v1/stream/candles?instruments=NSE_FO|61755,NSE_FO|61756
```

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Redis + Postgres status |

## 📈 GTT Order Example

```json
{
  "type": "MULTIPLE",
  "quantity": 25,
  "product": "I",
  "rules": [
    {"strategy": "ENTRY", "trigger_type": "ABOVE", "trigger_price": 200},
    {"strategy": "TARGET", "trigger_type": "IMMEDIATE", "trigger_price": 220},
    {"strategy": "STOPLOSS", "trigger_type": "IMMEDIATE", "trigger_price": 190, "trailing_gap": 5}
  ],
  "instrument_token": "NSE_FO|61755",
  "transaction_type": "BUY"
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
// 1. Candle Stream (with filter)
const candles = new EventSource('/api/v1/stream/candles?instruments=NSE_FO|61755');
candles.addEventListener('candle', (e) => {
  const candle = JSON.parse(e.data);
  console.log(candle.close, candle.oi_diff);
});

// 2. Order Updates
const orders = new EventSource('/api/v1/stream/orders');
orders.addEventListener('order', (e) => {
  const update = JSON.parse(e.data);
  console.log('Order:', update.status, update.order_id);
});
```

## 📝 License

MIT License - Antony HFT

---

**Built with ❤️ for Indian Markets**
