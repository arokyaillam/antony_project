<!-- Live Panic Score Analysis - Real-time Seller State Detection -->
<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { syncSubscriptions, subscriptionStore } from "$lib/stores/feed";
    import {
        connectStream,
        disconnectStream,
        isStreamActive,
    } from "$lib/stores/stream";
    import {
        marketDataStore,
        type InstrumentFeed,
        type MarketFF,
    } from "$lib/stores/marketData";
    import { marketContext } from "$lib/stores/marketContext";
    import { get } from "svelte/store";

    // ========================================
    // STATE MANAGEMENT
    // ========================================

    // Historical data tracking per instrument
    // Key: instrument_key, Value: historical snapshots
    interface HistoricalSnapshot {
        timestamp: number;
        ltp: number;
        oi: number;
        tsq: number;
        iv: number;
        tbq: number; // Total Bid Quantity (Wall)
    }

    interface InstrumentHistory {
        snapshots: HistoricalSnapshot[];
        prev_wall_qty: number;
        removed_qty: number;
        refilled_qty: number;
    }

    interface PanicAnalysis {
        instrument_key: string;
        strike: string;
        option_type: string;
        ltp: number;
        oi: number;
        oi_change_pct: number;
        price_change_pct: number;
        wall_decay_pct: number;
        wall_absorption: boolean;
        replenish_ratio: number;
        tsq_spike_ratio: number;
        velocity_ratio: number;
        iv_change: number;
        base_score: number;
        panic_score: number;
        seller_state: "SELLER_CONTROL" | "SELLER_STRESS" | "SELLER_PANIC";
        short_covering: boolean;
    }

    let instrumentHistory = $state<Record<string, InstrumentHistory>>({});
    let panicAnalysisList = $state<PanicAnalysis[]>([]);
    let lastUpdateTime = $state<number>(Date.now());

    // Config
    const HISTORY_INTERVAL_MS = 5000; // Snapshot every 5 seconds
    const LOOKBACK_30S = 6; // 6 snapshots = 30 seconds
    const LOOKBACK_5M = 60; // 60 snapshots = 5 minutes

    // Multipliers (can be made dynamic later)
    let is_expiry_day = $state(false);
    let is_open_close = $state(true);
    let range_pct_threshold = $state(35);
    let breaks_5d_extreme = $state(false);

    // Derived multipliers
    let time_multiplier = $derived(() => {
        if (is_expiry_day) return 2.0;
        if (is_open_close) return 1.5;
        return 1.0;
    });

    let historical_multiplier = $derived(() => {
        if (breaks_5d_extreme) return 2.0;
        if (range_pct_threshold > 50) return 1.6;
        if (range_pct_threshold >= 30) return 1.3;
        return 1.0;
    });

    // Normal velocity baseline (points per 30s for options)
    const NORMAL_VELOCITY = 5.0;

    // ========================================
    // HELPER FUNCTIONS
    // ========================================

    function getMarketFF(feed: InstrumentFeed): MarketFF | null {
        return feed?.fullFeed?.marketFF || feed?.fullFeed?.indexFF || null;
    }

    function parseStrikeFromKey(key: string): { strike: string; type: string } {
        const ctx = get(marketContext);

        // 1. Direct Lookup
        if (ctx.instruments && ctx.instruments[key]) {
            const meta = ctx.instruments[key];
            return {
                strike: meta.strike.toString(),
                type: meta.type,
            };
        }

        // Fallback: Strip prefix and try to handle
        const parts = key.split("|");
        const token = parts.length > 1 ? parts[1] : key;

        // 2. Token Lookup (loose match)
        if (ctx.instruments && ctx.instruments[token]) {
            const meta = ctx.instruments[token];
            return {
                strike: meta.strike.toString(),
                type: meta.type,
            };
        }

        // 3. Heuristic / Clean Display
        let type = "UNK";
        if (token.endsWith("CE") || token.includes("CE ")) type = "CE";
        else if (token.endsWith("PE") || token.includes("PE ")) type = "PE";

        return { strike: token, type };
    }

    function calculatePanicAnalysis(
        key: string,
        feed: InstrumentFeed,
        history: InstrumentHistory,
    ): PanicAnalysis | null {
        const ff = getMarketFF(feed);
        if (!ff) return null;

        const ltp = ff.ltpc?.ltp || 0;
        const oi = ff.oi || 0;
        const tsq = ff.tsq || 0;
        const iv = ff.iv || 0;
        const tbq = ff.tbq || 0;

        const snapshots = history.snapshots;
        const now = Date.now();

        // Get 30s ago snapshot
        const snapshot30s =
            snapshots.length >= LOOKBACK_30S
                ? snapshots[snapshots.length - LOOKBACK_30S]
                : snapshots[0];

        // Get 5min ago snapshot for average TSQ
        const recentSnapshots = snapshots.slice(-LOOKBACK_5M);
        const avgTsq5m =
            recentSnapshots.length > 0
                ? recentSnapshots.reduce((sum, s) => sum + s.tsq, 0) /
                  recentSnapshots.length
                : tsq;

        // === CALCULATIONS ===

        // OI Change %
        const oi_prev = snapshot30s?.oi || oi;
        const oi_change_pct =
            oi_prev > 0 ? ((oi - oi_prev) / oi_prev) * 100 : 0;

        // Price Change %
        const price_30s = snapshot30s?.ltp || ltp;
        const price_change_pct =
            price_30s > 0 ? ((ltp - price_30s) / price_30s) * 100 : 0;

        // Short Covering Detection
        const short_covering = oi_change_pct < -1.0 && price_change_pct > 0.3;

        // Wall Decay (using TBQ as wall proxy)
        const prev_wall = history.prev_wall_qty || tbq;
        const wall_decay_pct =
            prev_wall > 0 ? ((prev_wall - tbq) / prev_wall) * 100 : 0;
        const wall_absorption = wall_decay_pct >= 30;

        // Replenish Ratio
        const replenish_ratio =
            history.removed_qty > 0
                ? history.refilled_qty / history.removed_qty
                : 1.0;

        // TSQ Spike Ratio
        const tsq_spike_ratio = avgTsq5m > 0 ? tsq / avgTsq5m : 1.0;

        // Price Velocity
        const velocity = Math.abs(ltp - price_30s);
        const velocity_ratio = velocity / NORMAL_VELOCITY;

        // IV Change
        const iv_prev = snapshot30s?.iv || iv;
        const iv_change = iv - iv_prev;

        // === PANIC SCORE COMPONENTS ===
        const wall_absorption_score = wall_absorption ? 1 : 0;
        const replenish_failure_score =
            replenish_ratio < 0.5 ? (0.5 - replenish_ratio) / 0.5 : 0;
        const oi_divergence_score = short_covering
            ? 1
            : oi_change_pct < -0.5
              ? 0.5
              : 0;
        const tsq_spike_score = Math.min(tsq_spike_ratio / 4, 1);
        const velocity_score = Math.min(velocity_ratio / 3, 1);
        const iv_spike_score = Math.min(Math.max(iv_change, 0) / 1.5, 1);

        // Base Score
        const base_score =
            wall_absorption_score * 20 +
            replenish_failure_score * 15 +
            oi_divergence_score * 15 +
            tsq_spike_score * 15 +
            velocity_score * 15 +
            iv_spike_score * 10;

        // Final Score with multipliers
        const panic_score = Math.min(
            base_score * historical_multiplier() * time_multiplier(),
            100,
        );

        // Seller State
        let seller_state: "SELLER_CONTROL" | "SELLER_STRESS" | "SELLER_PANIC";
        if (panic_score >= 60) seller_state = "SELLER_PANIC";
        else if (panic_score >= 40) seller_state = "SELLER_STRESS";
        else seller_state = "SELLER_CONTROL";

        const { strike, type } = parseStrikeFromKey(key);

        return {
            instrument_key: key,
            strike,
            option_type: type,
            ltp,
            oi,
            oi_change_pct,
            price_change_pct,
            wall_decay_pct,
            wall_absorption,
            replenish_ratio,
            tsq_spike_ratio,
            velocity_ratio,
            iv_change,
            base_score,
            panic_score,
            seller_state,
            short_covering,
        };
    }

    // Track history and calculate panic for each subscribed instrument
    function updateAnalysis(marketData: Record<string, InstrumentFeed>) {
        const now = Date.now();
        const analyses: PanicAnalysis[] = [];

        for (const [key, feed] of Object.entries(marketData)) {
            // Skip index instruments
            if (key.includes("INDEX")) continue;

            const ff = getMarketFF(feed);
            if (!ff) continue;

            // Initialize history if needed
            if (!instrumentHistory[key]) {
                instrumentHistory[key] = {
                    snapshots: [],
                    prev_wall_qty: ff.tbq || 0,
                    removed_qty: 0,
                    refilled_qty: 0,
                };
            }

            const history = instrumentHistory[key];

            // Add snapshot (throttled)
            if (
                history.snapshots.length === 0 ||
                now -
                    (history.snapshots[history.snapshots.length - 1]
                        ?.timestamp || 0) >=
                    HISTORY_INTERVAL_MS
            ) {
                // Track wall changes before adding new snapshot
                const currentTbq = ff.tbq || 0;
                if (currentTbq < history.prev_wall_qty) {
                    history.removed_qty += history.prev_wall_qty - currentTbq;
                } else if (currentTbq > history.prev_wall_qty) {
                    history.refilled_qty += currentTbq - history.prev_wall_qty;
                }
                history.prev_wall_qty = currentTbq;

                history.snapshots.push({
                    timestamp: now,
                    ltp: ff.ltpc?.ltp || 0,
                    oi: ff.oi || 0,
                    tsq: ff.tsq || 0,
                    iv: ff.iv || 0,
                    tbq: currentTbq,
                });

                // Keep only last 5 minutes of data
                if (history.snapshots.length > LOOKBACK_5M) {
                    history.snapshots.shift();
                }
            }

            // Calculate analysis
            const analysis = calculatePanicAnalysis(key, feed, history);
            if (analysis) {
                analyses.push(analysis);
            }
        }

        // Sort by panic score descending
        panicAnalysisList = analyses.sort(
            (a, b) => b.panic_score - a.panic_score,
        );
        lastUpdateTime = now;
    }

    // Subscribe to market data changes
    let unsubscribeMarket: (() => void) | null = null;

    onMount(async () => {
        // Sync subscriptions from backend
        await syncSubscriptions();

        // Connect to live stream
        connectStream();

        // Subscribe to market data updates
        unsubscribeMarket = marketDataStore.subscribe((data) => {
            if (data && Object.keys(data).length > 0) {
                updateAnalysis(data);
            }
        });
    });

    onDestroy(() => {
        if (unsubscribeMarket) unsubscribeMarket();
    });

    // Get state class for styling
    function getStateClass(state: string): string {
        if (state === "SELLER_PANIC") return "panic";
        if (state === "SELLER_STRESS") return "stress";
        return "control";
    }

    // Highest panic strike
    let topPanicStrike = $derived(
        panicAnalysisList.length > 0 ? panicAnalysisList[0] : null,
    );

    // Count by state
    let panicCount = $derived(
        panicAnalysisList.filter((a) => a.seller_state === "SELLER_PANIC")
            .length,
    );
    let stressCount = $derived(
        panicAnalysisList.filter((a) => a.seller_state === "SELLER_STRESS")
            .length,
    );
    let controlCount = $derived(
        panicAnalysisList.filter((a) => a.seller_state === "SELLER_CONTROL")
            .length,
    );
</script>

<div class="panic-page">
    <div class="header">
        <h1>🎯 Live Panic Score Analysis</h1>
        <div class="status-bar">
            <span class="status {$isStreamActive ? 'active' : 'inactive'}">
                {$isStreamActive ? "🟢 LIVE" : "🔴 OFFLINE"}
            </span>
            <span class="count"
                >Tracking: {panicAnalysisList.length} strikes</span
            >
            <span class="timestamp"
                >Updated: {new Date(lastUpdateTime).toLocaleTimeString()}</span
            >
        </div>
    </div>

    <!-- Multiplier Controls -->
    <div class="multiplier-bar">
        <label>
            <input type="checkbox" bind:checked={is_expiry_day} /> Expiry Day (2x)
        </label>
        <label>
            <input type="checkbox" bind:checked={is_open_close} /> Open/Close Hour
            (1.5x)
        </label>
        <label>
            <input type="checkbox" bind:checked={breaks_5d_extreme} /> 5D Extreme
            Break (2x)
        </label>
        <label>
            Range %: <input
                type="number"
                bind:value={range_pct_threshold}
                class="small-input"
            />
        </label>
        <span class="multiplier-result">
            Final Multiplier: <strong
                >{(time_multiplier() * historical_multiplier()).toFixed(
                    2,
                )}x</strong
            >
        </span>
    </div>

    <!-- Summary Cards -->
    <div class="summary-grid">
        <div class="summary-card panic">
            <span class="count">{panicCount}</span>
            <span class="label">PANIC</span>
        </div>
        <div class="summary-card stress">
            <span class="count">{stressCount}</span>
            <span class="label">STRESS</span>
        </div>
        <div class="summary-card control">
            <span class="count">{controlCount}</span>
            <span class="label">CONTROL</span>
        </div>

        {#if topPanicStrike}
            <div class="top-panic-card">
                <div class="top-label">🔥 Highest Panic</div>
                <div class="top-strike">
                    {topPanicStrike.strike}
                    <span
                        class="type-badge {topPanicStrike.option_type === 'CE'
                            ? 'ce'
                            : 'pe'}"
                    >
                        {topPanicStrike.option_type}
                    </span>
                </div>
                <div
                    class="top-score {getStateClass(
                        topPanicStrike.seller_state,
                    )}"
                >
                    {topPanicStrike.panic_score.toFixed(0)}
                </div>
            </div>
        {/if}
    </div>

    <!-- Live Analysis Table -->
    <div class="table-container">
        <table class="panic-table">
            <thead>
                <tr>
                    <th>Strike</th>
                    <th>LTP</th>
                    <th>OI</th>
                    <th>OI Δ%</th>
                    <th>Price Δ%</th>
                    <th>TSQ Spike</th>
                    <th>Velocity</th>
                    <th>IV Δ</th>
                    <th>Wall Decay</th>
                    <th>Score</th>
                    <th>State</th>
                    <th>Signals</th>
                </tr>
            </thead>
            <tbody>
                {#each panicAnalysisList as analysis (analysis.instrument_key)}
                    <tr class="row-{getStateClass(analysis.seller_state)}">
                        <td class="strike">
                            <span class="strike-num">{analysis.strike}</span>
                            <span
                                class="type-badge {analysis.option_type === 'CE'
                                    ? 'ce'
                                    : 'pe'}"
                            >
                                {analysis.option_type}
                            </span>
                        </td>
                        <td class="ltp">{analysis.ltp.toFixed(2)}</td>
                        <td class="oi">{(analysis.oi / 1000).toFixed(1)}K</td>
                        <td
                            class="oi-change {analysis.oi_change_pct < 0
                                ? 'negative'
                                : 'positive'}"
                        >
                            {analysis.oi_change_pct.toFixed(2)}%
                        </td>
                        <td
                            class="price-change {analysis.price_change_pct > 0
                                ? 'positive'
                                : 'negative'}"
                        >
                            {analysis.price_change_pct.toFixed(2)}%
                        </td>
                        <td
                            class="tsq {analysis.tsq_spike_ratio > 2.5
                                ? 'highlight'
                                : ''}"
                        >
                            {analysis.tsq_spike_ratio.toFixed(2)}x
                        </td>
                        <td
                            class="velocity {analysis.velocity_ratio > 2
                                ? 'highlight'
                                : ''}"
                        >
                            {analysis.velocity_ratio.toFixed(2)}x
                        </td>
                        <td
                            class="iv {analysis.iv_change > 0.8
                                ? 'highlight'
                                : ''}"
                        >
                            {analysis.iv_change.toFixed(2)}
                        </td>
                        <td
                            class="wall {analysis.wall_absorption
                                ? 'absorbed'
                                : ''}"
                        >
                            {analysis.wall_decay_pct.toFixed(1)}%
                            {#if analysis.wall_absorption}
                                <span class="wall-badge">ABS</span>
                            {/if}
                        </td>
                        <td class="score">
                            <div class="score-bar">
                                <div
                                    class="score-fill {getStateClass(
                                        analysis.seller_state,
                                    )}"
                                    style="width: {analysis.panic_score}%"
                                ></div>
                            </div>
                            <span class="score-val"
                                >{analysis.panic_score.toFixed(0)}</span
                            >
                        </td>
                        <td class="state">
                            <span
                                class="state-badge {getStateClass(
                                    analysis.seller_state,
                                )}"
                            >
                                {analysis.seller_state.replace("SELLER_", "")}
                            </span>
                        </td>
                        <td class="signals">
                            {#if analysis.short_covering}
                                <span class="signal short-cover"
                                    >SHORT COVER</span
                                >
                            {/if}
                            {#if analysis.wall_absorption}
                                <span class="signal wall-abs">WALL ABS</span>
                            {/if}
                            {#if analysis.tsq_spike_ratio > 4}
                                <span class="signal tsq-panic">TSQ PANIC</span>
                            {/if}
                        </td>
                    </tr>
                {/each}

                {#if panicAnalysisList.length === 0}
                    <tr>
                        <td colspan="12" class="empty-state">
                            <div class="empty-icon">📡</div>
                            <div>Waiting for subscribed strike data...</div>
                            <div class="hint">
                                Make sure you have subscribed to option
                                instruments
                            </div>
                        </td>
                    </tr>
                {/if}
            </tbody>
        </table>
    </div>

    <!-- Hard Rules Reminder -->
    <div class="rules-reminder">
        <strong>⚠️ Agent Rules:</strong>
        NO direction prediction without panic | NO buyer mode during control | NO
        TRADE is valid
    </div>
</div>

<style>
    .panic-page {
        max-width: 1600px;
        margin: 0 auto;
        padding: 20px;
    }

    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    h1 {
        font-size: 1.5rem;
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .status-bar {
        display: flex;
        gap: 20px;
        align-items: center;
        font-size: 12px;
        color: var(--text-secondary);
    }

    .status.active {
        color: var(--accent-green);
        font-weight: 600;
    }

    .status.inactive {
        color: var(--accent-red);
    }

    /* Multiplier Bar */
    .multiplier-bar {
        display: flex;
        gap: 24px;
        align-items: center;
        padding: 12px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 12px;
        flex-wrap: wrap;
    }

    .multiplier-bar label {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--text-secondary);
    }

    .multiplier-bar input[type="checkbox"] {
        accent-color: var(--accent-blue);
    }

    .small-input {
        width: 60px;
        padding: 4px 8px;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-primary);
        font-size: 12px;
    }

    .multiplier-result {
        margin-left: auto;
        color: var(--accent-purple);
    }

    /* Summary Grid */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }

    .summary-card {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid var(--border-color);
    }

    .summary-card .count {
        font-size: 36px;
        font-weight: 700;
        font-family: var(--font-mono);
        display: block;
    }

    .summary-card .label {
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--text-secondary);
    }

    .summary-card.panic {
        background: rgba(255, 71, 87, 0.1);
        border-color: rgba(255, 71, 87, 0.3);
    }
    .summary-card.panic .count {
        color: var(--accent-red);
    }

    .summary-card.stress {
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.3);
    }
    .summary-card.stress .count {
        color: var(--accent-orange);
    }

    .summary-card.control {
        background: rgba(0, 210, 106, 0.1);
        border-color: rgba(0, 210, 106, 0.3);
    }
    .summary-card.control .count {
        color: var(--accent-green);
    }

    .top-panic-card {
        background: linear-gradient(
            135deg,
            rgba(255, 71, 87, 0.2),
            rgba(139, 92, 246, 0.2)
        );
        border: 1px solid rgba(255, 71, 87, 0.4);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .top-label {
        font-size: 11px;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }

    .top-strike {
        font-size: 18px;
        font-weight: 600;
        font-family: var(--font-mono);
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .top-score {
        font-size: 24px;
        font-weight: 700;
    }

    .top-score.panic {
        color: var(--accent-red);
    }
    .top-score.stress {
        color: var(--accent-orange);
    }
    .top-score.control {
        color: var(--accent-green);
    }

    /* Table */
    .table-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: hidden;
    }

    .panic-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    .panic-table th {
        background: var(--bg-secondary);
        padding: 12px 8px;
        text-align: left;
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border-color);
    }

    .panic-table td {
        padding: 10px 8px;
        border-bottom: 1px solid var(--border-color);
    }

    .panic-table tbody tr:hover {
        background: var(--bg-hover);
    }

    /* Row highlights by state */
    .row-panic {
        background: rgba(255, 71, 87, 0.05);
    }
    .row-stress {
        background: rgba(245, 158, 11, 0.05);
    }

    .strike-num {
        font-family: var(--font-mono);
        font-weight: 600;
        margin-right: 6px;
    }

    .type-badge {
        font-size: 9px;
        padding: 2px 4px;
        border-radius: 4px;
        font-weight: 700;
        background: var(--bg-hover);
        color: var(--text-muted);
        border: 1px solid var(--border-color);
        white-space: nowrap;
    }

    .type-badge.ce {
        background: rgba(0, 210, 106, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(0, 210, 106, 0.3);
    }

    .type-badge.pe {
        background: rgba(255, 71, 87, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(255, 71, 87, 0.3);
    }

    .ltp,
    .oi {
        font-family: var(--font-mono);
    }

    .oi-change.negative,
    .price-change.negative {
        color: var(--accent-red);
    }
    .oi-change.positive,
    .price-change.positive {
        color: var(--accent-green);
    }

    .highlight {
        color: var(--accent-orange) !important;
        font-weight: 600;
    }

    .wall.absorbed {
        color: var(--accent-red);
    }

    .wall-badge {
        background: var(--accent-red);
        color: white;
        font-size: 8px;
        padding: 2px 4px;
        border-radius: 3px;
        margin-left: 4px;
    }

    /* Score column */
    .score {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .score-bar {
        width: 60px;
        height: 6px;
        background: var(--bg-secondary);
        border-radius: 3px;
        overflow: hidden;
    }

    .score-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    .score-fill.control {
        background: var(--accent-green);
    }
    .score-fill.stress {
        background: var(--accent-orange);
    }
    .score-fill.panic {
        background: var(--accent-red);
    }

    .score-val {
        font-family: var(--font-mono);
        font-weight: 600;
        min-width: 24px;
    }

    /* State badge */
    .state-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .state-badge.control {
        background: rgba(0, 210, 106, 0.15);
        color: var(--accent-green);
    }
    .state-badge.stress {
        background: rgba(245, 158, 11, 0.15);
        color: var(--accent-orange);
    }
    .state-badge.panic {
        background: rgba(255, 71, 87, 0.15);
        color: var(--accent-red);
    }

    /* Signals */
    .signals {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
    }

    .signal {
        font-size: 8px;
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: 600;
    }

    .signal.short-cover {
        background: rgba(59, 130, 246, 0.2);
        color: var(--accent-blue);
    }
    .signal.wall-abs {
        background: rgba(139, 92, 246, 0.2);
        color: var(--accent-purple);
    }
    .signal.tsq-panic {
        background: rgba(255, 71, 87, 0.2);
        color: var(--accent-red);
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 60px 20px !important;
        color: var(--text-muted);
    }

    .empty-icon {
        font-size: 48px;
        margin-bottom: 12px;
    }

    .hint {
        font-size: 11px;
        margin-top: 8px;
        color: var(--text-muted);
    }

    /* Rules reminder */
    .rules-reminder {
        margin-top: 20px;
        padding: 12px 16px;
        background: rgba(255, 71, 87, 0.1);
        border: 1px solid rgba(255, 71, 87, 0.3);
        border-radius: 8px;
        font-size: 12px;
        color: var(--text-secondary);
        text-align: center;
    }

    .rules-reminder strong {
        color: var(--accent-red);
    }
</style>
