<!-- IndexSelector Component - Select Index & Fetch Option Chain -->
<script lang="ts">
    import {
        subscribeToFeed,
        unsubscribeFromFeed,
        getLocalSubscriptions,
    } from "$lib/stores/feed";

    const API_BASE = "http://localhost:8000";

    // Available indices
    const indices = [
        { key: "NSE_INDEX|Nifty 50", name: "Nifty 50" },
        { key: "NSE_INDEX|Nifty Bank", name: "Nifty Bank" },
    ];

    // State
    let selectedIndex = $state("");
    let expiryDate = $state("");
    let atmStrike = $state(0);
    let isLoading = $state(false);
    let subscribedCount = $state(0);
    let error = $state("");

    // Fetch option chain and subscribe
    async function handleSubscribe() {
        if (!selectedIndex || !expiryDate || !atmStrike) {
            error = "All fields are required!";
            return;
        }

        isLoading = true;
        error = "";

        try {
            // 1. Fetch option chain from backend
            const res = await fetch(
                `${API_BASE}/api/v1/instrument/option-chain`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        instrument_key: selectedIndex,
                        expiry_date: expiryDate,
                        atm_strike: atmStrike,
                    }),
                },
            );

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to fetch option chain");
            }

            const optionChain = await res.json();
            console.log("Option Chain:", optionChain);

            // 2. Extract all instrument keys (CE + PE)
            const instrumentKeys: string[] = [];

            // Add the index itself
            instrumentKeys.push(selectedIndex);

            // Add all option instruments
            for (const option of optionChain.options) {
                if (option.ce_instrument_key) {
                    instrumentKeys.push(option.ce_instrument_key);
                }
                if (option.pe_instrument_key) {
                    instrumentKeys.push(option.pe_instrument_key);
                }
            }

            console.log("Subscribing to instruments:", instrumentKeys);

            // 3. Subscribe via feed API
            const subscribeResult = await subscribeToFeed(
                instrumentKeys,
                "full",
            );

            if (subscribeResult) {
                subscribedCount = instrumentKeys.length;
                console.log(`Subscribed to ${subscribedCount} instruments`);
            } else {
                throw new Error("Subscription failed");
            }
        } catch (err: any) {
            error = err.message || "Unknown error";
            console.error("Error:", err);
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="index-selector">
    <select bind:value={selectedIndex} class="select-index">
        <option value="">Select Index</option>
        {#each indices as idx}
            <option value={idx.key}>{idx.name}</option>
        {/each}
    </select>

    <input
        type="text"
        bind:value={expiryDate}
        placeholder="YYYY-MM-DD"
        class="input-field"
        maxlength="10"
    />

    <input
        type="number"
        bind:value={atmStrike}
        placeholder="ATM Strike"
        class="input-field"
        step="50"
    />

    <button
        onclick={handleSubscribe}
        disabled={isLoading}
        class="btn-subscribe"
    >
        {#if isLoading}
            Loading...
        {:else}
            Subscribe
        {/if}
    </button>

    {#if subscribedCount > 0}
        <span class="badge-count">{subscribedCount}</span>
    {/if}

    {#if error}
        <span class="error-text">{error}</span>
    {/if}
</div>

<style>
    .index-selector {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .select-index {
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 13px;
        cursor: pointer;
    }

    .input-field {
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 13px;
        width: 120px;
    }

    .btn-subscribe {
        padding: 6px 14px;
        border-radius: 6px;
        border: none;
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        color: white;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-subscribe:hover:not(:disabled) {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
    }

    .btn-subscribe:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .badge-count {
        padding: 4px 10px;
        border-radius: 12px;
        background: rgba(0, 210, 106, 0.2);
        color: var(--accent-green);
        font-size: 12px;
        font-weight: 600;
    }

    .error-text {
        color: var(--accent-red, #ef4444);
        font-size: 12px;
    }
</style>
