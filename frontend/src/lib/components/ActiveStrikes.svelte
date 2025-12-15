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
        <div class="cards-grid">
            <!-- Highest CE OI -->
            {#if maxCeOI?.ceData}
                <div class="card card-ce-oi">
                    <div class="card-header">
                        <span class="badge">HIGHEST CE OI</span>
                        <span class="strike">{maxCeOI.strike} CE</span>
                    </div>
                    <div class="card-body">
                        <div class="row main-val">
                            <span class="label">OI</span>
                            <span class="val">{fmt(maxCeOI.ceData.oi)}</span>
                        </div>
                        <div class="row">
                            <span class="label">Change</span>
                            <span
                                class="val"
                                class:pos={maxCeOI.ceData.oi_diff > 0}
                                class:neg={maxCeOI.ceData.oi_diff < 0}
                                >{fmt(maxCeOI.ceData.oi_diff)}</span
                            >
                        </div>
                        <div class="divider"></div>
                        <div class="row">
                            <span class="label">LTP</span>
                            <span class="val"
                                >{fmtPr(maxCeOI.ceData.close)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">IV</span>
                            <span class="val">{fmtG(maxCeOI.ceData.iv)}</span>
                        </div>
                        <div class="row">
                            <span class="label">Delta</span>
                            <span class="val"
                                >{fmtG(maxCeOI.ceData.greeks.delta)}</span
                            >
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Highest PE OI -->
            {#if maxPeOI?.peData}
                <div class="card card-pe-oi">
                    <div class="card-header">
                        <span class="badge">HIGHEST PE OI</span>
                        <span class="strike">{maxPeOI.strike} PE</span>
                    </div>
                    <div class="card-body">
                        <div class="row main-val">
                            <span class="label">OI</span>
                            <span class="val">{fmt(maxPeOI.peData.oi)}</span>
                        </div>
                        <div class="row">
                            <span class="label">Change</span>
                            <span
                                class="val"
                                class:pos={maxPeOI.peData.oi_diff > 0}
                                class:neg={maxPeOI.peData.oi_diff < 0}
                                >{fmt(maxPeOI.peData.oi_diff)}</span
                            >
                        </div>
                        <div class="divider"></div>
                        <div class="row">
                            <span class="label">LTP</span>
                            <span class="val"
                                >{fmtPr(maxPeOI.peData.close)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">IV</span>
                            <span class="val">{fmtG(maxPeOI.peData.iv)}</span>
                        </div>
                        <div class="row">
                            <span class="label">Delta</span>
                            <span class="val"
                                >{fmtG(maxPeOI.peData.greeks.delta)}</span
                            >
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Highest CE Volume -->
            {#if maxCeVol?.ceData}
                <div class="card card-ce-vol">
                    <div class="card-header">
                        <span class="badge">HIGHEST CE VOL</span>
                        <span class="strike">{maxCeVol.strike} CE</span>
                    </div>
                    <div class="card-body">
                        <div class="row main-val">
                            <span class="label">Volume</span>
                            <span class="val"
                                >{fmt(maxCeVol.ceData.volume_1m)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Change</span>
                            <span
                                class="val"
                                class:pos={maxCeVol.ceData.volume_diff > 0}
                                class:neg={maxCeVol.ceData.volume_diff < 0}
                                >{fmt(maxCeVol.ceData.volume_diff)}</span
                            >
                        </div>
                        <div class="divider"></div>
                        <div class="row">
                            <span class="label">LTP</span>
                            <span class="val"
                                >{fmtPr(maxCeVol.ceData.close)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Vega</span>
                            <span class="val"
                                >{fmtG(maxCeVol.ceData.greeks.vega)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Gamma</span>
                            <span class="val"
                                >{fmtG(maxCeVol.ceData.greeks.gamma)}</span
                            >
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Highest PE Volume -->
            {#if maxPeVol?.peData}
                <div class="card card-pe-vol">
                    <div class="card-header">
                        <span class="badge">HIGHEST PE VOL</span>
                        <span class="strike">{maxPeVol.strike} PE</span>
                    </div>
                    <div class="card-body">
                        <div class="row main-val">
                            <span class="label">Volume</span>
                            <span class="val"
                                >{fmt(maxPeVol.peData.volume_1m)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Change</span>
                            <span
                                class="val"
                                class:pos={maxPeVol.peData.volume_diff > 0}
                                class:neg={maxPeVol.peData.volume_diff < 0}
                                >{fmt(maxPeVol.peData.volume_diff)}</span
                            >
                        </div>
                        <div class="divider"></div>
                        <div class="row">
                            <span class="label">LTP</span>
                            <span class="val"
                                >{fmtPr(maxPeVol.peData.close)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Vega</span>
                            <span class="val"
                                >{fmtG(maxPeVol.peData.greeks.vega)}</span
                            >
                        </div>
                        <div class="row">
                            <span class="label">Gamma</span>
                            <span class="val"
                                >{fmtG(maxPeVol.peData.greeks.gamma)}</span
                            >
                        </div>
                    </div>
                </div>
            {/if}
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

    .cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
    }

    .card {
        background: var(--bg-card, #1e1e1e);
        border: 1px solid var(--border-color, #333);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
    }

    /* Highlight Colors */
    .card-ce-oi,
    .card-ce-vol {
        border-top: 3px solid #22c55e; /* Green for Calls */
    }
    .card-pe-oi,
    .card-pe-vol {
        border-top: 3px solid #ef4444; /* Red for Puts */
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .badge {
        font-size: 10px;
        font-weight: 800;
        background: rgba(255, 255, 255, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
        color: #a1a1aa;
    }
    .strike {
        font-size: 16px;
        font-weight: 800;
        color: #fbbf24;
    }

    .card-body {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .row {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #d4d4d8;
    }

    .label {
        color: #71717a;
    }
    .val {
        font-family: "JetBrains Mono", monospace;
        font-weight: 600;
    }

    .main-val {
        font-size: 14px;
        font-weight: 700;
        color: #fff;
    }

    .divider {
        height: 1px;
        background: #333;
        margin: 4px 0;
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
