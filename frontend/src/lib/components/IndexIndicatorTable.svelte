<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
    } from "$lib/stores/candleData";
    import { marketContext } from "$lib/stores/marketContext";

    // Reactive Context
    let atmStrike = $derived($marketContext.atmStrike);
    let chain = $derived($marketContext.chain);

    // Get ATM Candle Data
    let atmCeKey = $derived(atmStrike ? chain[atmStrike]?.CE : undefined);
    let atmPeKey = $derived(atmStrike ? chain[atmStrike]?.PE : undefined);

    let ceData = $derived(atmCeKey ? $candleDataStore[atmCeKey] : null);
    let peData = $derived(atmPeKey ? $candleDataStore[atmPeKey] : null);

    // Formatters
    const fmtPrz = (n: number | undefined | null) => (n ? n.toFixed(2) : "-");

    // ----------------------------
    // CALCULATIONS (Frontend)
    // ----------------------------

    // Straddle Price = CE LTP + PE LTP
    let straddlePrice = $derived((ceData?.close || 0) + (peData?.close || 0));

    // Straddle Change (1m) = (CE Close + PE Close) - (CE Open + PE Open)
    // Logic: How much the combined premium moved in this minute
    let straddleOpen = $derived((ceData?.open || 0) + (peData?.open || 0));
    let straddleChange = $derived(straddlePrice - straddleOpen);
</script>

<div class="indicator-container">
    <div class="header">
        <h3>ATM Indicator ({atmStrike || "N/A"})</h3>
    </div>

    {#if atmStrike && ceData && peData}
        <div class="table-wrapper">
            <table class="ind-table">
                <thead>
                    <tr>
                        <!-- CE Header -->
                        <th colspan="3" class="ce-head">CALLS (CE)</th>
                        <!-- Center Header -->
                        <th colspan="3" class="center-head">STRADDLE</th>
                        <!-- PE Header -->
                        <th colspan="3" class="pe-head">PUTS (PE)</th>
                    </tr>
                    <tr class="sub-head">
                        <!-- CE Cols: 3ATP Chg, 2ATP, 1LTP (Reversed order as per req? "1LTP 2ATP 3ATP change") -->
                        <!-- User said: "1LTP 2ATP 3ATP change same pe side"
                             Usually Left side mirrors Right side or goes outward? 
                             Let's assume standard Left-to-Right reading for now:
                             CE: LTP | ATP | ATP Chg  <-- Center -->

                        <!-- Let's try to mirror from center: 
                             ATP Chg | ATP | LTP || STRADDLE || LTP | ATP | ATP Chg 
                             Wait, user listed "1LTP 2ATP 3ATP change". 
                             If standard reading:
                             CE: LTP, ATP, ATP Chg
                             PE: LTP, ATP, ATP Chg
                             Center: Strike, Straddle Price, Change
                        -->

                        <th>LTP</th>
                        <th>ATP</th>
                        <th>ATP Chg</th>

                        <!-- Center -->
                        <th>Strike</th>
                        <th>Price</th>
                        <th>Change</th>

                        <!-- PE -->
                        <th>LTP</th>
                        <th>ATP</th>
                        <th>ATP Chg</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="data-row">
                        <!-- CE Data -->
                        <td class="txt-val">{fmtPrz(ceData.close)}</td>
                        <td class="txt-val">{fmtPrz(ceData.atp)}</td>
                        <td
                            class="txt-val"
                            class:pos={(ceData.atp_diff || 0) > 0}
                            class:neg={(ceData.atp_diff || 0) < 0}
                        >
                            {fmtPrz(ceData.atp_diff)}
                        </td>

                        <!-- Center Data (Straddle) -->
                        <td class="cell-strike">{atmStrike}</td>
                        <td class="cell-straddle">{fmtPrz(straddlePrice)}</td>
                        <td
                            class="cell-straddle"
                            class:pos={straddleChange > 0}
                            class:neg={straddleChange < 0}
                        >
                            {fmtPrz(straddleChange)}
                        </td>

                        <!-- PE Data -->
                        <td class="txt-val">{fmtPrz(peData.close)}</td>
                        <td class="txt-val">{fmtPrz(peData.atp)}</td>
                        <td
                            class="txt-val"
                            class:pos={(peData.atp_diff || 0) > 0}
                            class:neg={(peData.atp_diff || 0) < 0}
                        >
                            {fmtPrz(peData.atp_diff)}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    {:else}
        <div class="empty">Waiting for Market Data...</div>
    {/if}
</div>

<style>
    .indicator-container {
        margin-top: 24px;
        background: var(--bg-card, #1e1e1e); /* Fallback */
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding-bottom: 8px;
        border: 1px solid #333;
    }
    .header {
        padding: 12px 16px;
        border-bottom: 1px solid #333;
        background: #27272a;
        border-radius: 12px 12px 0 0;
    }
    .header h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #e4e4e7;
    }

    .table-wrapper {
        padding: 0;
        overflow-x: auto;
    }

    .ind-table {
        width: 100%;
        border-collapse: collapse;
        font-family: "JetBrains Mono", monospace;
        font-size: 13px;
    }

    th,
    td {
        padding: 10px 12px;
        text-align: center;
        border-bottom: 1px solid #333;
        white-space: nowrap;
    }

    /* Headers */
    .ce-head {
        color: #22c55e;
        border-bottom: 2px solid #22c55e;
    }
    .pe-head {
        color: #ef4444;
        border-bottom: 2px solid #ef4444;
    }
    .center-head {
        color: #fbbf24;
        border-bottom: 2px solid #fbbf24;
    }

    .sub-head th {
        font-size: 11px;
        text-transform: uppercase;
        color: #a1a1aa;
        background: rgba(0, 0, 0, 0.2);
    }

    /* Cells */
    .cell-strike {
        font-weight: 800;
        color: #fbbf24;
        background: #2a2a30;
    }
    .cell-straddle {
        font-weight: 700;
        font-size: 14px;
    }
    .txt-val {
        color: #e4e4e7;
    }

    /* Colors */
    .pos {
        color: #22c55e;
    }
    .neg {
        color: #ef4444;
    }

    .empty {
        padding: 24px;
        text-align: center;
        color: #666;
    }
</style>
