<!-- Upstox Feed Connect - Connect + Subscribe -->
<script lang="ts">
    import { onMount } from "svelte";
    import { checkConnectionStatus, isFeedConnected } from "$lib/stores/feed";

    import { API_BASE } from "$lib/config";

    // Default index keys to subscribe
    const DEFAULT_KEYS = [
        "NSE_INDEX|Nifty 50",
        "NSE_INDEX|Nifty Bank",
        "NSE_INDEX|India VIX",
    ];

    let feedStatus = $state<
        "disconnected" | "connecting" | "connected" | "error"
    >("disconnected");
    let statusMessage = $state("Feed not connected");
    let subscriptions = $state<string[]>([]);
    let isSubscribing = $state(false);

    // Check health on mount
    let backendOk = $state(false);
    let tokenOk = $state(false);

    onMount(async () => {
        await checkBackendHealth();
        await checkTokenStatus();

        // Initial Connection Check
        const connected = await checkConnectionStatus();
        if (connected) {
            feedStatus = "connected";
            statusMessage = "WebSocket already connected (Persistent) ✅";
            // Auto-start streams if UI reconnects
            startAllStreams();
        }
    });

    // Reactive: If global store updates (e.g. from another tab/component), update local state
    $effect(() => {
        if ($isFeedConnected && feedStatus !== "connected") {
            feedStatus = "connected";
            statusMessage = "WebSocket synced from store ✅";
            if (!liveEventSource) {
                startAllStreams();
            }
        } else if (!$isFeedConnected && feedStatus === "connected") {
            feedStatus = "disconnected";
            statusMessage = "Disconnected (Synced)";
            stopAllStreams();
        }
    });

    async function checkBackendHealth() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            const data = await res.json();
            backendOk = data.redis === "up" && data.postgres === "up";
        } catch {
            backendOk = false;
        }
    }

    async function checkTokenStatus() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/portfolio/funds`);
            tokenOk = res.ok;
        } catch {
            tokenOk = false;
        }
    }

    // SSE Stream connections
    let liveEventSource: EventSource | null = null;
    let candleEventSource: EventSource | null = null;
    let orderEventSource: EventSource | null = null;

    // Stream status
    let liveStream = $state(false);
    let candleStream = $state(false);
    let orderStream = $state(false);

    function startAllStreams() {
        // Prevent duplicate streams
        if (liveEventSource) return;

        // Start Live Stream
        liveEventSource = new EventSource(`${API_BASE}/api/v1/stream/live`);
        liveEventSource.onopen = () => {
            liveStream = true;
        };
        liveEventSource.onerror = () => {
            liveStream = false;
            // Optional: retry logic?
        };

        // Start Candle Stream
        candleEventSource = new EventSource(
            `${API_BASE}/api/v1/stream/candles`,
        );
        candleEventSource.onopen = () => {
            candleStream = true;
        };
        candleEventSource.onerror = () => {
            candleStream = false;
        };

        // Start Order Stream
        orderEventSource = new EventSource(`${API_BASE}/api/v1/stream/orders`);
        orderEventSource.onopen = () => {
            orderStream = true;
        };
        orderEventSource.onerror = () => {
            orderStream = false;
        };
    }

    function stopAllStreams() {
        if (liveEventSource) {
            liveEventSource.close();
            liveEventSource = null;
        }
        if (candleEventSource) {
            candleEventSource.close();
            candleEventSource = null;
        }
        if (orderEventSource) {
            orderEventSource.close();
            orderEventSource = null;
        }
        liveStream = false;
        candleStream = false;
        orderStream = false;
    }

    async function connectFeed() {
        feedStatus = "connecting";
        statusMessage = "Connecting WebSocket + Streams...";

        try {
            // Step 1: Connect WebSocket
            const res = await fetch(`${API_BASE}/api/v1/feed/connect`, {
                method: "POST",
            });
            const data = await res.json();

            if (res.ok) {
                // Update Global Store
                isFeedConnected.set(true);

                feedStatus = "connected";
                statusMessage = "WebSocket connected! Starting streams...";

                // Step 2: Auto-start all SSE streams
                startAllStreams();
                statusMessage = "All streams connected! ✅";
            } else {
                feedStatus = "error";
                statusMessage = data.detail || "Failed to connect";
            }
        } catch (err) {
            feedStatus = "error";
            statusMessage = `Error: ${err}`;
        }
    }

    async function disconnectFeed() {
        try {
            // Stop all SSE streams first
            stopAllStreams();

            const res = await fetch(`${API_BASE}/api/v1/feed/disconnect`, {
                method: "POST",
            });
            const data = await res.json();

            // Update store
            isFeedConnected.set(false);

            feedStatus = "disconnected";
            statusMessage = data.message || "Disconnected";
            subscriptions = [];
        } catch (err) {
            feedStatus = "error";
            statusMessage = `Error: ${err}`;
        }
    }

    async function subscribeToDefaultKeys() {
        isSubscribing = true;
        try {
            const res = await fetch(`${API_BASE}/api/v1/feed/subscribe`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    instrument_keys: DEFAULT_KEYS,
                    mode: "full",
                }),
            });
            const data = await res.json();

            if (res.ok) {
                subscriptions = DEFAULT_KEYS;
                statusMessage = `Subscribed to ${DEFAULT_KEYS.length} instruments ✅`;
            } else {
                statusMessage = data.detail || "Subscribe failed";
            }
        } catch (err) {
            statusMessage = `Error: ${err}`;
        } finally {
            isSubscribing = false;
        }
    }
</script>

<div class="connect-page">
    <h1>📡 Upstox Feed Connect</h1>

    <!-- Prerequisites -->
    <div class="prereq">
        <div class="prereq-item" class:ok={backendOk}>
            {backendOk ? "✅" : "❌"} Backend
        </div>
        <div class="prereq-item" class:ok={tokenOk}>
            {tokenOk ? "✅" : "❌"} Token
        </div>
        {#if !tokenOk}
            <a href="/auth/refresh">🔄 Get Token</a>
        {/if}
    </div>

    <!-- Status -->
    <div class="status-card">
        <div class="status">
            {#if feedStatus === "connected"}🟢 Connected
            {:else if feedStatus === "connecting"}🟡 Connecting...
            {:else if feedStatus === "error"}🔴 Error
            {:else}⚫ Disconnected{/if}
        </div>
        <p>{statusMessage}</p>
    </div>

    <!-- Buttons -->
    <div class="buttons">
        {#if feedStatus === "connected"}
            <button class="btn-stop" onclick={disconnectFeed}
                >⏹️ Disconnect</button
            >
        {:else}
            <button
                class="btn-start"
                onclick={connectFeed}
                disabled={feedStatus === "connecting" || !backendOk || !tokenOk}
            >
                ▶️ Connect
            </button>
        {/if}
    </div>

    <!-- Stream Status (auto-connected when feed connects) -->
    {#if feedStatus === "connected"}
        <div class="streams-section">
            <h3>📡 Stream Status</h3>
            <div class="stream-status">
                <span class="stream-indicator" class:active={liveStream}>
                    📊 Live {liveStream ? "✓" : "⏳"}
                </span>
                <span class="stream-indicator" class:active={candleStream}>
                    📈 Candle {candleStream ? "✓" : "⏳"}
                </span>
                <span class="stream-indicator" class:active={orderStream}>
                    📋 Order {orderStream ? "✓" : "⏳"}
                </span>
            </div>
        </div>

        <!-- Subscribe (show after connected) -->
        {#if subscriptions.length === 0}
            <div class="subscribe-section">
                <button
                    class="btn-subscribe"
                    onclick={subscribeToDefaultKeys}
                    disabled={isSubscribing}
                >
                    {isSubscribing
                        ? "⏳ Subscribing..."
                        : "📊 Subscribe to Index"}
                </button>
            </div>
        {/if}
    {/if}

    <!-- Subscriptions List -->
    {#if subscriptions.length > 0}
        <div class="subscriptions-card">
            <h3>📊 Active Subscriptions ({subscriptions.length})</h3>
            <ul>
                {#each subscriptions as key}
                    <li>{key}</li>
                {/each}
            </ul>
        </div>
    {/if}
</div>

<style>
    .connect-page {
        max-width: 400px;
        margin: 0 auto;
        text-align: center;
    }

    h1 {
        font-size: 24px;
        margin-bottom: 24px;
    }

    .prereq {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 24px;
    }

    .prereq-item {
        padding: 8px 16px;
        background: var(--bg-card);
        border-radius: 8px;
        font-size: 14px;
        color: var(--text-secondary);
    }

    .prereq-item.ok {
        color: var(--text-primary);
    }

    .prereq a {
        font-size: 13px;
        color: var(--accent-blue);
    }

    .status-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
    }

    .status {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .status-card p {
        color: var(--text-secondary);
        font-size: 14px;
    }

    .buttons {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-bottom: 24px;
    }

    .btn-start,
    .btn-stop,
    .btn-subscribe {
        padding: 14px 32px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        border: none;
    }

    .btn-start {
        background: linear-gradient(135deg, var(--accent-green), #00a854);
        color: white;
    }

    .btn-start:disabled {
        background: var(--bg-hover);
        color: var(--text-muted);
        cursor: not-allowed;
    }

    .btn-stop {
        background: linear-gradient(135deg, var(--accent-red), #cc3a47);
        color: white;
    }

    .btn-subscribe {
        background: linear-gradient(135deg, var(--accent-blue), #1976d2);
        color: white;
    }

    .btn-subscribe:disabled {
        background: var(--bg-hover);
        color: var(--text-muted);
        cursor: not-allowed;
    }

    .subscriptions-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        text-align: left;
    }

    .subscriptions-card h3 {
        font-size: 14px;
        margin-bottom: 12px;
        color: var(--text-secondary);
    }

    .subscriptions-card ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .subscriptions-card li {
        padding: 8px 12px;
        background: var(--bg-hover);
        border-radius: 6px;
        font-size: 13px;
        margin-bottom: 6px;
        font-family: monospace;
    }

    /* Stream connection buttons */
    .streams-section {
        margin: 24px 0;
        padding: 20px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }

    .streams-section h3 {
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 16px;
    }

    .stream-status {
        display: flex;
        gap: 12px;
        justify-content: center;
    }

    .stream-indicator {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 13px;
        background: var(--bg-hover);
        color: var(--text-secondary);
    }

    .stream-indicator.active {
        background: rgba(0, 200, 83, 0.1);
        color: var(--accent-green);
    }

    .subscribe-section {
        margin-top: 20px;
    }
</style>
