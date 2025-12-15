<script lang="ts">
    import { onDestroy } from "svelte";
    import {
        candleDataStore,
        type CandleDetails,
    } from "$lib/stores/candleData";
    import { marketDataStore } from "$lib/stores/marketData";

    // --- State ---
    // We derive everything from the stores.
    // However, to organize the table by Strike, we need to group the store values.

    // Helper to extract Strike and Type from instrument key
    // Format: "NSE_FO|NIFTY23DEC18000CE" (Example)
    // Actually, real keys might look like "NSE_FO|54321".
    // If we only have keys, we need metadata.
    // Assumption: The Global Store keys are sufficient if we can parse them,
    // OR we rely on the `marketContext` if available.
    // BUT user said "No Index Selector", implying we just show WHAT IS THERE.
    // So we must rely on what's in `candleDataStore` or `marketDataStore`.
    // Problem: `candleDataStore` keys are just arbitrary strings if we don't have a mapping.
    // "NSE_FO|..." usually needs a lookup.
    // However, for this task, if the user says "already subscribed", likely the keys are known.
    // Let's assume we can try to parse or just list them.
    // WAIT: To make a "Center Strike" table, we NEED to know which is CE and PE for the SAME strike.

    // If we don't have a map, we can't easily group CE/PE.
    // Strategy: We will iterate through all keys in `$candleDataStore`.
    // We try to group them by Strike if possible.
    // If we can't parse the key, we might struggle.
    // usage of `marketContext` was robust because it mapped Strike -> CE/PE keys.
    // If we remove IndexSelector, we lose that Context.

    // REVISED STRATEGY:
    // We will still import `marketContext` because the User might have set it up earlier
    // or we might need to "scan" the store to infer relationships.
    // A more robust way without selector:
    // Just list all available instruments.
    // BUT User specifically asked for "Strike Center, Left CE, Right PE".
    // This implies we MUST group by Strike.

    // Let's try to "Group by Symbol/Strike" from the store values if metadata allows.
    // `CandleDetails` doesn't strictly have "Strike" field unless we added it.
    // It has `instrument_key`.

    // WORKAROUND: For now, we will look at `$candleDataStore` values.
    // If the backend isn't sending symbol/strike in the candle update, we might be blind.
    // Let's check `marketDataStore`. It has `InstrumentFeed`.
    // Usually Upstox keys are opaque.

    // CRITICAL: If the user says "Don't use Index Selector", they might assume we already "know" the chain.
    // If the subscriptions were done via the "Connect" page which used `IndexSelector`,
    // then `marketContext` MIGHT STILL BE POPULATED if we persisted it? No, it's memory only.

    // fallback: We will render a flat list OR standard table if we can't group.
    // BUT User demands "Strike Center".
    // I will assume for this implementation that we can access `marketContext`
    // OR we will inject a partial "Auto-Detector" logic here.

    // Actually, looking at previous files, `IndexSelector` populates `marketContext`.
    // If user removes `IndexSelector`, how do we get the grouping?
    // Maybe they just want to see the "Pattern" for whatever IS subscribed.
    // If I can't group CE/PE, I can't make the table they want.

    // Let's assume there IS a way to group.
    // For now, I'll use `marketContext` as a dependency.
    // If it's empty, the table will be empty.
    // User said "already sub pannitomla" (we already subscribed).
    // If they subscribed via valid means (like the earlier test test), the data is in the backend.
    // But the Frontend needs to know "Key X is 18000 CE".

    // Let's assume we use `marketContext` for structure.
    // If the user manually subscribed via backend script, frontend has NO IDEA what the keys mean
    // unless we fetch `/api/v1/instrument/details?key=...`.

    // DECISION: I will keep using `marketContext` to drive the rows.
    // The `IndexSelector` (or a hidden equivalent) is needed to populate it.
    // If the user deleted IndexSelector, I will add a "Auto-populate from Store" button or logic
    // that uses a heuristic or just renders what it can.

    // ACTUALLY, simply importing `marketContext` allows sharing state if `IndexSelector` was used elsewhere (e.g. Header).
    // The user's prompt "remove index selector" from THIS page doesn't mean remove it from the APP.
    // Use the `marketContext` that (hopefully) exists or is populated globally.

    import { marketContext } from "$lib/stores/marketContext";

    // --- Types & Logic ---

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
        // Logic:
        // Price ⬆️, OI ⬆️ -> Long Build-up (Strong Bullish)
        // Price ⬇️, OI ⬆️ -> Short Build-up (Strong Bearish)
        // Price ⬆️, OI ⬇️ -> Short Covering (Rocket 🚀)
        // Price ⬇️, OI ⬇️ -> Long Unwinding (Profit Booking)

        if (priceChange > 0 && oiChange > 0)
            return { name: "Long Build-up", color: "#22c55e", icon: "⬆️" }; // Green

        if (priceChange < 0 && oiChange > 0)
            return { name: "Short Build-up", color: "#ef4444", icon: "⬇️" }; // Red

        if (priceChange > 0 && oiChange < 0)
            return { name: "Short Covering", color: "#3b82f6", icon: "🚀" }; // Blue

        if (priceChange < 0 && oiChange < 0)
            return { name: "Long Unwinding", color: "#f59e0b", icon: "📉" }; // Orange

        return { name: "Neutral", color: "#9ca3af", icon: "-" };
    }

    // Reactive Sorted Strikes from Context
    let sortedStrikes = $derived(
        Object.keys($marketContext.chain)
            .map(Number)
            .sort((a, b) => a - b),
    );

    // Helpers to get data from GLOBAL STORES
    function getCandle(key: string | undefined): CandleDetails | null {
        if (!key) return null;
        return $candleDataStore[key] || null;
    }

    function getLTP(key: string | undefined): number {
        if (!key) return 0;
        // Prefer Candle Close if available (stable 1m), else Market Feed LTP
        return (
            $candleDataStore[key]?.close ||
            $marketDataStore[key]?.fullFeed?.marketFF?.ltpc?.ltp ||
            0
        );
    }

    // Calculate Max/Min OI Change for Highlighting
    let maxCeOiChg = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].CE)?.oi_diff || 0,
            ),
        ),
    );
    let minCeOiChg = $derived(
        Math.min(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].CE)?.oi_diff || 0,
            ),
        ),
    );
    let maxPeOiChg = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].PE)?.oi_diff || 0,
            ),
        ),
    );
    let minPeOiChg = $derived(
        Math.min(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].PE)?.oi_diff || 0,
            ),
        ),
    );

    // Calculate Max Values for Highlighting
    let maxCeOI = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].CE)?.oi || 0,
            ),
        ),
    );
    let maxCeVol = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].CE)?.volume_1m || 0,
            ),
        ),
    );
    let maxPeOI = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].PE)?.oi || 0,
            ),
        ),
    );
    let maxPeVol = $derived(
        Math.max(
            0,
            ...sortedStrikes.map(
                (s) => getCandle($marketContext.chain[s].PE)?.volume_1m || 0,
            ),
        ),
    );

    // Helper to format values
    const fmt = (n: number | undefined) => (n ? n.toLocaleString() : "-");
    const fmtDec = (n: number | undefined) => (n ? n.toFixed(2) : "-");
</script>

<div class="pattern-table-container">
    <table class="pattern-table">
        <thead>
            <tr class="main-header">
                <th colspan="7" class="call-side">CALLS (CE)</th>
                <th class="strike-col">STRIKE</th>
                <th colspan="7" class="put-side">PUTS (PE)</th>
            </tr>
            <tr class="sub-header">
                <th>Pattern</th>
                <th>Vol Chg</th>
                <th>Vol</th>
                <th>OI Chg</th>
                <th>OI</th>
                <th>LTP Chg</th>
                <th>LTP</th>

                <th><!-- Strike --></th>

                <th>LTP</th>
                <th>LTP Chg</th>
                <th>OI</th>
                <th>OI Chg</th>
                <th>Vol</th>
                <th>Vol Chg</th>
                <th>Pattern</th>
            </tr>
        </thead>
        <tbody>
            {#each sortedStrikes as strike}
                {@const ceKey = $marketContext.chain[strike].CE}
                {@const peKey = $marketContext.chain[strike].PE}
                {@const ceData = getCandle(ceKey)}
                {@const peData = getCandle(peKey)}

                <!-- CE Calculations -->
                {@const ceLtp = getLTP(ceKey)}
                {@const ceLtpChg = ceData ? ceData.price_diff : 0}
                {@const ceOi = ceData ? ceData.oi : 0}
                {@const ceOiChg = ceData ? ceData.oi_diff : 0}
                {@const ceVol = ceData ? ceData.volume_1m : 0}
                {@const ceVolChg = ceData ? ceData.volume_diff : 0}
                {@const cePattern = getPattern(ceLtpChg, ceOiChg)}

                <!-- PE Calculations -->
                {@const peLtp = getLTP(peKey)}
                {@const peLtpChg = peData ? peData.price_diff : 0}
                {@const peOi = peData ? peData.oi : 0}
                {@const peOiChg = peData ? peData.oi_diff : 0}
                {@const peVol = peData ? peData.volume_1m : 0}
                {@const peVolChg = peData ? peData.volume_diff : 0}
                {@const pePattern = getPattern(peLtpChg, peOiChg)}

                <tr
                    class="data-row"
                    class:atm-row={strike === $marketContext.atmStrike}
                >
                    <!-- CE SIDE -->
                    <td class="cell-pattern" style="color: {cePattern.color}">
                        <span class="p-icon">{cePattern.icon}</span>
                        <span class="p-name">{cePattern.name}</span>
                    </td>
                    <td class="cell-muted">{fmt(ceVolChg)}</td>
                    <td
                        class="cell-vol"
                        class:high-ce={ceVol === maxCeVol && ceVol > 0}
                        >{fmt(ceVol)}</td
                    >
                    <td
                        class="cell-oi-chg"
                        class:neg={ceOiChg > 0}
                        class:pos={ceOiChg < 0}
                        class:high-ce={ceOiChg === maxCeOiChg && ceOiChg > 0}
                        class:high-pe={ceOiChg === minCeOiChg && ceOiChg < 0}
                        >{fmt(ceOiChg)}</td
                    >
                    <td
                        class="cell-oi"
                        class:high-ce={ceOi === maxCeOI && ceOi > 0}
                        >{fmt(ceOi)}</td
                    >
                    <td
                        class="cell-ltp-chg"
                        class:pos={ceLtpChg > 0}
                        class:neg={ceLtpChg < 0}>{fmtDec(ceLtpChg)}</td
                    >
                    <td class="cell-ltp">{fmtDec(ceLtp)}</td>

                    <!-- STRIKE -->
                    <td class="cell-strike">{strike}</td>

                    <!-- PE SIDE -->
                    <td class="cell-ltp">{fmtDec(peLtp)}</td>
                    <td
                        class="cell-ltp-chg"
                        class:pos={peLtpChg > 0}
                        class:neg={peLtpChg < 0}>{fmtDec(peLtpChg)}</td
                    >
                    <td
                        class="cell-oi"
                        class:high-pe={peOi === maxPeOI && peOi > 0}
                        >{fmt(peOi)}</td
                    >
                    <td
                        class="cell-oi-chg"
                        class:neg={peOiChg > 0}
                        class:pos={peOiChg < 0}
                        class:high-ce={peOiChg === maxPeOiChg && peOiChg > 0}
                        class:high-pe={peOiChg === minPeOiChg && peOiChg < 0}
                        >{fmt(peOiChg)}</td
                    >
                    <td
                        class="cell-vol"
                        class:high-pe={peVol === maxPeVol && peVol > 0}
                        >{fmt(peVol)}</td
                    >
                    <td class="cell-muted">{fmt(peVolChg)}</td>
                    <td class="cell-pattern" style="color: {pePattern.color}">
                        <span class="p-name">{pePattern.name}</span>
                        <span class="p-icon">{pePattern.icon}</span>
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>

    {#if sortedStrikes.length === 0}
        <div class="empty-state">
            <p>No Pattern Data Found.</p>
            <p class="sub-text">
                Please select an Index and Subscribe using the <strong
                    >Top Header</strong
                > selector to load data.
            </p>
        </div>
    {/if}
</div>

<style>
    .pattern-table-container {
        width: 100%;
        overflow-x: auto;
        background: var(--bg-card, #1e1e1e);
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .pattern-table {
        width: 100%;
        border-collapse: collapse;
        font-family: "JetBrains Mono", monospace;
        font-size: 12px;
    }

    th,
    td {
        padding: 8px 12px;
        text-align: center;
        border-bottom: 1px solid var(--border-color, #333);
        white-space: nowrap;
    }

    /* HEADER STYLES */
    .main-header th {
        background: var(--bg-secondary, #27272a);
        color: var(--text-primary, #fff);
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 12px;
    }
    .call-side {
        border-bottom: 2px solid var(--accent-green, #22c55e);
    }
    .put-side {
        border-bottom: 2px solid var(--accent-red, #ef4444);
    }
    .strike-col {
        background: var(--bg-tertiary, #3f3f46) !important;
        color: #fbbf24;
    }

    .sub-header th {
        background: var(--bg-secondary, #27272a);
        color: var(--text-secondary, #a1a1aa);
        font-weight: 600;
        font-size: 11px;
    }

    /* DATA ROWS */
    .data-row:hover {
        background: rgba(255, 255, 255, 0.03);
    }

    .cell-strike {
        background: var(--bg-tertiary, #3f3f46);
        color: var(--text-primary, #fbbf24);
        font-weight: bold;
        font-size: 13px;
        border-left: 1px solid #444;
        border-right: 1px solid #444;
    }

    .cell-ltp {
        color: var(--text-primary, #e4e4e7);
        font-weight: 600;
    }
    .cell-vol {
        color: var(--text-muted, #71717a);
    }
    .cell-oi {
        color: var(--text-secondary, #a1a1aa);
    }
    .cell-muted {
        color: #52525b;
    }

    .cell-ltp-chg,
    .cell-oi-chg {
        font-weight: 500;
    }
    .pos {
        color: var(--accent-green, #22c55e);
    }
    .neg {
        color: var(--accent-red, #ef4444);
    }

    /* HIGHLIGHTS FOR MAX OI/VOL */
    /* high-ce: Red Bg (for Max CE / Max POSITIVE change) */
    .high-ce {
        background-color: rgba(239, 68, 68, 0.25);
        color: #fca5a5 !important;
        font-weight: 800;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    /* high-pe: Green Bg (for Max PE / Max NEGATIVE change) */
    .high-pe {
        background-color: rgba(34, 197, 94, 0.25);
        color: #86efac !important;
        font-weight: 800;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }

    /* PATTERN CELL */
    .cell-pattern {
        font-weight: 700;
        text-transform: uppercase;
        font-size: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        min-width: 140px;
    }
    .p-icon {
        font-size: 14px;
    }

    /* ATM ROW Highlight */
    .atm-row {
        background: rgba(59, 130, 246, 0.05);
    }
    .atm-row .cell-strike {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid #3b82f6;
    }

    .empty-state {
        padding: 40px;
        text-align: center;
        color: #71717a;
    }
    .sub-text {
        font-size: 12px;
        margin-top: 4px;
    }
</style>
