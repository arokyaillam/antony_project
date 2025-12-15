<script lang="ts">
    import {
        candleDataStore,
        type CandleDetails,
    } from "$lib/stores/candleData";
    import { marketContext } from "$lib/stores/marketContext";
    import ActiveStrikeCard from "./ActiveStrikeCard.svelte";

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
</script>

<div class="active-strikes-container">
    <h2 class="section-title">🔥 Active Strikes</h2>

    {#if activeData.length > 0}
        <div class="cards-grid">
            {#if maxCeOI?.ceData}
                <ActiveStrikeCard
                    instrumentKey={maxCeOI.ceData.instrument_key}
                    title="MAX CE OI"
                    strikeTitle="{maxCeOI.strike} CE"
                    color="#22c55e"
                />
            {/if}
            {#if maxPeOI?.peData}
                <ActiveStrikeCard
                    instrumentKey={maxPeOI.peData.instrument_key}
                    title="MAX PE OI"
                    strikeTitle="{maxPeOI.strike} PE"
                    color="#ef4444"
                />
            {/if}
            {#if maxCeVol?.ceData}
                <ActiveStrikeCard
                    instrumentKey={maxCeVol.ceData.instrument_key}
                    title="MAX CE VOL"
                    strikeTitle="{maxCeVol.strike} CE"
                    color="#22c55e"
                />
            {/if}
            {#if maxPeVol?.peData}
                <ActiveStrikeCard
                    instrumentKey={maxPeVol.peData.instrument_key}
                    title="MAX PE VOL"
                    strikeTitle="{maxPeVol.strike} PE"
                    color="#ef4444"
                />
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
        max-width: 1400px;
        margin-left: auto;
        margin-right: auto;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 24px;
        background: linear-gradient(to right, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    .cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
        padding: 0 16px;
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
