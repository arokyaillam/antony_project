<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
    } from "$lib/stores/candleData";
    import { marketContext } from "$lib/stores/marketContext";

    // Computed: Flattened list of strikes with data
    let activeData = $derived(
        Object.keys($marketContext.chain).map((strikeStr) => {
            const strike = Number(strikeStr);
            const ceKey = $marketContext.chain[strike].CE;
            const peKey = $marketContext.chain[strike].PE;
            const ceData = ceKey ? $candleDataStore[ceKey] : null;
            const peData = peKey ? $candleDataStore[peKey] : null;
            return { strike, ceData, peData };
        }),
    );

    // Find Max OI / Vol
    let maxCeOI = $derived(
        activeData.reduce(
            (prev, curr) =>
                (curr.ceData?.oi || 0) > (prev?.ceData?.oi || 0) ? curr : prev,
            activeData[0],
        ),
    );

    let maxPeOI = $derived(
        activeData.reduce(
            (prev, curr) =>
                (curr.peData?.oi || 0) > (prev?.peData?.oi || 0) ? curr : prev,
            activeData[0],
        ),
    );

    let maxCeVol = $derived(
        activeData.reduce(
            (prev, curr) =>
                (curr.ceData?.volume_1m || 0) > (prev?.ceData?.volume_1m || 0)
                    ? curr
                    : prev,
            activeData[0],
        ),
    );

    let maxPeVol = $derived(
        activeData.reduce(
            (prev, curr) =>
                (curr.peData?.volume_1m || 0) > (prev?.peData?.volume_1m || 0)
                    ? curr
                    : prev,
            activeData[0],
        ),
    );

    // Formatter
    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtPr = (n: number | undefined) => (n ? n.toFixed(2) : "-");
    const fmtG = (n: number | undefined) => (n ? n.toFixed(4) : "-");
</script>

<div class="active-strikes-container">
    <h2 class="section-title">🔥 Active Strikes</h2>

    {#if activeData.length > 0}
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Strike</th>
                        <th>OI (Chg)</th>
                        <th>Vol (Chg)</th>
                        <th>LTP (Chg)</th>
                        <th>Bid (Qty)</th>
                        <th>Ask (Qty)</th>
                        <th>ATP</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Helper to render a row -->
                    {#snippet row(title, data, strike, type)}
                        {#if data}
                            <tr class="row-{type}">
                                <td class="category-cell">
                                    <span class="badge">{title}</span>
                                </td>
                                <td class="strike-cell">
                                    <span class="strike-val"
                                        >{strike}
                                        {type === "ce" ? "CE" : "PE"}</span
                                    >
                                </td>
                                <td>
                                    <div class="cell-group">
                                        <span class="val">{fmt(data.oi)}</span>
                                        <span
                                            class="sub-val"
                                            class:pos={data.oi_diff > 0}
                                            class:neg={data.oi_diff < 0}
                                        >
                                            {fmt(data.oi_diff)}
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <div class="cell-group">
                                        <span class="val"
                                            >{fmt(data.volume_1m)}</span
                                        >
                                        <span
                                            class="sub-val"
                                            class:pos={data.volume_diff > 0}
                                            class:neg={data.volume_diff < 0}
                                        >
                                            {fmt(data.volume_diff)}
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <div class="cell-group">
                                        <span class="val"
                                            >{fmtPr(data.close)}</span
                                        >
                                        <span
                                            class="sub-val"
                                            class:pos={data.price_diff > 0}
                                            class:neg={data.price_diff < 0}
                                        >
                                            {fmtPr(data.price_diff)}
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <div class="cell-group">
                                        <span class="val"
                                            >{fmtPr(
                                                data.bid_ask.best_bid_price,
                                            )}</span
                                        >
                                        <span class="qty-val"
                                            >({fmt(
                                                data.bid_ask.best_bid_qty,
                                            )})</span
                                        >
                                    </div>
                                </td>
                                <td>
                                    <div class="cell-group">
                                        <span class="val"
                                            >{fmtPr(
                                                data.bid_ask.best_ask_price,
                                            )}</span
                                        >
                                        <span class="qty-val"
                                            >({fmt(
                                                data.bid_ask.best_ask_qty,
                                            )})</span
                                        >
                                    </div>
                                </td>
                                <td>
                                    <span class="val">{fmtPr(data.atp)}</span>
                                </td>
                            </tr>
                        {/if}
                    {/snippet}

                    {@render row(
                        "MAX CE OI",
                        maxCeOI?.ceData,
                        maxCeOI?.strike,
                        "ce",
                    )}
                    {@render row(
                        "MAX PE OI",
                        maxPeOI?.peData,
                        maxPeOI?.strike,
                        "pe",
                    )}
                    {@render row(
                        "MAX CE VOL",
                        maxCeVol?.ceData,
                        maxCeVol?.strike,
                        "ce",
                    )}
                    {@render row(
                        "MAX PE VOL",
                        maxPeVol?.peData,
                        maxPeVol?.strike,
                        "pe",
                    )}
                </tbody>
            </table>
        </div>
    {:else}
        <div class="empty-msg">
            Waiting for market data... <br />
            <span class="sub-msg"
                >Ensure you are connected and have subscribed to an Index.</span
            >
        </div>
    {/if}
</div>

<style>
    .active-strikes-container {
        margin-top: 30px;
        width: 100%;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 16px;
        background: linear-gradient(to right, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    .table-responsive {
        overflow-x: auto;
        background: var(--bg-card, #1e1e1e);
        border: 1px solid var(--border-color, #333);
        border-radius: 12px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    th {
        text-align: left;
        padding: 10px 12px;
        color: #71717a;
        font-weight: 600;
        border-bottom: 1px solid #333;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    td {
        padding: 8px 12px;
        border-bottom: 1px solid #333;
        vertical-align: middle;
        color: #d4d4d8;
    }

    tr:last-child td {
        border-bottom: none;
    }

    .row-ce td.category-cell {
        border-left: 3px solid #22c55e;
    }
    .row-pe td.category-cell {
        border-left: 3px solid #ef4444;
    }

    .badge {
        font-size: 11px;
        font-weight: 800;
        background: rgba(255, 255, 255, 0.05);
        padding: 4px 8px;
        border-radius: 4px;
        color: #e4e4e7;
    }

    .strike-val {
        color: #fbbf24;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
    }

    .cell-group {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .val {
        font-weight: 600;
        font-family: "JetBrains Mono", monospace;
        color: #fff;
    }

    .sub-val {
        font-size: 11px;
        font-family: "JetBrains Mono", monospace;
        color: #71717a;
    }

    .qty-val {
        font-size: 11px;
        color: #a1a1aa;
    }

    .pos {
        color: #22c55e;
    }
    .neg {
        color: #ef4444;
    }

    .empty-msg {
        text-align: center;
        color: #52525b;
        font-style: italic;
        padding: 20px;
    }
    .sub-msg {
        font-size: 12px;
        color: #71717a;
        font-style: normal;
        margin-top: 4px;
        display: block;
    }
</style>
