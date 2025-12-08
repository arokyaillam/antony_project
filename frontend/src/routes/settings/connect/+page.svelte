<!-- Upstox Feed Connect - Simple connect/disconnect only -->
<script lang="ts">
    import { onMount } from "svelte";

    const API_BASE = "http://localhost:8000";

    let feedStatus = $state<
        "disconnected" | "connecting" | "connected" | "error"
    >("disconnected");
    let statusMessage = $state("Feed not connected");

    // Check health on mount
    let backendOk = $state(false);
    let tokenOk = $state(false);

    onMount(async () => {
        await checkBackendHealth();
        await checkTokenStatus();
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

    async function connectFeed() {
        feedStatus = "connecting";
        statusMessage = "Connecting...";

        try {
            const res = await fetch(`${API_BASE}/api/v1/feed/connect`, {
                method: "POST",
            });
            const data = await res.json();

            if (res.ok) {
                feedStatus = "connected";
                statusMessage = data.message || "Connected!";
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
            const res = await fetch(`${API_BASE}/api/v1/feed/disconnect`, {
                method: "POST",
            });
            const data = await res.json();
            feedStatus = "disconnected";
            statusMessage = data.message || "Disconnected";
        } catch (err) {
            feedStatus = "error";
            statusMessage = `Error: ${err}`;
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
        justify-content: center;
    }

    .btn-start,
    .btn-stop {
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
</style>
