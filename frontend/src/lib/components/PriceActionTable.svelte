<script lang="ts">
    import { onDestroy } from "svelte";
    import {
        candleDataStore,
        type CandleDetails,
        type Wall,
    } from "$lib/stores/candleData";
    import { marketContext } from "$lib/stores/marketContext";

    // Reactive Sorted Strikes from Context
    let sortedStrikes = $derived(
        Object.keys($marketContext.chain)
            .map(Number)
            .sort((a, b) => a - b),
    );

    function getCandle(key: string | undefined): CandleDetails | null {
        if (!key) return null;
        return $candleDataStore[key] || null;
    }

    // Ratio Helper
    const getRatio = (b: number | undefined, a: number | undefined) => {
        const bid = b || 0;
        const ask = a || 0;
        if (bid === 0 && ask === 0) return 1.0;
        if (ask === 0) return bid > 0 ? 100 : 0;
        return bid / ask;
    };

    // Formatter
    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtPrz = (n: number | undefined) => (n ? n.toFixed(2) : "-");

    // Helper to get Wall Info
    const getWallLen = (walls: Wall[] | undefined) =>
        walls ? walls.length : 0;

    // Calculate Min Spread for Highlighting
    let minCeSpread = $derived(
        Math.min(
            ...sortedStrikes.map(
                (s) =>
                    getCandle($marketContext.chain[s].CE)?.bid_ask?.spread ||
                    Infinity,
            ),
        ),
    );
    let minPeSpread = $derived(
        Math.min(
            ...sortedStrikes.map(
                (s) =>
                    getCandle($marketContext.chain[s].PE)?.bid_ask?.spread ||
                    Infinity,
            ),
        ),
    );

    // Calculate Max Values for Highlighting (Bid=Green, Ask=Red)
    // Calculate Max Values for Highlighting (Bid=Green, Ask=Red)
    const getMax = (
        keys: (string | undefined)[],
        selector: (c: CandleDetails) => number,
    ) =>
        Math.max(
            ...keys.map((k) => {
                if (!k) return 0;
                const c = getCandle(k);
                return c ? selector(c) : 0;
            }),
        );

    // REMOVED TotBid/TotAsk Max Derivations

    let maxCeBestBidQ = $derived(
        getMax(
            sortedStrikes.map((s) => $marketContext.chain[s].CE),
            (c) => c.bid_ask?.best_bid_qty || 0,
        ),
    );
    let maxCeBestAskQ = $derived(
        getMax(
            sortedStrikes.map((s) => $marketContext.chain[s].CE),
            (c) => c.bid_ask?.best_ask_qty || 0,
        ),
    );

    // REMOVED ALL Max Wall Derivations

    // REMOVED TotBid/TotAsk Max Derivations

    let maxPeBestBidQ = $derived(
        getMax(
            sortedStrikes.map((s) => $marketContext.chain[s].PE),
            (c) => c.bid_ask?.best_bid_qty || 0,
        ),
    );
    let maxPeBestAskQ = $derived(
        getMax(
            sortedStrikes.map((s) => $marketContext.chain[s].PE),
            (c) => c.bid_ask?.best_ask_qty || 0,
        ),
    );

    // REMOVED ALL Max Wall Derivations
</script>

<div class="pa-table-container">
    <div class="table-header">
        <h3>Price Action / Market Depth</h3>
    </div>
    <div class="table-wrapper">
        <table class="pa-table">
            <thead>
                <tr class="main-header">
                    <th colspan="10" class="call-side">CALLS (CE)</th>
                    <th class="strike-col">STRIKE</th>
                    <th colspan="10" class="put-side">PUTS (PE)</th>
                </tr>
                <tr class="sub-header">
                    <!-- CE (Mirrored) -->
                    <!-- CE (Mirrored) -->
                    <th>Ratio</th>

                    <th>Best Bid Pr</th>
                    <th>Best Bid Qty</th>
                    <th>Best Ask Pr</th>
                    <th>Best Ask Qty</th>
                    <th>Wall</th>

                    <th>Spread</th>
                    <th>Spr Diff</th>

                    <th><!-- Strike --></th>

                    <!-- PE (Normal) -->
                    <th>Spr Diff</th>
                    <th>Spread</th>
                    <th>Wall</th>

                    <th>Best Ask Qty</th>
                    <th>Best Ask Pr</th>
                    <th>Best Bid Qty</th>
                    <th>Best Bid Pr</th>
                    <th>Ratio</th>
                </tr>
            </thead>
            <tbody>
                {#each sortedStrikes as strike}
                    {@const ceKey = $marketContext.chain[strike].CE}
                    {@const peKey = $marketContext.chain[strike].PE}
                    {@const ceData = getCandle(ceKey)}
                    {@const peData = getCandle(peKey)}

                    {@const ceBA = ceData?.bid_ask}
                    {@const peBA = peData?.bid_ask}

                    {@const ceRatio = getRatio(
                        ceBA?.total_bid_qty,
                        ceBA?.total_ask_qty,
                    )}
                    {@const peRatio = getRatio(
                        peBA?.total_bid_qty,
                        peBA?.total_ask_qty,
                    )}

                    {@const ceBidWallLen = getWallLen(ceBA?.bid_walls)}
                    {@const ceAskWallLen = getWallLen(ceBA?.ask_walls)}
                    {@const peBidWallLen = getWallLen(peBA?.bid_walls)}
                    {@const peAskWallLen = getWallLen(peBA?.ask_walls)}

                    <tr
                        class="data-row"
                        class:atm-row={strike === $marketContext.atmStrike}
                    >
                        <!-- CE SIDE -->

                        <td
                            class="cell-qty"
                            class:bg-green={ceRatio > 1.5}
                            class:bg-red={ceRatio < 0.7}
                            class:bg-yellow={ceRatio >= 0.8 && ceRatio <= 1.2}
                        >
                            {ceRatio.toFixed(2)}
                        </td>

                        <td class="cell-price"
                            >{fmtPrz(ceBA?.best_bid_price)}</td
                        >
                        <td
                            class="cell-qty"
                            class:bg-green={ceBA?.best_bid_qty ===
                                maxCeBestBidQ && maxCeBestBidQ > 0}
                            >{fmt(ceBA?.best_bid_qty)}</td
                        >
                        <td class="cell-price"
                            >{fmtPrz(ceBA?.best_ask_price)}</td
                        >
                        <td
                            class="cell-qty"
                            class:bg-red={ceBA?.best_ask_qty ===
                                maxCeBestAskQ && maxCeBestAskQ > 0}
                            >{fmt(ceBA?.best_ask_qty)}</td
                        >

                        <td
                            class="cell-wall"
                            class:bg-green={ceBidWallLen > ceAskWallLen}
                            class:bg-red={ceAskWallLen > ceBidWallLen}
                        >
                            {ceBidWallLen} / {ceAskWallLen}
                        </td>

                        <!-- Spread Info -->
                        <td
                            class="cell-muted"
                            class:spread-min={ceBA?.spread === minCeSpread &&
                                (ceBA?.spread ?? 0) > 0}
                            >{fmtPrz(ceBA?.spread)}</td
                        >
                        <td
                            class="cell-muted"
                            class:pos={(ceData?.spread_diff ?? 0) > 0}
                            class:neg={(ceData?.spread_diff ?? 0) < 0}
                            >{fmtPrz(ceData?.spread_diff)}</td
                        >

                        <!-- STRIKE -->
                        <td class="cell-strike">{strike}</td>

                        <!-- PE SIDE -->
                        <!-- Spread Info -->
                        <td
                            class="cell-muted"
                            class:pos={(peData?.spread_diff ?? 0) > 0}
                            class:neg={(peData?.spread_diff ?? 0) < 0}
                            >{fmtPrz(peData?.spread_diff)}</td
                        >
                        <td
                            class="cell-muted"
                            class:spread-min={peBA?.spread === minPeSpread &&
                                (peBA?.spread ?? 0) > 0}
                            >{fmtPrz(peBA?.spread)}</td
                        >

                        <td
                            class="cell-wall"
                            class:bg-green={peBidWallLen > peAskWallLen}
                            class:bg-red={peAskWallLen > peBidWallLen}
                        >
                            {peBidWallLen} / {peAskWallLen}
                        </td>

                        <td
                            class="cell-qty"
                            class:bg-red={peBA?.best_ask_qty ===
                                maxPeBestAskQ && maxPeBestAskQ > 0}
                            >{fmt(peBA?.best_ask_qty)}</td
                        >
                        <td class="cell-price"
                            >{fmtPrz(peBA?.best_ask_price)}</td
                        >
                        <td
                            class="cell-qty"
                            class:bg-green={peBA?.best_bid_qty ===
                                maxPeBestBidQ && maxPeBestBidQ > 0}
                            >{fmt(peBA?.best_bid_qty)}</td
                        >
                        <td class="cell-price"
                            >{fmtPrz(peBA?.best_bid_price)}</td
                        >

                        <td
                            class="cell-qty"
                            class:bg-green={peRatio > 1.5}
                            class:bg-red={peRatio < 0.7}
                            class:bg-yellow={peRatio >= 0.8 && peRatio <= 1.2}
                        >
                            {peRatio.toFixed(2)}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>

        {#if sortedStrikes.length === 0}
            <div class="empty-state">
                <p>No Data. Select Index in Header.</p>
            </div>
        {/if}
    </div>
</div>

<style>
    .pa-table-container {
        margin-top: 24px;
        background: var(--bg-card, #1e1e1e);
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding-bottom: 8px;
    }
    .table-header {
        padding: 16px;
        border-bottom: 1px solid #333;
    }
    .table-header h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #e4e4e7;
    }

    .table-wrapper {
        overflow-x: auto;
    }

    .pa-table {
        width: 100%;
        border-collapse: collapse;
        font-family: "JetBrains Mono", monospace;
        font-size: 11px;
    }

    th,
    td {
        padding: 6px 8px;
        text-align: center;
        border-bottom: 1px solid #333;
        white-space: nowrap;
    }

    .main-header th {
        background: #27272a;
        color: #fff;
        font-size: 12px;
        font-weight: 700;
        padding: 10px;
    }
    .sub-header th {
        background: #27272a;
        color: #a1a1aa;
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
    }

    .call-side {
        border-bottom: 2px solid #22c55e;
    }
    .put-side {
        border-bottom: 2px solid #ef4444;
    }

    .strike-col,
    .cell-strike {
        background: #3f3f46;
        color: #fbbf24;
        font-weight: bold;
        font-size: 12px;
        border-left: 1px solid #444;
        border-right: 1px solid #444;
        position: sticky;
        left: 0; /* Optional: Sticky Strike? No, hard to do with horizontal scroll unless careful */
    }

    .data-row:hover {
        background: rgba(255, 255, 255, 0.03);
    }
    .atm-row {
        background: rgba(59, 130, 246, 0.05);
    }

    .cell-qty {
        color: #a1a1aa;
    }
    .cell-price {
        color: #e4e4e7;
        font-weight: 600;
    }
    .cell-wall {
        color: #f472b6;
        font-weight: 700;
    }

    /* Colors */
    .bg-green {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80 !important;
        font-weight: 600;
    }
    .bg-red {
        background-color: rgba(239, 68, 68, 0.15);
        color: #fca5a5 !important;
        font-weight: 600;
    }

    .spread-min {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80 !important;
        font-weight: 700;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .pos {
        color: #22c55e;
    }
    .neg {
        color: #ef4444;
    }

    .bg-yellow {
        background-color: rgba(234, 179, 8, 0.15);
        color: #facc15 !important;
        font-weight: 600;
    }

    .empty-state {
        padding: 20px;
        text-align: center;
        color: #666;
    }
</style>
