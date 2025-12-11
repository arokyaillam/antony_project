import { writable, get } from 'svelte/store';

// --- Types ---

export interface Wall {
    price: number;
    qty: number;
}

export interface BidAskData {
    bid_walls: Wall[];
    ask_walls: Wall[];
    best_bid_price: number;
    best_bid_qty: number;
    best_ask_price: number;
    best_ask_qty: number;
    spread: number;
    total_bid_qty: number;
    total_ask_qty: number;
}

export interface Greeks {
    delta: number;
    theta: number;
    gamma: number;
    vega: number;
    rho: number;
}

export interface CandleDetails {
    instrument_key: string;
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    prev_close: number;
    price_diff: number;

    bid_ask: BidAskData;
    spread_diff: number;

    greeks: Greeks;
    delta_diff: number;
    theta_diff: number;
    gamma_diff: number;
    vega_diff: number;
    rho_diff: number;

    atp: number;
    atp_diff: number;
    vtt: number;
    volume_1m: number;

    oi: number;
    oi_diff: number;

    iv: number;
    iv_diff: number;

    tbq: number;
    tbq_diff: number;
    tsq: number;
    tsq_diff: number;
}

// --- Store ---

// Key: Instrument Key, Value: CandleDetails
export const candleDataStore = writable<Record<string, CandleDetails>>({});

// Helper to update the store
export function updateCandleData(data: CandleDetails) {
    if (data && data.instrument_key) {
        candleDataStore.update(current => {
            return {
                ...current,
                [data.instrument_key]: data
            };
        });
    }
}

// Helper: Get data for a specific instrument
export function getCandleData(key: string): CandleDetails | null {
    const data = get(candleDataStore);
    return data[key] || null;
}
