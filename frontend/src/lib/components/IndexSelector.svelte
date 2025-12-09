<!-- IndexSelector Component - Select Index & Fetch Option Chain -->
<script lang="ts">
    import {
        subscribeToFeed,
        unsubscribeFromFeed,
        getLocalSubscriptions,
    } from "$lib/stores/feed";
    import { connectStream, isStreamConnected } from "$lib/stores/stream";
    import {
        connectCandleStream,
        isCandleStreamConnected,
    } from "$lib/stores/candles";
    import {
        marketContext,
        type MarketContextState,
        type InstrumentMeta,
    } from "$lib/stores/marketContext";

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

            // 2. Build Market Context
            const newContext: MarketContextState = {
                indexKey: selectedIndex,
                expiry: expiryDate,
                atmStrike: atmStrike,
                instruments: {},
                chain: {},
            };

            const instrumentKeys: string[] = [];
            instrumentKeys.push(selectedIndex); // Add index itself

            // Process Options
            for (const option of optionChain.options) {
                const strike = option.strike_price;

                // Ensure chain entry exists
                if (!newContext.chain[strike]) {
                    newContext.chain[strike] = {};
                }

                // Add CE
                if (option.ce_instrument_key) {
                    newContext.instruments[option.ce_instrument_key] = {
                        strike: strike,
                        type: "CE",
                        key: option.ce_instrument_key,
                        symbol: `CE ${strike}`, // Placeholder symbol
                    };
                    newContext.chain[strike].CE = option.ce_instrument_key;
                    instrumentKeys.push(option.ce_instrument_key);
                }

                // Add PE
                if (option.pe_instrument_key) {
                    newContext.instruments[option.pe_instrument_key] = {
                        strike: strike,
                        type: "PE",
                        key: option.pe_instrument_key,
                        symbol: `PE ${strike}`, // Placeholder symbol
                    };
                    newContext.chain[strike].PE = option.pe_instrument_key;
                    instrumentKeys.push(option.pe_instrument_key);
                }
            }

            // 3. Update Global Context
            marketContext.setContext(newContext);
            console.log("Market Context Updated:", newContext);

            // --- LOGIC MOVED UP: Select 5 strikes closest to ATM (10 instruments) ---
            const allStrikes = Object.keys(newContext.chain)
                .map(Number)
                .sort((a, b) => a - b);

            // Find index of ATM or closest strike
            let atmIndex = allStrikes.indexOf(atmStrike);

            // If exact ATM not found, find closest
            if (atmIndex === -1) {
                let minDiff = Infinity;
                allStrikes.forEach((s, i) => {
                    const diff = Math.abs(s - atmStrike);
                    if (diff < minDiff) {
                        minDiff = diff;
                        atmIndex = i;
                    }
                });
            }

            // Select range: -2 to +2 around ATM (5 strikes total)
            const start = Math.max(0, atmIndex - 2);
            const end = Math.min(allStrikes.length, start + 5);
            const targetStrikes = allStrikes.slice(start, end);

            // Identify the 10 focused keys (Candle Keys) using a Set for easy lookup
            const candleKeySet = new Set<string>();
            const candleKeys: string[] = [];

            targetStrikes.forEach((strike) => {
                const c = newContext.chain[strike];
                if (c.CE) {
                    candleKeys.push(c.CE);
                    candleKeySet.add(c.CE);
                }
                if (c.PE) {
                    candleKeys.push(c.PE);
                    candleKeySet.add(c.PE);
                }
            });

            // Identify remaining keys (Regular Keys)
            const regularKeys = instrumentKeys.filter(
                (k) => !candleKeySet.has(k),
            );

            console.log(`Focused Keys (full_d30): ${candleKeys.length}`);
            console.log(`Regular Keys (full): ${regularKeys.length}`);

            // 4. Subscribe via feed API (Split Batches)
            // Batch A: The 10 Focused Keys -> full_d30
            const sub1 = await subscribeToFeed(candleKeys, "full_d30");

            // Batch B: The Rest -> full
            const sub2 = await subscribeToFeed(regularKeys, "full");

            // Combined success check
            if (sub1 && sub2) {
                subscribedCount = instrumentKeys.length;
                console.log(
                    `Subscribed to ${subscribedCount} instruments total`,
                );

                // 5. Connect Streams
                console.log("Connecting to Live and Candle Streams...");

                // A. Live Market Stream (Connect ALL)
                connectStream(instrumentKeys);

                // B. Candle Stream (Limit to 5 Strikes = 10 Instruments)
                console.log(
                    `Candle Stream restricted to ${candleKeys.length} instruments`,
                );
                connectCandleStream(candleKeys);
            } else {
                throw new Error("Subscription failed (Partial or Complete)");
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
