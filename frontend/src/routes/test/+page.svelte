<!-- Test Page - Test all streams -->
<script lang="ts">
    import { onDestroy } from "svelte";
    import {
        connectStream,
        disconnectStream,
        subscribeToStream,
    } from "$lib/stores/stream";
    import {
        connectCandleStream,
        disconnectCandleStream,
        subscribeToCandleStream,
    } from "$lib/stores/candles";
    import {
        connectOrderStream,
        disconnectOrderStream,
        subscribeToOrderStream,
    } from "$lib/stores/orders";

    const API_BASE = "http://localhost:8000";

    let instrument = $state("NSE_INDEX|Nifty 50");

    // Raw stream
    let rawConnected = $state(false);
    let rawData = $state<any[]>([]);
    let rawUnsub: (() => void) | null = null;

    // Candle stream
    let candleConnected = $state(false);
    let candleData = $state<any[]>([]);
    let candleUnsub: (() => void) | null = null;

    // Order stream
    let orderConnected = $state(false);
    let orderData = $state<any[]>([]);
    let orderUnsub: (() => void) | null = null;

    const sampleInstruments = [
        "NSE_INDEX|Nifty 50",
        "NSE_INDEX|Nifty Bank",
        "NSE_INDEX|India VIX",
        "NSE_FO|41908",
    ];

    async function subscribe() {
        await fetch(`${API_BASE}/api/v1/feed/subscribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                instrument_keys: [instrument],
                mode: "full",
            }),
        });
    }

    // Raw
    async function startRaw() {
        await subscribe();
        connectStream([instrument]);
        rawConnected = true;
        rawUnsub = subscribeToStream((data) => {
            rawData = [data, ...rawData.slice(0, 4)];
        });
    }

    function stopRaw() {
        disconnectStream();
        if (rawUnsub) rawUnsub();
        rawConnected = false;
        rawData = [];
    }

    // Candle
    async function startCandles() {
        await subscribe();
        connectCandleStream([instrument]);
        candleConnected = true;
        candleUnsub = subscribeToCandleStream((data) => {
            candleData = [data, ...candleData.slice(0, 4)];
        });
    }

    function stopCandles() {
        disconnectCandleStream();
        if (candleUnsub) candleUnsub();
        candleConnected = false;
        candleData = [];
    }

    // Orders
    function startOrders() {
        connectOrderStream();
        orderConnected = true;
        orderUnsub = subscribeToOrderStream((data) => {
            orderData = [data, ...orderData.slice(0, 4)];
        });
    }

    function stopOrders() {
        disconnectOrderStream();
        if (orderUnsub) orderUnsub();
        orderConnected = false;
        orderData = [];
    }

    onDestroy(() => {
        if (rawUnsub) rawUnsub();
        if (candleUnsub) candleUnsub();
        if (orderUnsub) orderUnsub();
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
    </div>

    <div class="streams">
        <!-- Raw -->
        <div class="stream-box">
            <h3>📡 Raw</h3>
            <div class="status">{rawConnected ? "🟢" : "⚫"}</div>
            <button onclick={rawConnected ? stopRaw : startRaw}
                >{rawConnected ? "Stop" : "Start"}</button
            >
            {#if rawData.length > 0}
                <pre>{JSON.stringify(rawData[0], null, 2).slice(
                        0,
                        150,
                    )}...</pre>
            {/if}
        </div>

        <!-- Candle -->
        <div class="stream-box">
            <h3>📊 Candle</h3>
            <div class="status">{candleConnected ? "🟢" : "⚫"}</div>
            <button onclick={candleConnected ? stopCandles : startCandles}
                >{candleConnected ? "Stop" : "Start"}</button
            >
            {#if candleData.length > 0}
                <pre>{JSON.stringify(candleData[0], null, 2).slice(
                        0,
                        300,
                    )}...</pre>
            {/if}
        </div>

        <!-- Orders -->
        <div class="stream-box">
            <h3>📋 Orders</h3>
            <div class="status">{orderConnected ? "🟢" : "⚫"}</div>
            <button onclick={orderConnected ? stopOrders : startOrders}
                >{orderConnected ? "Stop" : "Start"}</button
            >
            {#if orderData.length > 0}
                <pre>{JSON.stringify(orderData[0], null, 2).slice(
                        0,
                        200,
                    )}...</pre>
            {:else if orderConnected}
                <p class="hint">Waiting for order updates...</p>
            {/if}
        </div>
    </div>
</div>

<style>
    .test-page {
        max-width: 900px;
        margin: 0 auto;
    }
    h1 {
        text-align: center;
        margin-bottom: 24px;
    }
    .controls {
        display: flex;
        justify-content: center;
        margin-bottom: 24px;
    }
    select {
        padding: 10px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 14px;
    }
    .streams {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }
    .stream-box {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
    }
    .stream-box h3 {
        font-size: 14px;
        margin-bottom: 12px;
    }
    .status {
        font-size: 20px;
        margin-bottom: 12px;
    }
    button {
        padding: 8px 16px;
        background: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        cursor: pointer;
        margin-bottom: 12px;
    }
    pre {
        background: var(--bg-secondary);
        padding: 10px;
        border-radius: 6px;
        font-size: 9px;
        font-family: var(--font-mono);
        color: var(--text-secondary);
        overflow-x: auto;
        white-space: pre-wrap;
    }
    .hint {
        font-size: 12px;
        color: var(--text-muted);
    }
</style>
