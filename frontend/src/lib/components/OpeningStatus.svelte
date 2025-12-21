<script lang="ts">
    export let prevHigh: number;
    export let prevLow: number;
    export let prevClose: number;
    export let liveOpen: number;

    let status = "WAITING";
    let color = "#71717a"; // Zinc 500 (Gray)

    $: calculateStatus(liveOpen, prevHigh, prevLow, prevClose);

    function calculateStatus(
        open: number,
        high: number,
        low: number,
        close: number,
    ) {
        if (!open || !high || !low || !close) {
            status = "Waiting for Data";
            color = "#71717a";
            return;
        }

        const diff = open - close;

        if (Math.abs(diff) <= 5) {
            status = "FLAT";
            color = "#a1a1aa"; // Light Gray
        } else if (open > high) {
            status = "GAP UP";
            color = "#22c55e"; // Green
        } else if (open < low) {
            status = "GAP DOWN";
            color = "#ef4444"; // Red
        } else if (open > close) {
            status = "POSITIVE OPEN";
            color = "#84cc16"; // Lime/Light Green
        } else {
            status = "NEGATIVE OPEN";
            color = "#f87171"; // Light Red
        }
    }
</script>

<div
    class="status-badge"
    style="background-color: {color}20; color: {color}; border-color: {color}40;"
>
    <span class="status-text">{status}</span>
    {#if liveOpen}
        <span class="diff">
            ({liveOpen - prevClose > 0 ? "+" : ""}{(
                liveOpen - prevClose
            ).toFixed(2)})
        </span>
    {/if}
</div>

<style>
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid;
        font-family: "JetBrains Mono", monospace;
        font-weight: 600;
        font-size: 13px;
    }

    .diff {
        font-size: 11px;
        opacity: 0.8;
    }
</style>
