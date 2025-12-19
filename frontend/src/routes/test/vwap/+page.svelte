<script lang="ts">
    import IndexSelector from "$lib/components/IndexSelector.svelte";
    import { vwapStore, isVwapConnected } from "$lib/stores/vwap";
    import { marketContext } from "$lib/stores/marketContext";
    import { formatCurrency, formatNumber } from "$lib/utils/format";

    function getInstrumentLabel(key: string) {
        const meta = $marketContext.instruments[key];
        if (meta) {
            return `${meta.strike} ${meta.type}`;
        }
        if (key === $marketContext.indexKey) {
            return $marketContext.indexKey.split("|")[1];
        }
        return key;
    }

    // Computed derived state for the table
    // We iterate over the keys in the filtered store

    // Sort keys for stable display
    $effect(() => {
        // console.log("VWAP Store Updated:", $vwapStore);
    });
</script>

<div class="container">
    <header class="header">
        <h1>VWAP Monitor</h1>
        <div class="status">
            <span class="status-indicator" class:connected={$isVwapConnected}
            ></span>
            <span class="status-text">
                {$isVwapConnected ? "Stream Connected" : "Stream Disconnected"}
            </span>
        </div>
    </header>

    <div class="controls">
        <IndexSelector />
    </div>

    <div class="data-grid">
        <div class="card">
            <h2>Live VWAP Data</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Instrument</th>
                            <th class="right">LTP</th>
                            <th class="right">VWAP</th>
                            <th class="right">Diff</th>
                            <th class="right">Volume</th>
                            <th class="right">Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each Object.entries($vwapStore) as [key, data] (key)}
                            {@const diff = data.ltp - data.vwap}
                            <tr>
                                <td class="key">
                                    <div class="instrument-label">
                                        {getInstrumentLabel(key)}
                                    </div>
                                    <div class="instrument-key-sub">{key}</div>
                                </td>
                                <td class="right price"
                                    >{formatCurrency(data.ltp)}</td
                                >
                                <td class="right price"
                                    >{formatCurrency(data.vwap)}</td
                                >
                                <td
                                    class="right diff"
                                    class:positive={diff > 0}
                                    class:negative={diff < 0}
                                >
                                    {formatCurrency(diff)}
                                </td>
                                <td class="right"
                                    >{formatNumber(data.volume)}</td
                                >
                                <td class="right timestamp">
                                    {new Date(
                                        data.timestamp,
                                    ).toLocaleTimeString()}
                                </td>
                            </tr>
                        {:else}
                            <tr>
                                <td colspan="6" class="empty">
                                    No Data. Connect feed and subscribe to
                                    instruments.
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<style>
    .container {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 16px;
        border-bottom: 1px solid #333;
    }

    h1 {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
    }

    .status {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #1e1e1e;
        padding: 6px 12px;
        border-radius: 20px;
    }

    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #ef4444;
    }

    .status-indicator.connected {
        background-color: #22c55e;
    }

    .status-text {
        font-size: 13px;
        font-weight: 500;
        color: #9ca3af;
    }

    .card {
        background: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #333;
    }

    h2 {
        font-size: 18px;
        margin: 0 0 16px 0;
        color: #e5e7eb;
    }

    .table-container {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    th {
        text-align: left;
        padding: 12px;
        color: #9ca3af;
        font-weight: 500;
        border-bottom: 1px solid #333;
    }

    td {
        padding: 12px;
        border-bottom: 1px solid #2a2a2a;
        color: #e5e7eb;
        font-variant-numeric: tabular-nums;
    }

    .right {
        text-align: right;
    }

    .key {
        font-family: monospace;
        color: #60a5fa;
    }

    .instrument-label {
        font-weight: 600;
        color: #60a5fa;
        font-size: 14px;
    }

    .instrument-key-sub {
        font-size: 11px;
        color: #6b7280;
        font-family: monospace;
    }

    .price {
        font-weight: 500;
    }

    .diff.positive {
        color: #22c55e;
    }
    .diff.negative {
        color: #ef4444;
    }

    .empty {
        text-align: center;
        padding: 40px;
        color: #6b7280;
    }

    .timestamp {
        color: #6b7280;
        font-size: 0.9em;
    }
</style>
