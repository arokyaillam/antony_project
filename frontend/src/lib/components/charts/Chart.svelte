<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { createChart, ColorType, CrosshairMode } from "lightweight-charts";

    // Props
    interface ChartProps {
        data?: any[];
        colors?: {
            backgroundColor?: string;
            lineColor?: string;
            textColor?: string;
            areaTopColor?: string;
            areaBottomColor?: string;
        };
        height?: number;
        autosize?: boolean;
    }

    let {
        data = [],
        colors = {
            backgroundColor: "transparent",
            lineColor: "#2962FF",
            textColor: "#d1d5db", // tailwind gray-300
            areaTopColor: "#2962FF",
            areaBottomColor: "rgba(41, 98, 255, 0.28)",
        },
        height = 300,
        autosize = true,
    }: ChartProps = $props();

    let chartContainer: HTMLElement;
    let chart: any;
    let series: any;

    onMount(() => {
        if (!chartContainer) return;

        // 1. Initialize Chart
        chart = createChart(chartContainer, {
            layout: {
                background: {
                    type: ColorType.Solid,
                    color: colors.backgroundColor,
                },
                textColor: colors.textColor,
            },
            width: chartContainer.clientWidth,
            height: height,
            grid: {
                vertLines: { color: "rgba(42, 46, 57, 0)" }, // Transparent grid
                horzLines: { color: "rgba(42, 46, 57, 0.2)" },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            timeScale: {
                borderColor: "#485c7b",
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // 2. Add Series (Default to Candlestick or Area based on data structure??)
        // For simplicity, let's create a generic Area series for now,
        // OR better, we allow the parent to define the series.
        // But the user asked to "add library", often implying "give me a working chart".
        // Let's make this a "CandleChart" specifically if that's the main case,
        // or a "SmartChart" that detects.
        // Typical HFT usage = Candlestick.

        // Let's implement Candlestick Series by default.
        series = chart.addCandlestickSeries({
            upColor: "#26a69a",
            downColor: "#ef5350",
            borderVisible: false,
            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
        });

        if (data.length > 0) {
            series.setData(data);
        }

        chart.timeScale().fitContent();

        // 3. Resize Observer
        const handleResize = () => {
            if (chartContainer) {
                chart.applyOptions({ width: chartContainer.clientWidth });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    });

    // Reactivity: storage for updates
    $effect(() => {
        if (series && data) {
            // If we receive a SINGLE update vs FULL History?
            // Assuming `data` prop is FULL HISTORY for now.
            // We can optimize later.
            series.setData(data);
        }
    });
</script>

<div class="chart-wrapper" bind:this={chartContainer} style:height="{height}px">
    <!-- Chart renders here -->
</div>

<style>
    .chart-wrapper {
        width: 100%;
        position: relative;
    }
</style>
