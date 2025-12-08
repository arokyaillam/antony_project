<!-- Test Page - Test global stream with instrument -->
<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import {
        connectStream,
        disconnectStream,
        subscribeToStream,
        isStreamConnected,
    } from "$lib/stores/stream";

    const API_BASE = "http://localhost:8000";

    // Test instrument
    let instrument = $state("NSE_INDEX|Nifty 50");
    let streamData = $state<any[]>([]);
    let isConnected = $state(false);
    let unsubscribe: (() => void) | null = null;

    const sampleInstruments = [
        "NSE_INDEX|Nifty 50",
        "NSE_INDEX|Nifty Bank",
        "NSE_INDEX|India VIX",
    ];

    function handleConnect() {
        // First subscribe to backend feed
        fetch(`${API_BASE}/api/v1/feed/subscribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                instrument_keys: [instrument],
                mode: "full",
            }),
        }).then(() => {
            // Then connect to SSE stream with filter
            connectStream([instrument]);
            isConnected = true;

            // Subscribe to receive data
            unsubscribe = subscribeToStream((data) => {
                streamData = [data, ...streamData.slice(0, 9)];
            });
        });
    }

    function handleDisconnect() {
        disconnectStream();
        if (unsubscribe) unsubscribe();
        isConnected = false;
        streamData = [];
    }

    onDestroy(() => {
        if (unsubscribe) unsubscribe();
    });
</script>

<div class="test-page">
    <h1>🧪 Stream Test</h1>

    <div class="controls">
        <select bind:value={instrument}>
            {#each sampleInstruments as inst}
                <option value={inst}>{inst}</option>
            {/each}
        </select>

        {#if isConnected}
            <button class="btn-stop" onclick={handleDisconnect}>⏹️ Stop</button>
        {:else}
            <button class="btn-start" onclick={handleConnect}>▶️ Start</button>
        {/if}
    </div>

    <div class="status">
        {isConnected ? "🟢 Connected" : "⚫ Disconnected"}
    </div>

    {#if streamData.length > 0}
        <div class="data-log">
            <h3>Live Data</h3>
            {#each streamData as entry}
                <pre>{JSON.stringify(entry, null, 2).slice(0, 300)}...</pre>
            {/each}
        </div>
    {/if}
</div>

<style>
    .test-page {
        max-width: 600px;
        margin: 0 auto;
        text-align: center;
    }

    h1 {
        font-size: 24px;
        margin-bottom: 24px;
    }

    .controls {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-bottom: 20px;
    }

    select {
        padding: 10px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 14px;
    }

    .btn-start,
    .btn-stop {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        border: none;
    }

    .btn-start {
        background: var(--accent-green);
        color: white;
    }
    .btn-stop {
        background: var(--accent-red);
        color: white;
    }

    .status {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 24px;
    }

    .data-log {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        text-align: left;
    }

    .data-log h3 {
        font-size: 14px;
        margin-bottom: 12px;
        color: var(--text-secondary);
    }

    pre {
        background: var(--bg-secondary);
        padding: 10px;
        border-radius: 6px;
        font-size: 11px;
        font-family: var(--font-mono);
        color: var(--text-secondary);
        overflow-x: auto;
        white-space: pre-wrap;
        margin-bottom: 8px;
    }
</style>
