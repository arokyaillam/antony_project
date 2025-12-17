<script lang="ts">
    import { marketContext } from "$lib/stores/marketContext";
    import { isFeedConnected } from "$lib/stores/feed";
    import { marketDataStore } from "$lib/stores/marketData";

    // Computed properties based on the selected index
    let selectedIndexKey = $derived($marketContext.indexKey);
    let indexName = $derived(selectedIndexKey.split("|")[1] || "Select Index");

    // Get live data for the selected index
    let indexData = $derived($marketDataStore[selectedIndexKey]);

    // Extract values with safe defaults
    let fullFeed = $derived(indexData?.fullFeed);
    let indexFF = $derived(fullFeed?.indexFF || fullFeed?.marketFF);
    let ltpc = $derived(indexFF?.ltpc);
    let ohlc = $derived(indexFF?.marketOHLC?.ohlc?.[0]);

    let ltp = $derived(ltpc?.ltp || 0);
    // Prioritize ltpc.cp (Closing Price) but fallback to OHLC close if needed
    let close = $derived(ltpc?.cp || ohlc?.close || ltp);
    let open = $derived(ohlc?.open || 0);
    let high = $derived(ohlc?.high || 0);
    let low = $derived(ohlc?.low || 0);
    let lastTradedTime = $derived(Number(ltpc?.ltt) || 0);

    // Calculate change
    let change = $derived(ltp && close ? ltp - close : 0);
    let changePercent = $derived(close ? (change / close) * 100 : 0);

    // Connection status
    let isConnected = $derived($isFeedConnected && !!indexData);

    // Format numbers
    function formatPrice(n: number): string {
        return n.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
</script>

<div class="index-card">
    <div class="card-header">
        <span class="index-name">{indexName}</span>
        <span class="status-dot" class:connected={isConnected}></span>
    </div>

    {#if selectedIndexKey}
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
    {:else}
        <div class="empty-state">
            <span class="empty-text">Please select an index</span>
        </div>
    {/if}
</div>

<style>
    .index-card {
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

    .index-card:hover {
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

    .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100px;
    }

    .empty-text {
        color: var(--text-muted);
        font-size: 14px;
        font-style: italic;
    }
</style>
