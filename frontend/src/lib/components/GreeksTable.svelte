<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
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

    // Formatter
    const fmt = (n: number | undefined, d: number = 4) =>
        n !== undefined ? n.toFixed(d) : "-";

    // Greeks Formatting (usually 4 decimals)
    const fmtG = (n: number | undefined) => fmt(n, 4);
</script>

<div class="greeks-table-container">
    <div class="table-header">
        <h3>Greeks Analysis</h3>
    </div>
    <div class="table-wrapper">
        <table class="greeks-table">
            <thead>
                <tr class="main-header">
                    <th colspan="10" class="call-side">CALLS (CE)</th>
                    <th class="strike-col">STRIKE</th>
                    <th colspan="10" class="put-side">PUTS (PE)</th>
                </tr>
                <tr class="sub-header">
                    <!-- CE (Mirrored: IV -> Delta) -->
                    <th>IV Diff</th>
                    <th>IV</th>
                    <th>Vega Diff</th>
                    <th>Vega</th>
                    <th>Gamma Diff</th>

                    <th>Gamma</th>
                    <th>Theta Diff</th>
                    <th>Theta</th>
                    <th>Delta Diff</th>
                    <th>Delta</th>

                    <th><!-- Strike --></th>

                    <!-- PE (Normal: Delta -> IV) -->
                    <th>Delta</th>
                    <th>Delta Diff</th>
                    <th>Theta</th>
                    <th>Theta Diff</th>
                    <th>Gamma</th>
                    <th>Gamma Diff</th>
                    <th>Vega</th>
                    <th>Vega Diff</th>
                    <th>IV</th>

                    <th>IV Diff</th>
                </tr>
            </thead>
            <tbody>
                {#each sortedStrikes as strike}
                    {@const ceKey = $marketContext.chain[strike].CE}
                    {@const peKey = $marketContext.chain[strike].PE}
                    {@const ceData = getCandle(ceKey)}
                    {@const peData = getCandle(peKey)}

                    {@const ceG = ceData?.greeks}
                    {@const peG = peData?.greeks}

                    <!-- Determine color for diffs -->
                    {@const pos = (n: number | undefined) => (n || 0) > 0}
                    {@const neg = (n: number | undefined) => (n || 0) < 0}

                    <tr
                        class="data-row"
                        class:atm-row={strike === $marketContext.atmStrike}
                    >
                        <!-- CE SIDE (Mirrored) -->
                        <td
                            class="cell-muted"
                            class:pos={pos(ceData?.iv_diff)}
                            class:neg={neg(ceData?.iv_diff)}
                            >{fmtG(ceData?.iv_diff)}</td
                        >
                        <td class="cell-val">{fmtG(ceData?.iv)}</td>

                        <td
                            class="cell-muted"
                            class:pos={pos(ceData?.vega_diff)}
                            class:neg={neg(ceData?.vega_diff)}
                            >{fmtG(ceData?.vega_diff)}</td
                        >
                        <td class="cell-val">{fmtG(ceG?.vega)}</td>

                        <td
                            class="cell-muted"
                            class:pos={pos(ceData?.gamma_diff)}
                            class:neg={neg(ceData?.gamma_diff)}
                            >{fmtG(ceData?.gamma_diff)}</td
                        >
                        <td class="cell-val">{fmtG(ceG?.gamma)}</td>

                        <td
                            class="cell-muted"
                            class:pos={pos(ceData?.theta_diff)}
                            class:neg={neg(ceData?.theta_diff)}
                            >{fmtG(ceData?.theta_diff)}</td
                        >
                        <td class="cell-val">{fmtG(ceG?.theta)}</td>

                        <td
                            class="cell-muted"
                            class:pos={pos(ceData?.delta_diff)}
                            class:neg={neg(ceData?.delta_diff)}
                            >{fmtG(ceData?.delta_diff)}</td
                        >
                        <td class="cell-val">{fmtG(ceG?.delta)}</td>

                        <!-- STRIKE -->
                        <td class="cell-strike">{strike}</td>

                        <!-- PE SIDE (Normal) -->
                        <td class="cell-val">{fmtG(peG?.delta)}</td>
                        <td
                            class="cell-muted"
                            class:pos={pos(peData?.delta_diff)}
                            class:neg={neg(peData?.delta_diff)}
                            >{fmtG(peData?.delta_diff)}</td
                        >

                        <td class="cell-val">{fmtG(peG?.theta)}</td>
                        <td
                            class="cell-muted"
                            class:pos={pos(peData?.theta_diff)}
                            class:neg={neg(peData?.theta_diff)}
                            >{fmtG(peData?.theta_diff)}</td
                        >

                        <td class="cell-val">{fmtG(peG?.gamma)}</td>
                        <td
                            class="cell-muted"
                            class:pos={pos(peData?.gamma_diff)}
                            class:neg={neg(peData?.gamma_diff)}
                            >{fmtG(peData?.gamma_diff)}</td
                        >

                        <td class="cell-val">{fmtG(peG?.vega)}</td>
                        <td
                            class="cell-muted"
                            class:pos={pos(peData?.vega_diff)}
                            class:neg={neg(peData?.vega_diff)}
                            >{fmtG(peData?.vega_diff)}</td
                        >

                        <td class="cell-val">{fmtG(peData?.iv)}</td>
                        <td
                            class="cell-muted"
                            class:pos={pos(peData?.iv_diff)}
                            class:neg={neg(peData?.iv_diff)}
                            >{fmtG(peData?.iv_diff)}</td
                        >
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
    .greeks-table-container {
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

    .greeks-table {
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
        left: 0;
    }

    .data-row:hover {
        background: rgba(255, 255, 255, 0.03);
    }
    .atm-row {
        background: rgba(59, 130, 246, 0.05);
    }

    .cell-val {
        color: #e4e4e7;
        font-weight: 500;
    }
    .cell-muted {
        color: #71717a;
    }

    .pos {
        color: #22c55e;
    }
    .neg {
        color: #ef4444;
    }

    .empty-state {
        padding: 20px;
        text-align: center;
        color: #666;
    }
</style>
