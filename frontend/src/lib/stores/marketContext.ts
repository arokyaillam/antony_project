import { writable } from 'svelte/store';

export type InstrumentType = 'CE' | 'PE' | 'FUT' | 'INDEX';

export interface InstrumentMeta {
    strike: number;
    type: InstrumentType;
    key: string;
    symbol: string; // e.g. "NIFTY23DEC18000CE"
}

export interface MarketContextState {
    indexKey: string;       // e.g. "NSE_INDEX|Nifty 50"
    expiry: string;         // e.g. "2025-01-25"
    atmStrike: number;
    // Map of InstrumentKey -> Metadata
    instruments: Record<string, InstrumentMeta>;
    // Grouped by strike for easy table rendering
    chain: Record<number, { CE?: string, PE?: string }>;
}

const initialState: MarketContextState = {
    indexKey: "",
    expiry: "",
    atmStrike: 0,
    instruments: {},
    chain: {}
};

import { browser } from '$app/environment';

const STORAGE_KEY = 'market_context_v1';

function createMarketContext() {
    // 1. Recover from localStorage if available
    let startState = initialState;
    if (browser) {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                startState = JSON.parse(stored);
            }
        } catch (e) {
            console.warn("Failed to load market context", e);
        }
    }

    const { subscribe, set, update } = writable<MarketContextState>(startState);

    // 2. Persist on change
    if (browser) {
        subscribe((value) => {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
            } catch (e) {
                console.warn("Failed to save market context", e);
            }
        });
    }

    return {
        subscribe,
        setContext: (newState: MarketContextState) => set(newState),
        reset: () => set(initialState)
    };
}

export const marketContext = createMarketContext();
