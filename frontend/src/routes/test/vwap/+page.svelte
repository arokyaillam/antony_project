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

    // Derived Straddles
    // Group subscribed instruments by strike
    let straddles = $derived.by(() => {
        const chain = $marketContext.chain;
        if (!chain) return [];

        const strikes = Object.keys(chain)
            .map(Number)
            .sort((a, b) => a - b);
        const result = [];

        for (const strike of strikes) {
            const ceKey = chain[strike].CE;
            const peKey = chain[strike].PE;

            // Only include if both legs are subscribed/available in vwapStore (or at least we know about them)
            // Actually, we should check if they are in the current subscription list or vwapStore has data?
            // Let's rely on marketContext chain which only contains what we fetched.
            // But checking if we have keys is safer.

            if (ceKey && peKey) {
                // Get Data
                const ceData = $vwapStore[ceKey];
                const peData = $vwapStore[peKey];

                // Ensure we have at least one leg of data to show something,
                // but for accurate straddle we need both.
                // If missing, consider value 0 or skip?
                // Let's show even if partial, but summing undefined is NaN.

                const ceLtp = ceData?.ltp || 0;
                const peLtp = peData?.ltp || 0;
                const ceVwap = ceData?.vwap || 0;
                const peVwap = peData?.vwap || 0;
                const ceVol = ceData?.volume || 0;
                const peVol = peData?.volume || 0;

                // Determine moneyness tag (approximate)
                const atmStub = $marketContext.atmStrike;
                let tag = "";
                if (Math.abs(strike - atmStub) < 10)
                    tag = "ATM"; // Exact or close
                else if (strike < atmStub) tag = "ITM/OTM";
                else tag = "OTM/ITM";

                // If we exactly match the ATM strike stored in context
                if (strike === atmStub) tag = "ATM";

                result.push({
                    strike,
                    tag,
                    ceKey,
                    peKey,
                    straddleLtp: ceLtp + peLtp,
                    straddleVwap: ceVwap + peVwap,
                    diff: ceLtp + peLtp - (ceVwap + peVwap),
                    combinedVol: ceVol + peVol,
                });
            }
        }
        return result;
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

    <div class="grid-layout">
        <!-- Main Strings Table -->
        <div class="card">
            <h2>Individual Legs</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Instrument</th>
                            <th class="right">LTP</th>
                            <th class="right">VWAP</th>
                            <th class="right">Diff</th>
                            <th class="right">Volume</th>
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
                            </tr>
                        {:else}
                            <tr>
                                <td colspan="5" class="empty">No Data</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Straddles Table -->
        <div class="card">
            <h2>Straddle VWAP (CE + PE)</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Strike</th>
                            <th class="right">Straddle LTP</th>
                            <th class="right">Straddle VWAP</th>
                            <th class="right">Diff</th>
                            <th class="right">Comb. Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each straddles as row (row.strike)}
                            <tr>
                                <td class="key">
                                    <div class="instrument-label">
                                        {row.strike}
                                        {#if row.tag === "ATM"}
                                            <span class="tag atm">ATM</span>
                                        {/if}
                                    </div>
                                    <div class="instrument-key-sub">
                                        Combined
                                    </div>
                                </td>
                                <td class="right price"
                                    >{formatCurrency(row.straddleLtp)}</td
                                >
                                <td class="right price"
                                    >{formatCurrency(row.straddleVwap)}</td
                                >
                                <td
                                    class="right diff"
                                    class:positive={row.diff > 0}
                                    class:negative={row.diff < 0}
                                >
                                    {formatCurrency(row.diff)}
                                </td>
                                <td class="right"
                                    >{formatNumber(row.combinedVol)}</td
                                >
                            </tr>
                        {:else}
                            <tr>
                                <td colspan="5" class="empty"
                                    >No Straddle Data</td
                                >
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
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 24px;
        padding-bottom: 50px;
    }

    .grid-layout {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        align-items: start;
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
        border-bottom: 1px solid #333;
        padding-bottom: 12px;
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
        display: flex;
        flex-direction: column;
    }

    .instrument-label {
        font-weight: 600;
        color: #60a5fa;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .instrument-key-sub {
        font-size: 0.75em;
        color: #6b7280;
        font-family: monospace;
    }

    .tag {
        font-size: 0.75em;
        padding: 2px 6px;
        border-radius: 4px;
        background: #374151;
        color: #9ca3af;
    }

    .tag.atm {
        background: rgba(234, 179, 8, 0.2);
        color: #facc15;
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

    @media (max-width: 1000px) {
        .grid-layout {
            grid-template-columns: 1fr;
        }
    }
</style>
