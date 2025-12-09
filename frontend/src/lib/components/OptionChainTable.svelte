<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { marketContext } from "$lib/stores/marketContext";
    import { subscribeToStream } from "$lib/stores/stream";

    // Live Data Map: InstrumentKey -> FullFeed Data
    let liveData = $state<Record<string, any>>({});

    // Sort strikes for display
    let sortedStrikes = $derived(
        Object.keys($marketContext.chain)
            .map(Number)
            .sort((a, b) => a - b),
    );

    // Unsubscribe function
    let unsubscribeStream: () => void;

    onMount(() => {
        unsubscribeStream = subscribeToStream((data: any) => {
            if (data?.feeds) {
                // Merge new data into liveData
                // Note: creating a new object to trigger reactivity if needed,
                // though usually specific field access is enough.
                // For high freq, we might want to optimize this.
                const newFeeds = data.feeds;
                // DEBUG: Log the first key to see structure
                const firstKey = Object.keys(newFeeds)[0];
                if (firstKey) {
                    console.log(
                        "Stream Data Sample:",
                        firstKey,
                        newFeeds[firstKey],
                    );
                }

                for (const key in newFeeds) {
                    liveData[key] = newFeeds[key];
                }
            }
        });
    });

    onDestroy(() => {
        if (unsubscribeStream) {
            unsubscribeStream();
        }
    });

    // Helper to get value safely
    function getValue(key: string | undefined, field: string): string | number {
        if (!key || !liveData[key]) return "-";

        const ff = liveData[key].fullFeed;
        if (!ff) return "-";

        // Try to find LTP in various possible fields
        // Options usually use marketFF, Indices use indexFF, Futures use marketFF
        const ltpc = ff.marketFF?.ltpc || ff.indexFF?.ltpc || ff.optionFF?.ltpc;
        const ohlc = ff.marketOHLC?.ohlc?.[0];

        if (field === "ltp") return ltpc?.ltp?.toFixed(2) ?? "-";
        if (field === "oi") return ohlc?.oi ?? "-";
        if (field === "vol") return ohlc?.vol ?? "-";

        return "-";
    }

    // Highlighting ATM
    function isATM(strike: number): boolean {
        return strike === $marketContext.atmStrike;
    }
</script>

<div class="option-chain-container">
    <table class="chain-table">
        <thead>
            <tr>
                <th colspan="3" class="ce-header">CALLS (CE)</th>
                <th class="strike-header">STRIKE</th>
                <th colspan="3" class="pe-header">PUTS (PE)</th>
            </tr>
            <tr class="sub-header">
                <th>Vol</th>
                <th>OI</th>
                <th>LTP</th>
                <th>Price</th>
                <th>LTP</th>
                <th>OI</th>
                <th>Vol</th>
            </tr>
        </thead>
        <tbody>
            {#each sortedStrikes as strike}
                {@const ceKey = $marketContext.chain[strike].CE}
                {@const peKey = $marketContext.chain[strike].PE}

                <tr class:atm-row={isATM(strike)}>
                    <!-- CE DATA -->
                    <td class="cell-vol">{getValue(ceKey, "vol")}</td>
                    <td class="cell-oi">{getValue(ceKey, "oi")}</td>
                    <td class="cell-ltp ce-color">{getValue(ceKey, "ltp")}</td>

                    <!-- STRIKE -->
                    <td class="cell-strike">{strike}</td>

                    <!-- PE DATA -->
                    <td class="cell-ltp pe-color">{getValue(peKey, "ltp")}</td>
                    <td class="cell-oi">{getValue(peKey, "oi")}</td>
                    <td class="cell-vol">{getValue(peKey, "vol")}</td>
                </tr>
            {/each}
        </tbody>
    </table>

    {#if sortedStrikes.length === 0}
        <div class="empty-state">
            Select an Index above to load Option Chain
        </div>
    {/if}
</div>

<style>
    .option-chain-container {
        width: 100%;
        overflow-x: auto;
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        margin-top: 16px;
    }

    .chain-table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--font-mono);
        font-size: 13px;
    }

    th,
    td {
        padding: 8px 12px;
        text-align: center;
        border-bottom: 1px solid var(--border-color);
    }

    th {
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .ce-header {
        color: var(--accent-green);
        border-right: 1px solid var(--border-color);
    }
    .pe-header {
        color: var(--accent-red);
        border-left: 1px solid var(--border-color);
    }
    .strike-header {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .sub-header th {
        font-size: 10px;
        color: var(--text-muted);
    }

    .cell-strike {
        background: var(--bg-secondary);
        font-weight: 700;
        color: var(--text-primary);
        border-left: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color);
    }

    .atm-row td {
        background: rgba(255, 255, 255, 0.03);
    }

    .atm-row .cell-strike {
        background: var(--accent-blue-dim, rgba(59, 130, 246, 0.1));
        color: var(--accent-blue);
        border: 1px solid var(--accent-blue);
    }

    .ce-color {
        color: var(--accent-green);
    }
    .pe-color {
        color: var(--accent-red);
    }

    .cell-vol,
    .cell-oi {
        color: var(--text-muted);
        font-size: 12px;
    }

    .empty-state {
        padding: 40px;
        text-align: center;
        color: var(--text-muted);
        font-style: italic;
    }
</style>
