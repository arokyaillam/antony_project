<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { createChart, ColorType } from "lightweight-charts";
    import { candleDataStore } from "$lib/stores/candleData";
    import { marketContext } from "$lib/stores/marketContext";

    // We need to calculate Total CE OI Change vs Total PE OI Change
    // And push it to the chart every X seconds.

    let chartContainer: HTMLElement;
    let chart: any;
    let ceSeries: any;
    let peSeries: any;

    // History
    // Since we don't have backend history for "Aggregates" yet, we start fresh on load.
    let dataCE: { time: number; value: number }[] = [];
    let dataPE: { time: number; value: number }[] = [];

    onMount(() => {
        chart = createChart(chartContainer, {
            layout: {
                background: { type: ColorType.Solid, color: "#1e1e1e" },
                textColor: "#d1d5db",
            },
            width: chartContainer.clientWidth,
            height: 400,
            grid: {
                vertLines: { color: "rgba(255, 255, 255, 0.05)" },
                horzLines: { color: "rgba(255, 255, 255, 0.05)" },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: true,
            },
        });

        // CE Series (Green for Bullish view if CE unwinds? No, let's just plot Raw OI Chg)
        // Usually:
        // CE OI Chg UP -> Calls being written -> Resistance -> Bearish (Red?)
        // PE OI Chg UP -> Puts being written -> Support -> Bullish (Green?)
        // Let's stick to standard colors: CE = Red Line, PE = Green Line.
        ceSeries = chart.addLineSeries({
            color: "#ef4444",
            title: "CE OI Chg (Resist)",
        });
        peSeries = chart.addLineSeries({
            color: "#22c55e",
            title: "PE OI Chg (Supp)",
        });

        const handleResize = () => {
            chart.applyOptions({ width: chartContainer.clientWidth });
        };
        window.addEventListener("resize", handleResize);

        // Interval to snapshot aggregates (every 3 seconds)
        const interval = setInterval(() => {
            updateChart();
        }, 3000);

        return () => {
            window.removeEventListener("resize", handleResize);
            clearInterval(interval);
            chart.remove();
        };
    });

    function updateChart() {
        if (!chart || !$marketContext.chain) return;

        const strikes = Object.keys($marketContext.chain).map(Number);
        if (strikes.length === 0) return;

        let totCeOiChg = 0;
        let totPeOiChg = 0;

        strikes.forEach((strike) => {
            const c = $marketContext.chain[strike];
            if (c.CE && $candleDataStore[c.CE])
                totCeOiChg += $candleDataStore[c.CE].oi_diff || 0;
            if (c.PE && $candleDataStore[c.PE])
                totPeOiChg += $candleDataStore[c.PE].oi_diff || 0;
        });

        const time = Math.floor(Date.now() / 1000) as any; // lightweight charts expects seconds (UTCTimestamp)

        // Add points
        // NOTE: Lightweight charts strictly requires ascending time.
        // We use system time.

        ceSeries.update({ time, value: totCeOiChg });
        peSeries.update({ time, value: totPeOiChg });
    }
</script>

<div class="sentiment-chart-wrapper">
    <h3>Live Sentiment (Aggregate OI Change)</h3>
    <div class="chart-box" bind:this={chartContainer}></div>
    <div class="legend">
        <span class="l-item pe">PE OI Chg (Support)</span>
        <span class="l-item ce">CE OI Chg (Resistance)</span>
    </div>
</div>

<style>
    .sentiment-chart-wrapper {
        background: #1e1e1e;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #333;
    }
    h3 {
        margin: 0 0 12px 0;
        color: #e4e4e7;
        font-size: 14px;
        font-weight: 600;
    }
    .chart-box {
        width: 100%;
        height: 400px;
    }
    .legend {
        display: flex;
        gap: 16px;
        margin-top: 8px;
        justify-content: center;
    }
    .l-item {
        font-size: 12px;
        font-weight: bold;
    }
    .pe {
        color: #22c55e;
    }
    .ce {
        color: #ef4444;
    }
</style>
