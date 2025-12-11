<script lang="ts">
    import { onDestroy } from "svelte";
    import {
        connectCandleStream,
        disconnectCandleStream,
        isCandleConnected,
    } from "$lib/stores/candles";
    import { candleDataStore } from "$lib/stores/candleData";
    import { isFeedConnected, subscribeToFeed } from "$lib/stores/feed";

    let instrument = $state("NSE_FO|48202"); // Default example
    let instruments = [
        "NSE_FO|48202",
        "NSE_INDEX|Nifty 50",
        "NSE_INDEX|Nifty Bank",
    ];

    // Connect on mount (optional, or manual)
    function connect() {
        subscribeToFeed([instrument]); // Ensure subscription
        connectCandleStream([instrument]);
    }

    function disconnect() {
        disconnectCandleStream();
    }

    // Derived data for the selected instrument
    let data = $derived($candleDataStore[instrument] || null);

    onDestroy(() => {
        disconnectCandleStream();
    });
</script>

<div class="p-6 max-w-6xl mx-auto space-y-6">
    <div
        class="flex items-center justify-between bg-zinc-900 p-4 rounded-xl border border-zinc-800"
    >
        <div class="flex items-center gap-4">
            <h1 class="text-xl font-bold text-zinc-100">
                🕯️ Candle Data Inspector
            </h1>
            <div
                class="px-3 py-1 rounded-full text-xs font-mono"
                class:bg-green-500-20={$isCandleConnected}
                class:text-green-500={$isCandleConnected}
                class:bg-red-500-20={!$isCandleConnected}
                class:text-red-500={!$isCandleConnected}
            >
                {$isCandleConnected ? "CONNECTED" : "DISCONNECTED"}
            </div>
        </div>

        <div class="flex gap-3">
            <select
                bind:value={instrument}
                class="bg-zinc-800 border-zinc-700 rounded px-3 py-1 text-sm text-zinc-200"
            >
                {#each instruments as inst}
                    <option value={inst}>{inst}</option>
                {/each}
            </select>
            <button
                onclick={connect}
                class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded text-sm font-medium transition"
            >
                Connect & Subscribe
            </button>
            <button
                onclick={disconnect}
                class="bg-zinc-700 hover:bg-zinc-600 text-white px-4 py-1.5 rounded text-sm font-medium transition"
            >
                Disconnect
            </button>
        </div>
    </div>

    {#if data}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Main Price Card -->
            <div
                class="bg-zinc-900 p-5 rounded-xl border border-zinc-800 col-span-1"
            >
                <div class="text-zinc-400 text-xs font-mono mb-1">
                    {data.timestamp}
                </div>
                <div class="text-4xl font-bold text-white mb-2">
                    {data.close}
                </div>
                <div class="flex gap-3 text-sm font-mono">
                    <span
                        class={data.price_diff >= 0
                            ? "text-green-400"
                            : "text-red-400"}
                    >
                        {data.price_diff > 0 ? "+" : ""}{data.price_diff}
                    </span>
                    <span class="text-zinc-500">Vol: {data.volume_1m}</span>
                </div>

                <div
                    class="mt-4 grid grid-cols-2 gap-y-2 text-sm text-zinc-300"
                >
                    <div class="flex justify-between">
                        <span>Open</span>
                        <span class="font-mono">{data.open}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>High</span>
                        <span class="font-mono">{data.high}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Low</span>
                        <span class="font-mono">{data.low}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Prev</span>
                        <span class="font-mono">{data.prev_close}</span>
                    </div>
                    <div class="flex justify-between text-blue-400">
                        <span>ATP</span>
                        <span class="font-mono">{data.atp}</span>
                    </div>
                </div>
            </div>

            <!-- Greeks -->
            <div
                class="bg-zinc-900 p-5 rounded-xl border border-zinc-800 col-span-1"
            >
                <h3
                    class="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4"
                >
                    Greeks
                </h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-zinc-500">Delta</span>
                        <div class="text-right">
                            <div class="font-mono text-zinc-200">
                                {data.greeks.delta}
                            </div>
                            <div class="text-[10px] text-zinc-600">
                                {data.delta_diff > 0
                                    ? "+"
                                    : ""}{data.delta_diff}
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-zinc-500">Theta</span>
                        <div class="text-right">
                            <div class="font-mono text-zinc-200">
                                {data.greeks.theta}
                            </div>
                            <div class="text-[10px] text-zinc-600">
                                {data.theta_diff > 0
                                    ? "+"
                                    : ""}{data.theta_diff}
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-zinc-500">Gamma</span>
                        <div class="text-right">
                            <div class="font-mono text-zinc-200">
                                {data.greeks.gamma}
                            </div>
                            <div class="text-[10px] text-zinc-600">
                                {data.gamma_diff > 0
                                    ? "+"
                                    : ""}{data.gamma_diff}
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-zinc-500">Vega</span>
                        <div class="text-right">
                            <div class="font-mono text-zinc-200">
                                {data.greeks.vega}
                            </div>
                            <div class="text-[10px] text-zinc-600">
                                {data.vega_diff > 0 ? "+" : ""}{data.vega_diff}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- OI & Vol Stats -->
            <div
                class="bg-zinc-900 p-5 rounded-xl border border-zinc-800 col-span-1"
            >
                <h3
                    class="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4"
                >
                    Market Depth Stats
                </h3>
                <div class="space-y-2 text-sm">
                    <div
                        class="flex justify-between border-b border-zinc-800 pb-2"
                    >
                        <span class="text-zinc-500">OI</span>
                        <span class="font-mono text-zinc-200"
                            >{data.oi.toLocaleString()}
                            <span class="text-[10px] text-zinc-600"
                                >({data.oi_diff})</span
                            ></span
                        >
                    </div>
                    <div
                        class="flex justify-between border-b border-zinc-800 pb-2"
                    >
                        <span class="text-zinc-500">IV</span>
                        <span class="font-mono text-zinc-200"
                            >{data.iv.toFixed(2)}
                            <span class="text-[10px] text-zinc-600"
                                >({data.iv_diff.toFixed(4)})</span
                            ></span
                        >
                    </div>
                    <div
                        class="flex justify-between border-b border-zinc-800 pb-2"
                    >
                        <span class="text-zinc-500">TBQ</span>
                        <span class="font-mono text-green-400"
                            >{data.tbq.toLocaleString()}</span
                        >
                    </div>
                    <div class="flex justify-between pb-2">
                        <span class="text-zinc-500">TSQ</span>
                        <span class="font-mono text-red-400"
                            >{data.tsq.toLocaleString()}</span
                        >
                    </div>
                </div>
            </div>
        </div>

        <!-- Walls Visualizer -->
        <div class="grid grid-cols-2 gap-4">
            <!-- Bids -->
            <div class="bg-zinc-900 p-4 rounded-xl border border-zinc-800">
                <h3 class="text-green-500 font-bold mb-3 text-center">
                    Bid Walls (Support)
                </h3>
                <div class="space-y-1">
                    {#each data.bid_ask.bid_walls as wall}
                        <div
                            class="flex justify-between text-xs bg-green-900/20 px-2 py-1 rounded border border-green-900/30"
                        >
                            <span class="font-mono text-green-100"
                                >{wall.price}</span
                            >
                            <span class="font-mono font-bold text-green-400"
                                >{wall.qty}</span
                            >
                        </div>
                    {/each}
                    {#if data.bid_ask.bid_walls.length === 0}
                        <div class="text-center text-zinc-600 text-xs py-2">
                            No Bid Walls
                        </div>
                    {/if}
                </div>
            </div>

            <!-- Asks -->
            <div class="bg-zinc-900 p-4 rounded-xl border border-zinc-800">
                <h3 class="text-red-500 font-bold mb-3 text-center">
                    Ask Walls (Resist)
                </h3>
                <div class="space-y-1">
                    {#each data.bid_ask.ask_walls as wall}
                        <div
                            class="flex justify-between text-xs bg-red-900/20 px-2 py-1 rounded border border-red-900/30"
                        >
                            <span class="font-mono text-red-100"
                                >{wall.price}</span
                            >
                            <span class="font-mono font-bold text-red-400"
                                >{wall.qty}</span
                            >
                        </div>
                    {/each}
                    {#if data.bid_ask.ask_walls.length === 0}
                        <div class="text-center text-zinc-600 text-xs py-2">
                            No Ask Walls
                        </div>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Raw JSON Dump (Foldable) -->
        <div class="bg-zinc-950 p-4 rounded-xl border border-zinc-800">
            <details>
                <summary class="cursor-pointer text-zinc-500 text-xs font-mono"
                    >View Raw JSON Payload</summary
                >
                <pre
                    class="mt-2 text-[10px] text-zinc-400 overflow-x-auto whitespace-pre-wrap">{JSON.stringify(
                        data,
                        null,
                        2,
                    )}</pre>
            </details>
        </div>
    {:else}
        <div class="text-center py-20 text-zinc-500">
            <p>Waiting for data...</p>
            <p class="text-xs mt-2">
                Make sure to connect and that market is open or data is
                streaming.
            </p>
        </div>
    {/if}
</div>

<style>
    /* Quick utility classes wrapper if tailwind not fully purging for dynamic classes */
    .bg-green-500-20 {
        background-color: rgba(34, 197, 94, 0.2);
    }
    .bg-red-500-20 {
        background-color: rgba(239, 68, 68, 0.2);
    }
    .text-green-500 {
        color: rgb(34, 197, 94);
    }
    .text-red-500 {
        color: rgb(239, 68, 68);
    }
</style>
