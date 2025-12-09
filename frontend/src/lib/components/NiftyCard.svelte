<script lang="ts">
    import { onMount, onDestroy } from "svelte";

    const API_BASE = "http://localhost:8000";
    const NIFTY_KEY = "NSE_INDEX|Nifty 50";

    // Nifty Index Data
    let ltp = $state(0);
    let open = $state(0);
    let high = $state(0);
    let low = $state(0);
    let close = $state(0);
    let change = $state(0);
    let changePercent = $state(0);
    let isConnected = $state(false);

    let eventSource: EventSource | null = null;

    function processData(data: any) {
        if (!data?.feeds) return;

        const niftyFeed = data.feeds[NIFTY_KEY];
        if (!niftyFeed) return;

        const ff = niftyFeed.fullFeed?.indexFF;
        if (!ff) return;

        const ltpc = ff.ltpc;
        const ohlc = ff.marketOHLC?.ohlc?.[0]; // Today's OHLC

        if (ltpc) {
            ltp = ltpc.ltp || 0;
            const prevClose = ltpc.cp || ltp;
            change = ltp - prevClose;
            changePercent = prevClose > 0 ? (change / prevClose) * 100 : 0;
        }

        if (ohlc) {
            open = ohlc.open || 0;
            high = ohlc.high || 0;
            low = ohlc.low || 0;
            close = ohlc.close || ltp;
        }

        isConnected = true;
    }

    onMount(() => {
        // Direct SSE connection for Nifty Index
        const url = `${API_BASE}/api/v1/stream/live?instruments=${NIFTY_KEY}`;
        eventSource = new EventSource(url);

        eventSource.onopen = () => {
            console.log("Nifty stream connected");
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                processData(data);
            } catch {
                // Skip invalid JSON (keep-alive comments)
            }
        };

        eventSource.onerror = () => {
            isConnected = false;
        };
    });

    onDestroy(() => {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    });

    // Format numbers
    function formatPrice(n: number): string {
        return n.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
</script>

<div class="nifty-card">
    <div class="card-header">
        <span class="index-name">NIFTY 50</span>
        <span class="status-dot" class:connected={isConnected}></span>
    </div>

    <div class="ltp-section">
        <span class="ltp">{formatPrice(ltp)}</span>
        <span
            class="change"
            class:positive={change >= 0}
            class:negative={change < 0}
        >
            {change >= 0 ? "+" : ""}{formatPrice(change)} ({changePercent.toFixed(
                2,
            )}%)
        </span>
    </div>

    <div class="ohlc-grid">
        <div class="ohlc-item">
            <span class="label">O</span>
            <span class="value">{formatPrice(open)}</span>
        </div>
        <div class="ohlc-item">
            <span class="label">H</span>
            <span class="value high">{formatPrice(high)}</span>
        </div>
        <div class="ohlc-item">
            <span class="label">L</span>
            <span class="value low">{formatPrice(low)}</span>
        </div>
        <div class="ohlc-item">
            <span class="label">C</span>
            <span class="value">{formatPrice(close)}</span>
        </div>
    </div>
</div>

<style>
    .nifty-card {
        background: linear-gradient(145deg, #1a1a24 0%, #12121a 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        min-width: 280px;
        box-shadow: var(--shadow-md);
        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }

    .nifty-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-blue);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .index-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        transition: background 0.3s ease;
    }

    .status-dot.connected {
        background: var(--accent-green);
        box-shadow: 0 0 8px var(--accent-green);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }

    .ltp-section {
        margin-bottom: 16px;
    }

    .ltp {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-mono);
        display: block;
        margin-bottom: 4px;
    }

    .change {
        font-size: 14px;
        font-weight: 500;
        font-family: var(--font-mono);
    }

    .change.positive {
        color: var(--accent-green);
    }

    .change.negative {
        color: var(--accent-red);
    }

    .ohlc-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        padding-top: 12px;
        border-top: 1px solid var(--border-color);
    }

    .ohlc-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }

    .label {
        font-size: 11px;
        color: var(--text-muted);
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .value {
        font-size: 13px;
        color: var(--text-primary);
        font-family: var(--font-mono);
    }

    .value.high {
        color: var(--accent-green);
    }

    .value.low {
        color: var(--accent-red);
    }
</style>
