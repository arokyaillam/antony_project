<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import {
        historicalDataStore,
        fetchSubscribedHistory,
    } from "$lib/stores/historicalData";
    import { marketContext } from "$lib/stores/marketContext";
    import {
        marketDataStore,
        type InstrumentFeed,
    } from "$lib/stores/marketData";
    import OpeningStatus from "$lib/components/OpeningStatus.svelte";
    import { subscribeToFeed, unsubscribeFromFeed } from "$lib/stores/feed";

    let loading = false;
    let error = "";
    let interval = "day";
    let loaded = false;

    // Helper to format date YYYY-MM-DD
    const isoDate = (d: Date) => d.toISOString().split("T")[0];

    onMount(async () => {
        loading = true;
        try {
            // Fetch last 5 days to be safe, but we only want the latest one
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            const start = new Date(yesterday);
            start.setDate(start.getDate() - 5);

            const toDate = isoDate(yesterday);
            const fromDate = isoDate(start);

            console.log(
                `Fetching history for strategy: ${fromDate} to ${toDate}`,
            );

            await fetchSubscribedHistory(interval, fromDate, toDate);
            loaded = true;

            // Subscribe to live feed for all fetched instruments to get "Live Open"
            // We need to wait for history to know which instruments we have?
            // Actually fetchSubscribedHistory uses marketContext, so we can use that keys
            const keys = Object.keys($marketContext.instruments);
            if (keys.length > 0) {
                subscribeToFeed(keys, "full_d30"); // Subscribe to full feed to ensure OHLC
            }
        } catch (e) {
            error = e instanceof Error ? e.message : String(e);
        } finally {
            loading = false;
        }
    });

    onDestroy(() => {
        // Optional: Unsubscribe if we don't want to keep streaming in background
        // But typically we might want to keep it if user navigates back quickly.
        // For now, let's leave it or unsubscribe to be clean.
        const keys = Object.keys($marketContext.instruments);
        if (keys.length > 0) {
            unsubscribeFromFeed(keys);
        }
    });

    function fmtDate(ts: string) {
        return new Date(ts).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    }

    function getDisplayName(key: string) {
        const meta = $marketContext.instruments[key];
        if (meta) {
            if (meta.strike && meta.type) {
                return `${meta.strike} ${meta.type}`;
            }
            return meta.symbol || key;
        }
        if (key.includes("|")) return key.split("|")[1];
        return key;
    }

    // Helper to get Live Open from marketDataStore
    function getLiveOpen(
        key: string,
        feedMap: Record<string, InstrumentFeed>,
    ): number {
        const feed = feedMap[key];
        if (!feed?.fullFeed) return 0;

        // Check Index Feed or Market Feed
        const ff = feed.fullFeed.indexFF || feed.fullFeed.marketFF;
        if (!ff?.marketOHLC?.ohlc) return 0;

        // Assuming the first OHLC entry is the day's OHLC or we look for specific interval
        // Usually Upstox sends '1d' or similar. Let's try to find it or pick first.
        const dayOhlc =
            ff.marketOHLC.ohlc.find(
                (o) => o.interval === "1d" || o.interval === "day",
            ) || ff.marketOHLC.ohlc[0];
        return dayOhlc?.open || 0;
    }

    // Helper to get LTP just in case
    function getLTP(
        key: string,
        feedMap: Record<string, InstrumentFeed>,
    ): number {
        const feed = feedMap[key];
        const ff = feed?.fullFeed?.indexFF || feed?.fullFeed?.marketFF;
        return ff?.ltpc?.ltp || 0;
    }
</script>

<div class="page-container">
    <header class="page-header">
        <h1>Strategy Test - Last Candle</h1>
        <div class="status">
            {#if loading}
                <span class="badge loading">Loading...</span>
            {:else if error}
                <span class="badge error">{error}</span>
            {:else if loaded}
                <span class="badge success">Loaded</span>
            {/if}
        </div>
    </header>

    <div class="content">
        {#each Object.entries($historicalDataStore) as [instrument, intervals]}
            {@const candles = intervals[interval] || []}
            <!-- User requested the "first row" from history, which corresponds to index 0 -->
            {@const lastCandle = candles.length > 0 ? candles[0] : null}
            {@const liveOpen = getLiveOpen(instrument, $marketDataStore)}
            {@const currentLtp = getLTP(instrument, $marketDataStore)}

            <div class="instrument-card">
                <div class="card-header">
                    <div class="title-group">
                        <h2>{getDisplayName(instrument)}</h2>
                        <span class="tag">Last Traded Session</span>
                    </div>
                </div>

                {#if lastCandle}
                    <div class="analysis-section">
                        <div class="status-row">
                            <div class="live-info">
                                <span class="label">Live Open</span>
                                <span class="value live-val"
                                    >{liveOpen || "Waiting..."}</span
                                >
                            </div>
                            <OpeningStatus
                                prevHigh={lastCandle.high}
                                prevLow={lastCandle.low}
                                prevClose={lastCandle.close}
                                {liveOpen}
                            />
                        </div>
                    </div>

                    <div class="candle-grid">
                        <div class="stat-item">
                            <span class="label">Date</span>
                            <span class="value date"
                                >{fmtDate(lastCandle.timestamp)}</span
                            >
                        </div>
                        <div class="stat-item">
                            <span class="label">Open</span>
                            <span class="value"
                                >{lastCandle.open.toFixed(2)}</span
                            >
                        </div>
                        <div class="stat-item">
                            <span class="label">High</span>
                            <span class="value"
                                >{lastCandle.high.toFixed(2)}</span
                            >
                        </div>
                        <div class="stat-item">
                            <span class="label">Low</span>
                            <span class="value"
                                >{lastCandle.low.toFixed(2)}</span
                            >
                        </div>
                        <div class="stat-item">
                            <span class="label">Close</span>
                            <span class="value close"
                                >{lastCandle.close.toFixed(2)}</span
                            >
                        </div>
                        <div class="stat-item">
                            <span class="label">Volume</span>
                            <span class="value"
                                >{lastCandle.volume.toLocaleString()}</span
                            >
                        </div>
                    </div>
                {:else}
                    <div class="empty">No Data Found</div>
                {/if}
            </div>
        {/each}

        {#if !loading && Object.keys($historicalDataStore).length === 0}
            <div class="empty-state">
                <p>No subscribed instruments found or no data fetched.</p>
            </div>
        {/if}
    </div>
</div>

<style>
    .page-container {
        padding: 24px;
        max-width: 800px;
        margin: 0 auto;
        color: #e4e4e7;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
        padding-bottom: 16px;
        border-bottom: 1px solid #333;
    }

    h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(to right, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .status .badge {
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 600;
    }
    .loading {
        background: #3b82f6;
        color: white;
    }
    .error {
        background: #ef4444;
        color: white;
    }
    .success {
        background: #22c55e;
        color: white;
    }

    .content {
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .instrument-card {
        background: #1e1e1e;
        border-radius: 12px;
        border: 1px solid #333;
        overflow: hidden;
    }

    .card-header {
        background: #27272a;
        padding: 16px;
        border-bottom: 1px solid #333;
    }

    .title-group {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    h2 {
        margin: 0;
        font-size: 16px;
        font-family: "JetBrains Mono", monospace;
        color: #fbbf24;
    }

    .tag {
        font-size: 11px;
        background: #3f3f46;
        padding: 2px 8px;
        border-radius: 4px;
        color: #e4e4e7;
    }

    .analysis-section {
        padding: 16px 24px;
        background: rgba(0, 0, 0, 0.2);
        border-bottom: 1px solid #333;
    }

    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .live-info {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }

    .live-val {
        color: #fbbf24;
        font-weight: bold;
    }

    .candle-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        padding: 24px;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .label {
        font-size: 11px;
        color: #71717a;
        text-transform: uppercase;
        font-weight: 600;
    }

    .value {
        font-family: "JetBrains Mono", monospace;
        font-size: 18px;
        color: #e4e4e7;
    }

    .date {
        color: #a1a1aa;
        font-size: 14px;
    }

    .close {
        color: #22c55e;
        font-weight: bold;
    }

    .empty {
        padding: 24px;
        text-align: center;
        color: #52525b;
        font-style: italic;
    }

    .empty-state {
        text-align: center;
        margin-top: 48px;
        color: #52525b;
    }
</style>
