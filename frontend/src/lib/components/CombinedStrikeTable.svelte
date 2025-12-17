<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
        type Wall,
    } from "$lib/stores/candleData";
    import { marketDataStore } from "$lib/stores/marketData";
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

    // --- Formatters ---
    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtPrz = (n: number | undefined) => (n ? n.toFixed(2) : "-");
    const fmtG = (n: number | undefined) =>
        n !== undefined ? n.toFixed(4) : "-";

    // --- Helpers ---
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
        return $candleDataStore[key]?.close || $marketDataStore[key]?.ltp || 0;
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

<div class="combined-table-container">
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
        {@const ceLtpChg = ceData?.ltp_diff || 0}
        {@const peLtpChg = peData?.ltp_diff || 0}
        {@const ceOiChg = ceData?.oi_diff || 0}
        {@const peOiChg = peData?.oi_diff || 0}
        {@const cePattern = getPattern(ceLtpChg, ceOiChg)}
        {@const pePattern = getPattern(peLtpChg, peOiChg)}

        {@const ceRatio = getRatio(ceBA?.total_bid_qty, ceBA?.total_ask_qty)}
        {@const peRatio = getRatio(peBA?.total_bid_qty, peBA?.total_ask_qty)}
        {@const ceBidWall = getWallLen(ceBA?.bid_walls)}
        {@const ceAskWall = getWallLen(ceBA?.ask_walls)}
        {@const peBidWall = getWallLen(peBA?.bid_walls)}
        {@const peAskWall = getWallLen(peBA?.ask_walls)}

        <div
            class="strike-card"
            class:atm-card={strike === $marketContext.atmStrike}
        >
            <!-- Strike Header -->
            <div class="strike-header">
                <span class="strike-value">{strike}</span>
                {#if strike === $marketContext.atmStrike}
                    <span class="atm-badge">ATM</span>
                {/if}
            </div>

            <div class="strike-body">
                <!-- CE Side -->
                <div class="side ce-side">
                    <div class="side-label">CE</div>
                    <div class="data-grid">
                        <!-- Pattern -->
                        <div
                            class="data-item pattern"
                            style="color: {cePattern.color}"
                        >
                            <span class="icon">{cePattern.icon}</span>
                            <span class="label">{cePattern.name}</span>
                        </div>

                        <!-- LTP & Change -->
                        <div class="data-item">
                            <span class="value">{fmtPrz(ceLtp)}</span>
                            <span
                                class="label"
                                class:pos={ceLtpChg > 0}
                                class:neg={ceLtpChg < 0}
                                >{fmtPrz(ceLtpChg)}</span
                            >
                        </div>

                        <!-- OI Change -->
                        <div class="data-item">
                            <span class="label">OI Chg</span>
                            <span
                                class="value"
                                class:pos={ceOiChg > 0}
                                class:neg={ceOiChg < 0}>{fmt(ceOiChg)}</span
                            >
                        </div>

                        <!-- Ratio -->
                        <div
                            class="data-item"
                            class:bg-green={ceRatio > 1.5}
                            class:bg-red={ceRatio < 0.7}
                            class:bg-yellow={ceRatio >= 0.8 && ceRatio <= 1.2}
                        >
                            <span class="label">Ratio</span>
                            <span class="value">{ceRatio.toFixed(2)}</span>
                        </div>

                        <!-- Wall -->
                        <div
                            class="data-item"
                            class:bg-green={ceBidWall > ceAskWall}
                            class:bg-red={ceAskWall > ceBidWall}
                        >
                            <span class="label">Wall</span>
                            <span class="value">{ceBidWall}/{ceAskWall}</span>
                        </div>

                        <!-- Spread -->
                        <div class="data-item">
                            <span class="label">Spread</span>
                            <span class="value">{fmtPrz(ceBA?.spread)}</span>
                        </div>

                        <!-- Greeks -->
                        <div class="data-item greek">
                            <span class="label">Δ</span>
                            <span class="value">{fmtG(ceG?.delta)}</span>
                        </div>
                        <div class="data-item greek">
                            <span class="label">Θ</span>
                            <span class="value">{fmtG(ceG?.theta)}</span>
                        </div>
                        <div class="data-item greek">
                            <span class="label">IV</span>
                            <span class="value">{fmtG(ceData?.iv)}</span>
                        </div>
                    </div>
                </div>

                <!-- PE Side -->
                <div class="side pe-side">
                    <div class="side-label">PE</div>
                    <div class="data-grid">
                        <!-- Pattern -->
                        <div
                            class="data-item pattern"
                            style="color: {pePattern.color}"
                        >
                            <span class="icon">{pePattern.icon}</span>
                            <span class="label">{pePattern.name}</span>
                        </div>

                        <!-- LTP & Change -->
                        <div class="data-item">
                            <span class="value">{fmtPrz(peLtp)}</span>
                            <span
                                class="label"
                                class:pos={peLtpChg > 0}
                                class:neg={peLtpChg < 0}
                                >{fmtPrz(peLtpChg)}</span
                            >
                        </div>

                        <!-- OI Change -->
                        <div class="data-item">
                            <span class="label">OI Chg</span>
                            <span
                                class="value"
                                class:pos={peOiChg > 0}
                                class:neg={peOiChg < 0}>{fmt(peOiChg)}</span
                            >
                        </div>

                        <!-- Ratio -->
                        <div
                            class="data-item"
                            class:bg-green={peRatio > 1.5}
                            class:bg-red={peRatio < 0.7}
                            class:bg-yellow={peRatio >= 0.8 && peRatio <= 1.2}
                        >
                            <span class="label">Ratio</span>
                            <span class="value">{peRatio.toFixed(2)}</span>
                        </div>

                        <!-- Wall -->
                        <div
                            class="data-item"
                            class:bg-green={peBidWall > peAskWall}
                            class:bg-red={peAskWall > peBidWall}
                        >
                            <span class="label">Wall</span>
                            <span class="value">{peBidWall}/{peAskWall}</span>
                        </div>

                        <!-- Spread -->
                        <div class="data-item">
                            <span class="label">Spread</span>
                            <span class="value">{fmtPrz(peBA?.spread)}</span>
                        </div>

                        <!-- Greeks -->
                        <div class="data-item greek">
                            <span class="label">Δ</span>
                            <span class="value">{fmtG(peG?.delta)}</span>
                        </div>
                        <div class="data-item greek">
                            <span class="label">Θ</span>
                            <span class="value">{fmtG(peG?.theta)}</span>
                        </div>
                        <div class="data-item greek">
                            <span class="label">IV</span>
                            <span class="value">{fmtG(peData?.iv)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    {/each}

    {#if sortedStrikes.length === 0}
        <div class="empty-state">
            <p>No Data. Select Index in Header.</p>
        </div>
    {/if}
</div>

<style>
    .combined-table-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 24px;
    }

    .strike-card {
        background: var(--bg-card, #1e1e1e);
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .atm-card {
        border: 2px solid #3b82f6;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
    }

    .strike-header {
        background: #27272a;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .strike-value {
        font-size: 16px;
        font-weight: 700;
        color: #fbbf24;
        font-family: "JetBrains Mono", monospace;
    }

    .atm-badge {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
    }

    .strike-body {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1px;
        background: #333;
    }

    .side {
        padding: 12px;
        background: #1e1e1e;
    }

    .ce-side {
        border-right: 1px solid #333;
    }

    .side-label {
        font-size: 11px;
        font-weight: 700;
        color: #71717a;
        margin-bottom: 8px;
        text-transform: uppercase;
    }

    .ce-side .side-label {
        color: #22c55e;
    }
    .pe-side .side-label {
        color: #ef4444;
    }

    .data-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .data-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 6px 10px;
        background: #27272a;
        border-radius: 6px;
        min-width: 60px;
        font-family: "JetBrains Mono", monospace;
    }

    .data-item.pattern {
        flex-direction: row;
        gap: 6px;
        min-width: 120px;
    }

    .data-item .icon {
        font-size: 14px;
    }

    .data-item .label {
        font-size: 9px;
        color: #71717a;
        text-transform: uppercase;
    }

    .data-item .value {
        font-size: 12px;
        font-weight: 600;
        color: #e4e4e7;
    }

    .data-item.greek {
        min-width: 50px;
    }

    .pos {
        color: #22c55e !important;
    }
    .neg {
        color: #ef4444 !important;
    }

    .bg-green {
        background-color: rgba(34, 197, 94, 0.15) !important;
    }
    .bg-green .value {
        color: #4ade80 !important;
    }

    .bg-red {
        background-color: rgba(239, 68, 68, 0.15) !important;
    }
    .bg-red .value {
        color: #fca5a5 !important;
    }

    .bg-yellow {
        background-color: rgba(234, 179, 8, 0.15) !important;
    }
    .bg-yellow .value {
        color: #facc15 !important;
    }

    .empty-state {
        padding: 40px;
        text-align: center;
        color: #666;
        background: var(--bg-card, #1e1e1e);
        border-radius: 12px;
    }
</style>
