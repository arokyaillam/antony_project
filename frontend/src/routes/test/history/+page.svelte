<script lang="ts">
    import { onMount } from "svelte";
    import {
        historicalDataStore,
        fetchSubscribedHistory,
    } from "$lib/stores/historicalData";
    import { marketContext } from "$lib/stores/marketContext";

    let loading = false;
    let error = "";
    let interval = "day"; // User requested "day" only
    let loaded = false;

    // Helper to format date YYYY-MM-DD
    const isoDate = (d: Date) => d.toISOString().split("T")[0];

    onMount(async () => {
        loading = true;
        try {
            // "Previous day irunthu oru 5 days"
            // End Date = Yesterday
            // Start Date = Yesterday - 5 days
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            const start = new Date(yesterday);
            start.setDate(start.getDate() - 5);

            const toDate = isoDate(yesterday);
            const fromDate = isoDate(start);

            console.log(`Fetching history: ${fromDate} to ${toDate}`);

            await fetchSubscribedHistory(interval, fromDate, toDate);
            loaded = true;
        } catch (e) {
            error = e instanceof Error ? e.message : String(e);
        } finally {
            loading = false;
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
            // If it has strike & type, format nicely
            if (meta.strike && meta.type) {
                return `${meta.strike} ${meta.type}`;
            }
            // Fallback to symbol or name if available match?
            // Actually "symbol" field usually has the trading symbol
            return meta.symbol || key;
        }
        // Basic fallback clean up if it's "NSE_INDEX|..."
        if (key.includes("|")) return key.split("|")[1];
        return key;
    }
</script>

<div class="page-container">
    <header class="page-header">
        <h1>Historical Data Test</h1>
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
            <div class="instrument-card">
                <div class="card-header">
                    <h2>{getDisplayName(instrument)}</h2>
                    <span class="count">{candles.length} Days</span>
                </div>

                {#if candles.length > 0}
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Open</th>
                                    <th>High</th>
                                    <th>Low</th>
                                    <th>Close</th>
                                    <th>Volume</th>
                                    <th>OI</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each candles as candle}
                                    <tr>
                                        <td class="date"
                                            >{fmtDate(candle.timestamp)}</td
                                        >
                                        <td class="num"
                                            >{candle.open.toFixed(2)}</td
                                        >
                                        <td class="num"
                                            >{candle.high.toFixed(2)}</td
                                        >
                                        <td class="num"
                                            >{candle.low.toFixed(2)}</td
                                        >
                                        <td class="num close"
                                            >{candle.close.toFixed(2)}</td
                                        >
                                        <td class="num"
                                            >{candle.volume.toLocaleString()}</td
                                        >
                                        <td class="num"
                                            >{(
                                                candle.oi || 0
                                            ).toLocaleString()}</td
                                        >
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
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
        max-width: 1200px;
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
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #333;
    }

    h2 {
        margin: 0;
        font-size: 16px;
        font-family: "JetBrains Mono", monospace;
        color: #fbbf24;
    }

    .count {
        font-size: 12px;
        color: #71717a;
    }

    .table-wrapper {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: "JetBrains Mono", monospace;
    }

    th {
        background: #18181b;
        color: #a1a1aa;
        font-weight: 600;
        text-align: right;
        padding: 12px 16px;
        font-size: 11px;
        text-transform: uppercase;
    }
    th:first-child {
        text-align: left;
    }

    td {
        padding: 12px 16px;
        border-bottom: 1px solid #27272a;
        color: #d4d4d8;
        text-align: right;
    }
    td:first-child {
        text-align: left;
    }

    tr:last-child td {
        border-bottom: none;
    }
    tr:hover {
        background: rgba(255, 255, 255, 0.02);
    }

    .date {
        color: #a1a1aa;
    }
    .close {
        color: #fff;
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
