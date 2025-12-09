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

function createMarketContext() {
    const { subscribe, set, update } = writable<MarketContextState>(initialState);

    return {
        subscribe,
        setContext: (newState: MarketContextState) => set(newState),
        reset: () => set(initialState)
    };
}

export const marketContext = createMarketContext();
