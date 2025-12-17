<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
        type Wall,
    } from "$lib/stores/candleData";
    import { marketDataStore } from "$lib/stores/marketData";
    import { marketContext } from "$lib/stores/marketContext";

    let sortedStrikes = $derived(
        Object.keys($marketContext.chain)
            .map(Number)
            .sort((a, b) => a - b),
    );

    function getCandle(key: string | undefined): CandleDetails | null {
        if (!key) return null;
        return $candleDataStore[key] || null;
    }

    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtPrz = (n: number | undefined) => (n ? n.toFixed(2) : "-");
    const fmtG = (n: number | undefined) =>
        n !== undefined ? n.toFixed(4) : "-";

    const getWallLen = (walls: Wall[] | undefined) =>
        walls ? walls.length : 0;

    const getRatio = (b: number | undefined, a: number | undefined) => {
        const bid = b || 0;
        const ask = a || 0;
        if (bid === 0 && ask === 0) return 1.0;
        if (ask === 0) return bid > 0 ? 100 : 0;
        return bid / ask;
    };

    function getLTP(key: string | undefined): number {
        if (!key) return 0;
        const feed = $marketDataStore[key];
        const feedLtp =
            feed?.fullFeed?.marketFF?.ltpc?.ltp ||
            feed?.fullFeed?.indexFF?.ltpc?.ltp ||
            0;
        return $candleDataStore[key]?.close || feedLtp;
    }

    type Pattern =
        | "Long Build-up"
        | "Short Build-up"
        | "Short Covering"
        | "Long Unwinding"
        | "Neutral";

    function getPattern(
        priceChange: number,
        oiChange: number,
    ): { name: Pattern; color: string; icon: string } {
        if (priceChange > 0 && oiChange > 0)
            return { name: "Long Build-up", color: "#22c55e", icon: "🚀" };
        if (priceChange < 0 && oiChange > 0)
            return { name: "Short Build-up", color: "#ef4444", icon: "🐻" };
        if (priceChange > 0 && oiChange < 0)
            return { name: "Short Covering", color: "#60a5fa", icon: "📈" };
        if (priceChange < 0 && oiChange < 0)
            return { name: "Long Unwinding", color: "#f97316", icon: "📉" };
        return { name: "Neutral", color: "#a1a1aa", icon: "➖" };
    }

    const pos = (n: number | undefined) => (n || 0) > 0;
    const neg = (n: number | undefined) => (n || 0) < 0;
</script>

<div class="unified-table-container">
    <div class="table-header">
        <h3>Complete Option Analysis</h3>
    </div>
    <div class="table-wrapper">
        <table class="unified-table">
            <thead>
                <tr class="main-header">
                    <th colspan="16" class="call-side">CALLS (CE)</th>
                    <th class="strike-col">STRIKE</th>
                    <th colspan="16" class="put-side">PUTS (PE)</th>
                </tr>
                <tr class="sub-header">
                    <!-- CE Side (Price Action → Pattern → Greeks) -->
                    <th>Ratio</th>
                    <th>Wall</th>
                    <th>Spread</th>

                    <th>Pattern</th>
                    <th>LTP</th>
                    <th>LTP Chg</th>
                    <th>OI</th>
                    <th>OI Chg</th>
                    <th>Vol</th>
                    <th>Vol Chg</th>

                    <th>IV</th>
                    <th>IV Diff</th>
                    <th>Vega</th>
                    <th>Gamma</th>
                    <th>Theta</th>
                    <th>Delta</th>

                    <th><!-- Strike --></th>

                    <!-- PE Side (Greeks → Pattern → Price Action) -->
                    <th>Delta</th>
                    <th>Theta</th>
                    <th>Gamma</th>
                    <th>Vega</th>
                    <th>IV Diff</th>
                    <th>IV</th>

                    <th>Vol Chg</th>
                    <th>Vol</th>
                    <th>OI Chg</th>
                    <th>OI</th>
                    <th>LTP Chg</th>
                    <th>LTP</th>
                    <th>Pattern</th>

                    <th>Spread</th>
                    <th>Wall</th>
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
                    {@const ceG = ceData?.greeks}
                    {@const peG = peData?.greeks}

                    {@const ceLtp = getLTP(ceKey)}
                    {@const peLtp = getLTP(peKey)}
                    {@const ceLtpChg = ceData?.price_diff || 0}
                    {@const peLtpChg = peData?.price_diff || 0}
                    {@const ceOiChg = ceData?.oi_diff || 0}
                    {@const peOiChg = peData?.oi_diff || 0}
                    {@const cePattern = getPattern(ceLtpChg, ceOiChg)}
                    {@const pePattern = getPattern(peLtpChg, peOiChg)}

                    {@const ceRatio = getRatio(
                        ceBA?.total_bid_qty,
                        ceBA?.total_ask_qty,
                    )}
                    {@const peRatio = getRatio(
                        peBA?.total_bid_qty,
                        peBA?.total_ask_qty,
                    )}
                    {@const ceBidWall = getWallLen(ceBA?.bid_walls)}
                    {@const ceAskWall = getWallLen(ceBA?.ask_walls)}
                    {@const peBidWall = getWallLen(peBA?.bid_walls)}
                    {@const peAskWall = getWallLen(peBA?.ask_walls)}

                    <tr
                        class="data-row"
                        class:atm-row={strike === $marketContext.atmStrike}
                    >
                        <!-- CE: Price Action -->
                        <td
                            class="cell-ratio"
                            class:bg-green={ceRatio > 1.5}
                            class:bg-red={ceRatio < 0.7}
                            class:bg-yellow={ceRatio >= 0.8 && ceRatio <= 1.2}
                        >
                            {ceRatio.toFixed(2)}
                        </td>
                        <td
                            class="cell-wall"
                            class:bg-green={ceBidWall > ceAskWall}
                            class:bg-red={ceAskWall > ceBidWall}
                        >
                            {ceBidWall}/{ceAskWall}
                        </td>
                        <td class="cell-val">{fmtPrz(ceBA?.spread)}</td>

                        <!-- CE: Pattern -->
                        <td
                            class="cell-pattern"
                            style="color: {cePattern.color}"
                        >
                            <span class="p-icon">{cePattern.icon}</span>
                            <span class="p-name">{cePattern.name}</span>
                        </td>
                        <td class="cell-ltp">{fmtPrz(ceLtp)}</td>
                        <td
                            class="cell-chg"
                            class:pos={ceLtpChg > 0}
                            class:neg={ceLtpChg < 0}
                        >
                            {fmtPrz(ceLtpChg)}
                        </td>
                        <td class="cell-oi">{fmt(ceData?.oi)}</td>
                        <td
                            class="cell-chg"
                            class:pos={ceOiChg > 0}
                            class:neg={ceOiChg < 0}
                        >
                            {fmt(ceOiChg)}
                        </td>
                        <td class="cell-vol">{fmt(ceData?.volume_1m)}</td>
                        <td
                            class="cell-chg"
                            class:pos={(ceData?.volume_diff || 0) > 0}
                            class:neg={(ceData?.volume_diff || 0) < 0}
                        >
                            {fmt(ceData?.volume_diff)}
                        </td>

                        <!-- CE: Greeks -->
                        <td class="cell-greek">{fmtG(ceData?.iv)}</td>
                        <td
                            class="cell-diff"
                            class:pos={pos(ceData?.iv_diff)}
                            class:neg={neg(ceData?.iv_diff)}
                        >
                            {fmtG(ceData?.iv_diff)}
                        </td>
                        <td class="cell-greek">{fmtG(ceG?.vega)}</td>
                        <td class="cell-greek">{fmtG(ceG?.gamma)}</td>
                        <td class="cell-greek">{fmtG(ceG?.theta)}</td>
                        <td class="cell-greek">{fmtG(ceG?.delta)}</td>

                        <!-- STRIKE -->
                        <td class="cell-strike">{strike}</td>

                        <!-- PE: Greeks -->
                        <td class="cell-greek">{fmtG(peG?.delta)}</td>
                        <td class="cell-greek">{fmtG(peG?.theta)}</td>
                        <td class="cell-greek">{fmtG(peG?.gamma)}</td>
                        <td class="cell-greek">{fmtG(peG?.vega)}</td>
                        <td
                            class="cell-diff"
                            class:pos={pos(peData?.iv_diff)}
                            class:neg={neg(peData?.iv_diff)}
                        >
                            {fmtG(peData?.iv_diff)}
                        </td>
                        <td class="cell-greek">{fmtG(peData?.iv)}</td>

                        <!-- PE: Pattern -->
                        <td
                            class="cell-chg"
                            class:pos={(peData?.volume_diff || 0) > 0}
                            class:neg={(peData?.volume_diff || 0) < 0}
                        >
                            {fmt(peData?.volume_diff)}
                        </td>

                        <td class="cell-vol">{fmt(peData?.volume_1m)}</td>
                        <td
                            class="cell-chg"
                            class:pos={peOiChg > 0}
                            class:neg={peOiChg < 0}
                        >
                            {fmt(peOiChg)}
                        </td>
                        <td class="cell-oi">{fmt(peData?.oi)}</td>
                        <td
                            class="cell-chg"
                            class:pos={peLtpChg > 0}
                            class:neg={peLtpChg < 0}
                        >
                            {fmtPrz(peLtpChg)}
                        </td>
                        <td class="cell-ltp">{fmtPrz(peLtp)}</td>
                        <td
                            class="cell-pattern"
                            style="color: {pePattern.color}"
                        >
                            <span class="p-icon">{pePattern.icon}</span>
                            <span class="p-name">{pePattern.name}</span>
                        </td>

                        <!-- PE: Price Action -->
                        <td class="cell-val">{fmtPrz(peBA?.spread)}</td>
                        <td
                            class="cell-wall"
                            class:bg-green={peBidWall > peAskWall}
                            class:bg-red={peAskWall > peBidWall}
                        >
                            {peBidWall}/{peAskWall}
                        </td>
                        <td
                            class="cell-ratio"
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
    .unified-table-container {
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

    .unified-table {
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
    }

    .data-row:hover {
        background: rgba(255, 255, 255, 0.03);
    }

    .atm-row {
        background: rgba(59, 130, 246, 0.05);
    }

    .cell-pattern {
        display: flex;
        align-items: center;
        gap: 4px;
        justify-content: center;
        font-weight: 600;
    }

    .p-icon {
        font-size: 12px;
    }
    .p-name {
        font-size: 10px;
    }

    .cell-ltp,
    .cell-val {
        color: #e4e4e7;
        font-weight: 600;
    }
    .cell-oi,
    .cell-vol {
        color: #a1a1aa;
    }
    .cell-chg,
    .cell-diff {
        color: #71717a;
    }
    .cell-greek {
        color: #e4e4e7;
        font-weight: 500;
    }
    .cell-wall,
    .cell-ratio {
        font-weight: 600;
    }

    .pos {
        color: #22c55e !important;
    }
    .neg {
        color: #ef4444 !important;
    }

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
