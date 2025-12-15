<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
    } from "$lib/stores/candleData";
    import {
        liveFeedStore,
        monitorInstruments,
        type LiveQuote,
    } from "$lib/stores/liveFeed";

    export let instrumentKey: string;
    export let title: string; // e.g. "MAX CE OI"
    export let strikeTitle: string; // e.g. "24000 CE"
    export let color: string = "#22c55e"; // Accent color

    // Register for Live Feed
    $: if (instrumentKey) {
        monitorInstruments([instrumentKey]);
    }

    // Reactive Data Sources
    let candleData: CandleDetails | undefined;
    let liveData: LiveQuote | undefined;

    $: candleData = $candleDataStore[instrumentKey];
    $: liveData = $liveFeedStore[instrumentKey];

    // History Logic (Rolling 10 1m candles from Candle Store)
    let history: CandleDetails[] = [];
    let lastTimestamp: string | null = null;
    let lastCandle: CandleDetails | null = null;

    $: if (candleData) {
        processHistoryUpdate(candleData);
    }

    function processHistoryUpdate(current: CandleDetails) {
        if (!lastTimestamp) {
            lastTimestamp = current.timestamp;
            lastCandle = current;
            return;
        }

        // Detect new minute (timestamp change)
        if (current.timestamp !== lastTimestamp) {
            // Push previous completed candle to history
            if (lastCandle) {
                history = [lastCandle, ...history].slice(0, 10);
            }
            lastTimestamp = current.timestamp;
        }

        // Always update lastCandle to current live state
        lastCandle = current;
    }

    // Formatters
    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtPr = (n: number | undefined) => (n ? n.toFixed(2) : "-");
    const fmtChg = (n: number | undefined) =>
        n ? (n > 0 ? "+" + n.toFixed(2) : n.toFixed(2)) : "-";
    // Extract HH:MM from timestamp (assuming "YYYY-MM-DD HH:MM:SS" or ISO)
    const fmtTime = (ts: string) => {
        if (!ts) return "-";
        const parts = ts.split(/[ T]/); // Split by space or T
        return parts[1] ? parts[1].slice(0, 5) : "-";
    };

    // Derived Display Values
    // Header should show Day Change from OPEN (User Request: "open - ltp")
    $: displayLtp = liveData?.ltp || candleData?.close;

    // Calculate Change from Open
    $: activeOpen = liveData?.open || candleData?.open;
    $: displayChg =
        displayLtp && activeOpen ? displayLtp - activeOpen : undefined;
    $: displayChgPct =
        displayChg !== undefined && activeOpen
            ? (displayChg / activeOpen) * 100
            : 0;

    // OHLC (Day)
    $: displayOpen = liveData?.open;
    $: displayHigh = liveData?.high;
    $: displayLow = liveData?.low;
    $: displayClose = liveData?.close;
</script>

<div class="active-card" style="--accent-color: {color}">
    <!-- Header -->
    <div class="card-header">
        <div class="titles">
            <span class="category-badge">{title}</span>
            <span class="strike-title">{strikeTitle}</span>
        </div>
        <span class="status-dot" class:connected={!!liveData}></span>
    </div>

    <!-- Main Price (Live Feed - Index Style) -->
    <div class="price-section">
        <span class="ltp">{fmtPr(displayLtp)}</span>
        {#if displayChg !== undefined}
            <span
                class="change"
                class:pos={displayChg >= 0}
                class:neg={displayChg < 0}
            >
                {displayChg > 0 ? "+" : ""}{fmtPr(displayChg)} ({fmtPr(
                    displayChgPct,
                )}%)
            </span>
        {/if}
    </div>

    <!-- OHLC Grid (Day OHLC from Live Feed) -->
    <div class="ohlc-grid">
        <div class="ohlc-item">
            <span class="lbl">O</span><span class="val"
                >{fmtPr(displayOpen)}</span
            >
        </div>
        <div class="ohlc-item">
            <span class="lbl">H</span><span class="val high"
                >{fmtPr(displayHigh)}</span
            >
        </div>
        <div class="ohlc-item">
            <span class="lbl">L</span><span class="val low"
                >{fmtPr(displayLow)}</span
            >
        </div>
        <div class="ohlc-item">
            <span class="lbl">C</span><span class="val"
                >{fmtPr(displayClose)}</span
            >
        </div>
    </div>

    <div class="divider"></div>

    <!-- History Table (2-Column Stacked - 1m Candles) -->
    <div class="history-list">
        <!-- Live Row (From Candle Data for consistency with history) -->
        {#if candleData}
            {@render historyItem(candleData, true)}
        {/if}

        <!-- History Rows -->
        {#each history as h}
            {@render historyItem(h, false)}
        {/each}
    </div>
</div>

{#snippet historyItem(d: CandleDetails, isLive: boolean)}
    <div class="h-item" class:live={isLive}>
        <!-- Left Col: Time & Price -->
        <div class="h-left">
            <span class="h-time">{fmtTime(d.timestamp)}</span>
            <span
                class="h-price"
                class:pos={d.price_diff > 0}
                class:neg={d.price_diff < 0}
            >
                {fmtPr(d.close)}
            </span>
        </div>

        <!-- Right Col: Metrics Stacked -->
        <div class="h-right">
            <!-- Row 1: OI -->
            <div class="m-row">
                <span class="lbl">OI:</span>
                <span class="val">{fmt(d.oi)}</span>
                <span
                    class="chg"
                    class:pos={d.oi_diff > 0}
                    class:neg={d.oi_diff < 0}
                >
                    ({d.oi_diff > 0 ? "+" : ""}{fmt(d.oi_diff)})
                </span>
            </div>
            <!-- Row 2: Vol -->
            <div class="m-row">
                <span class="lbl">Vol:</span>
                <span class="val">{fmt(d.volume_1m)}</span>
                <span
                    class="chg"
                    class:pos={d.volume_diff > 0}
                    class:neg={d.volume_diff < 0}
                >
                    ({d.volume_diff > 0 ? "+" : ""}{fmt(d.volume_diff)})
                </span>
            </div>
            <!-- Row 3: Bid/Ask -->
            <div class="m-row ba-row">
                <span class="ba"
                    >B: <span class="pr"
                        >{fmtPr(d.bid_ask?.best_bid_price)}</span
                    >
                    <span class="qty">({fmt(d.bid_ask?.best_bid_qty)})</span
                    ></span
                >
                <span class="ba"
                    >A: <span class="pr"
                        >{fmtPr(d.bid_ask?.best_ask_price)}</span
                    >
                    <span class="qty">({fmt(d.bid_ask?.best_ask_qty)})</span
                    ></span
                >
            </div>
        </div>
    </div>
{/snippet}

<style>
    .active-card {
        background: linear-gradient(145deg, #1a1a24 0%, #12121a 100%);
        border: 1px solid #333;
        border-top: 3px solid var(--accent-color); /* Top Highlight */
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
        height: 100%;
    }
    .active-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Header */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .titles {
        display: flex;
        flex-direction: column;
    }
    .category-badge {
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        color: #71717a;
        letter-spacing: 0.5px;
    }
    .strike-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--accent-color);
        font-family: "JetBrains Mono", monospace;
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #333;
    }
    .status-dot.connected {
        background: #22c55e;
        box-shadow: 0 0 8px #22c55e;
        animation: pulse 2s infinite;
    }

    /* Price Section */
    .price-section {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .ltp {
        font-size: 24px;
        font-weight: 700;
        color: #fff;
        font-family: "JetBrains Mono", monospace;
    }
    .change {
        font-size: 13px;
        font-weight: 600;
        font-family: "JetBrains Mono", monospace;
    }

    /* OHLC */
    .ohlc-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 4px;
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 6px;
    }
    .ohlc-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .lbl {
        font-size: 9px;
        color: #71717a;
        font-weight: 700;
    }
    .val {
        font-size: 11px;
        color: #d4d4d8;
        font-family: "JetBrains Mono", monospace;
    }
    .val.high {
        color: #22c55e;
    }
    .val.low {
        color: #ef4444;
    }

    .divider {
        height: 1px;
        background: #333;
    }

    /* History List */
    .history-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
        overflow-y: auto;
        flex-grow: 1;
        padding-right: 2px; /* Scrollbar space */
    }

    .h-item {
        display: grid;
        grid-template-columns: 80px 1fr;
        gap: 12px;
        padding: 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid transparent;
    }
    .h-item.live {
        background: rgba(34, 197, 94, 0.05); /* Slight green tint */
        border-color: rgba(34, 197, 94, 0.2);
    }

    .h-left {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        padding-right: 8px;
    }
    .h-time {
        font-size: 10px;
        color: #71717a;
        font-weight: 600;
    }
    .h-price {
        font-size: 14px;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
        color: #fff;
    }

    .h-right {
        display: flex;
        flex-direction: column;
        gap: 2px;
        justify-content: center;
    }

    .m-row {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 10px;
        font-family: "JetBrains Mono", monospace;
    }
    .m-row .lbl {
        color: #71717a;
        width: 25px;
    } /* Fixed label width align */
    .m-row .val {
        color: #d4d4d8;
    }

    .chg {
        margin-left: auto;
        font-size: 9px;
    }

    .ba-row {
        margin-top: 2px;
        padding-top: 2px;
        border-top: 1px dashed rgba(255, 255, 255, 0.05);
        color: #a1a1aa;
        justify-content: space-between;
    }
    .ba {
        display: flex;
        gap: 4px;
    }
    .ba .pr {
        color: #d4d4d8;
    }
    .ba .qty {
        color: #71717a;
    }

    /* Utils */
    .pos {
        color: #22c55e;
    }
    .neg {
        color: #ef4444;
    }

    @keyframes pulse {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
        100% {
            opacity: 1;
        }
    }
</style>
