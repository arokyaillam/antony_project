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
    // ALGO INTERFACES (Market Panic Detection Agent)
    // ========================================

    interface PanicCandle {
        start_ts: number;
        open: number;
        high: number;
        low: number;
        close: number;

        // TBT Metrics
        total_ticks: number;
        avg_score_sum: number;
        max_score: number;
        panic_ticks: number; // count where score >= 60

        // State Counts
        control_ticks: number;
        stress_ticks: number;
        panic_state_ticks: number;

        // Final Results (Computed at Close)
        final_score: number;
        panic_ratio: number;
        state: "CONTROL" | "STRESS" | "PANIC";

        is_closed: boolean;
    }

    interface AlgoState {
        history: PanicCandle[];
        current: PanicCandle | null;
        buyer_mode: boolean;
        decision_reason: string;
        last_pattern: string[];
    }

    let algoStates = $state<Record<string, AlgoState>>({});

    // ========================================
    // STATE MANAGEMENT
    // ========================================

    interface HistoricalSnapshot {
        timestamp: number;
        ltp: number;
        oi: number;
        tsq: number;
        iv: number;
        tbq: number;
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

        // Algo Props
        algo_buyer_mode: boolean;
        algo_reason: string;
        algo_candle_state: string; // Live candle state
        candle_progress: number;
    }

    let instrumentHistory = $state<Record<string, InstrumentHistory>>({});
    let panicAnalysisList = $state<PanicAnalysis[]>([]);
    let lastUpdateTime = $state<number>(Date.now());

    // Config
    const HISTORY_INTERVAL_MS = 5000;
    const LOOKBACK_30S = 6;
    const LOOKBACK_5M = 60;

    // Multipliers
    let is_expiry_day = $state(false);
    let is_open_close = $state(true);
    let range_pct_threshold = $state(35);
    let breaks_5d_extreme = $state(false);

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

    // ========================================
    // ALGO LOGIC (STAGES 1, 2, 3)
    // ========================================

    function createNewCandle(start_ts: number, open: number): PanicCandle {
        return {
            start_ts,
            open,
            high: open,
            low: open,
            close: open,
            total_ticks: 0,
            avg_score_sum: 0,
            max_score: 0,
            panic_ticks: 0,
            control_ticks: 0,
            stress_ticks: 0,
            panic_state_ticks: 0,
            final_score: 0,
            panic_ratio: 0,
            state: "CONTROL",
            is_closed: false,
        };
    }

    function processAlgoTick(
        key: string,
        tickPrice: number,
        tickScore: number,
        tickState: string,
    ) {
        if (!algoStates[key]) {
            algoStates[key] = {
                history: [],
                current: null,
                buyer_mode: false,
                decision_reason: "Initializing...",
                last_pattern: [],
            };
        }

        const algo = algoStates[key];
        const now = Date.now();
        const candleStart = Math.floor(now / 60000) * 60000;

        // Check if we need to close previous candle or start new
        if (!algo.current || algo.current.start_ts !== candleStart) {
            // Close previous candle if it exists
            if (algo.current) {
                closeCandle(algo.current);
                algo.history.push(algo.current);
                if (algo.history.length > 5) algo.history.shift(); // Keep small history

                // Run Stage 3 Logic on Close
                evaluateBuyerMode(algo);
            }
            algo.current = createNewCandle(candleStart, tickPrice);
        }

        // --- STAGE 1: TBT Aggregation ---
        const candle = algo.current;
        candle.close = tickPrice;
        candle.high = Math.max(candle.high, tickPrice);
        candle.low = Math.min(candle.low, tickPrice);

        candle.total_ticks++;
        candle.avg_score_sum += tickScore;
        candle.max_score = Math.max(candle.max_score, tickScore);

        if (tickScore >= 60) candle.panic_ticks++;

        if (tickState === "SELLER_CONTROL") candle.control_ticks++;
        else if (tickState === "SELLER_STRESS") candle.stress_ticks++;
        else if (tickState === "SELLER_PANIC") candle.panic_state_ticks++;

        // Live Classification
        classifyCandle(candle);
    }

    // --- STAGE 2: Candle Classification ---
    function classifyCandle(candle: PanicCandle) {
        if (candle.total_ticks === 0) return;

        const avg_score = candle.avg_score_sum / candle.total_ticks;
        const panic_ratio = candle.panic_ticks / candle.total_ticks;

        // Weighted Score
        // (max * 0.4) + (avg * 0.4) + (ratio * 100 * 0.2)
        const score =
            candle.max_score * 0.4 + avg_score * 0.4 + panic_ratio * 100 * 0.2;

        candle.final_score = score;
        candle.panic_ratio = panic_ratio;

        // Classification Rules
        if (score >= 65 && panic_ratio >= 0.4) {
            candle.state = "PANIC";
        } else if (score >= 45) {
            candle.state = "STRESS";
        } else {
            candle.state = "CONTROL";
        }
    }

    function closeCandle(candle: PanicCandle) {
        classifyCandle(candle);
        candle.is_closed = true;
    }

    // --- STAGE 3: 3-Candle Confirmation ---
    function evaluateBuyerMode(algo: AlgoState) {
        const hist = algo.history;
        if (hist.length < 3) {
            algo.buyer_mode = false;
            algo.decision_reason = "Waiting for 3 candles...";
            return;
        }

        const C0 = hist[hist.length - 1]; // Newest closed
        const C1 = hist[hist.length - 2];
        const C2 = hist[hist.length - 3];

        algo.last_pattern = [C2.state, C1.state, C0.state];

        // Rule D: NO TRADE ZONE
        const controlCount = [C0, C1, C2].filter(
            (c) => c.state === "CONTROL",
        ).length;
        if (controlCount > 1) {
            algo.buyer_mode = false;
            algo.decision_reason = "No Trade Zone (Control Dominance)";
            return;
        }

        // Rule C: PANIC REJECTION
        if (C1.state === "PANIC" && C0.state === "CONTROL") {
            algo.buyer_mode = false;
            algo.decision_reason = "Panic Rejected by Control";
            return;
        }

        // Rule A: STRONG PANIC CONFIRMATION
        if (
            C1.state === "PANIC" &&
            C0.state === "PANIC" &&
            C0.final_score >= C1.final_score
        ) {
            algo.buyer_mode = true;
            algo.decision_reason = "Strong Panic Confirmation";
            return;
        }

        // Rule B: PANIC CONTINUATION
        if (
            C2.state === "PANIC" &&
            C1.state === "PANIC" &&
            C0.state === "STRESS" &&
            C0.final_score >= 50
        ) {
            algo.buyer_mode = true;
            algo.decision_reason = "Panic Continuation (High Stress)";
            return;
        }

        // Strict Discipline: Default to False
        algo.buyer_mode = false;
        algo.decision_reason = "No Setup Triggered";
    }

    // ========================================
    // MAIN CALCULATION
    // ========================================

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
        const snapshot30s =
            snapshots.length >= LOOKBACK_30S
                ? snapshots[snapshots.length - LOOKBACK_30S]
                : snapshots[0];
        const recentSnapshots = snapshots.slice(-LOOKBACK_5M);
        const avgTsq5m =
            recentSnapshots.length > 0
                ? recentSnapshots.reduce((sum, s) => sum + s.tsq, 0) /
                  recentSnapshots.length
                : tsq;

        const oi_prev = snapshot30s?.oi || oi;
        const oi_change_pct =
            oi_prev > 0 ? ((oi - oi_prev) / oi_prev) * 100 : 0;
        const price_30s = snapshot30s?.ltp || ltp;
        const price_change_pct =
            price_30s > 0 ? ((ltp - price_30s) / price_30s) * 100 : 0;
        const short_covering = oi_change_pct < -1.0 && price_change_pct > 0.3;

        const prev_wall = history.prev_wall_qty || tbq;
        const wall_decay_pct =
            prev_wall > 0 ? ((prev_wall - tbq) / prev_wall) * 100 : 0;
        const wall_absorption = wall_decay_pct >= 30;

        const replenish_ratio =
            history.removed_qty > 0
                ? history.refilled_qty / history.removed_qty
                : 1.0;
        const tsq_spike_ratio = avgTsq5m > 0 ? tsq / avgTsq5m : 1.0;
        const velocity = Math.abs(ltp - price_30s);
        const velocity_ratio = velocity / NORMAL_VELOCITY;
        const iv_prev = snapshot30s?.iv || iv;
        const iv_change = iv - iv_prev;

        // Base Score Components
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

        const base_score =
            wall_absorption_score * 20 +
            replenish_failure_score * 15 +
            oi_divergence_score * 15 +
            tsq_spike_score * 15 +
            velocity_score * 15 +
            iv_spike_score * 10;

        const panic_score = Math.min(
            base_score * historical_multiplier() * time_multiplier(),
            100,
        );

        let seller_state: "SELLER_CONTROL" | "SELLER_STRESS" | "SELLER_PANIC";
        if (panic_score >= 60) seller_state = "SELLER_PANIC";
        else if (panic_score >= 40) seller_state = "SELLER_STRESS";
        else seller_state = "SELLER_CONTROL";

        const { strike, type } = parseStrikeFromKey(key);

        // Pass to Algo
        processAlgoTick(key, ltp, panic_score, seller_state);

        // Retrieve Algo Status
        const algo = algoStates[key];
        const candleProgress = algo?.current
            ? ((Math.floor(Date.now() / 1000) % 60) / 60) * 100
            : 0;

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

            // Algo Props
            algo_buyer_mode: algo?.buyer_mode || false,
            algo_reason: algo?.decision_reason || "Init",
            algo_candle_state: algo?.current?.state || "WAIT",
            candle_progress: candleProgress,
        };
    }

    function updateAnalysis(marketData: Record<string, InstrumentFeed>) {
        const now = Date.now();
        const analyses: PanicAnalysis[] = [];

        for (const [key, feed] of Object.entries(marketData)) {
            if (key.includes("INDEX")) continue;

            const ff = getMarketFF(feed);
            if (!ff) continue;

            if (!instrumentHistory[key]) {
                instrumentHistory[key] = {
                    snapshots: [],
                    prev_wall_qty: ff.tbq || 0,
                    removed_qty: 0,
                    refilled_qty: 0,
                };
            }

            const history = instrumentHistory[key];
            if (
                history.snapshots.length === 0 ||
                now -
                    (history.snapshots[history.snapshots.length - 1]
                        ?.timestamp || 0) >=
                    HISTORY_INTERVAL_MS
            ) {
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

                if (history.snapshots.length > LOOKBACK_5M) {
                    history.snapshots.shift();
                }
            }

            const analysis = calculatePanicAnalysis(key, feed, history);
            if (analysis) {
                analyses.push(analysis);
            }
        }

        panicAnalysisList = analyses.sort(
            (a, b) => b.panic_score - a.panic_score,
        );
        lastUpdateTime = now;
    }

    let unsubscribeMarket: (() => void) | null = null;
    onMount(async () => {
        await syncSubscriptions();
        connectStream();
        unsubscribeMarket = marketDataStore.subscribe((data) => {
            if (data && Object.keys(data).length > 0) updateAnalysis(data);
        });
    });

    onDestroy(() => {
        if (unsubscribeMarket) unsubscribeMarket();
    });

    function getStateClass(state: string): string {
        if (state === "SELLER_PANIC" || state === "PANIC") return "panic";
        if (state === "SELLER_STRESS" || state === "STRESS") return "stress";
        return "control";
    }

    let topPanicStrike = $derived(
        panicAnalysisList.length > 0 ? panicAnalysisList[0] : null,
    );
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
    let buyerModeCount = $derived(
        panicAnalysisList.filter((a) => a.algo_buyer_mode).length,
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
        <label
            ><input type="checkbox" bind:checked={is_expiry_day} /> Expiry Day (2x)</label
        >
        <label
            ><input type="checkbox" bind:checked={is_open_close} /> Open/Close (1.5x)</label
        >
        <label
            ><input type="checkbox" bind:checked={breaks_5d_extreme} /> 5D Break
            (2x)</label
        >
        <label
            >Range %: <input
                type="number"
                bind:value={range_pct_threshold}
                class="small-input"
            /></label
        >
        <span class="multiplier-result"
            >Final Multiplier: <strong
                >{(time_multiplier() * historical_multiplier()).toFixed(
                    2,
                )}x</strong
            ></span
        >
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
        <div class="summary-card buy">
            <span class="count">{buyerModeCount}</span>
            <span class="label">BUYER MODE</span>
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
                    <th style="width: 120px;">Strike</th>
                    <th style="width: 70px;">LTP</th>
                    <th style="width: 100px;">State (TBT)</th>
                    <th style="width: 100px;">Score</th>
                    <th style="width: 100px;">Algo Candle</th>
                    <th>3-Candle Sig</th>
                    <th>Reason</th>
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
                                    : analysis.option_type === 'PE'
                                      ? 'pe'
                                      : 'unk'}"
                            >
                                {analysis.option_type}
                            </span>
                        </td>
                        <td class="ltp">{analysis.ltp.toFixed(2)}</td>

                        <td class="state">
                            <span
                                class="state-badge {getStateClass(
                                    analysis.seller_state,
                                )}"
                            >
                                {analysis.seller_state.replace("SELLER_", "")}
                            </span>
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

                        <!-- Algo Candle -->
                        <td class="algo-candle">
                            <div class="candle-mini">
                                <span
                                    class="state-dot {getStateClass(
                                        analysis.algo_candle_state,
                                    )}"
                                ></span>
                                {analysis.algo_candle_state}
                            </div>
                            <div class="progress">
                                <div
                                    class="fill"
                                    style="width: {analysis.candle_progress}%"
                                ></div>
                            </div>
                        </td>

                        <!-- 3-Candle Sig -->
                        <td class="algo-sig">
                            {#if analysis.algo_buyer_mode}
                                <span class="buy-badge">BUYER ENABLED</span>
                            {:else}
                                <span class="wait-badge">NO TRADE</span>
                            {/if}
                        </td>

                        <!-- Reason -->
                        <td class="algo-reason">
                            {analysis.algo_reason}
                        </td>
                    </tr>
                {/each}

                {#if panicAnalysisList.length === 0}
                    <tr>
                        <td colspan="7" class="empty-state">
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
        <strong>⚠️ Panic Algo Rules:</strong> &nbsp; 1. Wait for PANIC > PANIC (Growing
        Fear) &nbsp;|&nbsp; 2. Wait for PANIC > PANIC > STRESS (Sustain) &nbsp;|&nbsp;
        3. No Trade if Control Dominates
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
        grid-template-columns: repeat(4, 1fr) auto;
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

    .summary-card.buy {
        background: rgba(139, 92, 246, 0.1);
        border-color: rgba(139, 92, 246, 0.3);
    }
    .summary-card.buy .count {
        color: var(--accent-purple);
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
        min-width: 200px;
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

    /* Algo UI */
    .algo-candle {
        font-family: var(--font-mono);
        font-size: 11px;
    }
    .candle-mini {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 4px;
    }
    .state-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--text-muted);
    }
    .state-dot.panic {
        background: var(--accent-red);
    }
    .state-dot.stress {
        background: var(--accent-orange);
    }
    .state-dot.control {
        background: var(--accent-green);
    }

    .progress {
        width: 100%;
        height: 2px;
        background: var(--bg-secondary);
        position: relative;
    }
    .progress .fill {
        height: 100%;
        background: var(--text-secondary);
        transition: width 1s linear;
    }

    .buy-badge {
        background: rgba(0, 210, 106, 0.2);
        color: var(--accent-green);
        border: 1px solid rgba(0, 210, 106, 0.4);
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 10px;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    .wait-badge {
        color: var(--text-muted);
        font-size: 10px;
        border: 1px dashed var(--border-color);
        padding: 2px 6px;
        border-radius: 4px;
    }

    .algo-reason {
        font-size: 10px;
        color: var(--text-secondary);
        max-width: 150px;
        white-space: normal;
        line-height: 1.2;
    }

    @keyframes pulse {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
        100% {
            opacity: 1;
        }
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
