import { writable, get } from 'svelte/store';

// --- Types ---

export interface LTPC {
    ltp: number;
    ltt: string;
    ltq: string;
    cp: number;
}

export interface BidAskQuote {
    bidQ: string;
    bidP: number;
    askQ: string;
    askP: number;
}

export interface OptionGreeks {
    delta: number;
    theta: number;
    gamma: number;
    vega: number;
    rho: number;
}

export interface OHLC {
    interval: string;
    open: number;
    high: number;
    low: number;
    close: number;
    vol: string;
    ts: string;
}

export interface MarketOHLC {
    ohlc: OHLC[];
}

export interface MarketLevel {
    bidAskQuote: BidAskQuote[];
    optionGreeks?: OptionGreeks; // Optional as not all instruments have greeks
}

export interface MarketFF {
    ltpc: LTPC;
    marketLevel: MarketLevel;
    marketOHLC: MarketOHLC;
    atp: number;
    vtt: string;
    oi: number;
    iv: number;
    tbq: number;
    tsq: number;
}

export interface FullFeed {
    marketFF: MarketFF;
}

export interface InstrumentFeed {
    fullFeed: FullFeed;
    requestMode: string;
}

export interface LiveFeedData {
    type: string;
    feeds: Record<string, InstrumentFeed>;
    currentTs: string;
}

// --- Store ---

// Primary store holding the entire map of properties for all instruments
// Key: Instrument Key (e.g., "NSE_FO|41880"), Value: InstrumentFeed
export const marketDataStore = writable<Record<string, InstrumentFeed>>({});

// Helper to update the store from the socket response
export function updateMarketData(data: LiveFeedData) {
    if (data.type === 'live_feed' && data.feeds) {
        marketDataStore.update(current => {
            // Merge new feeds into the existing state
            // This ensures we don't lose data for instruments not in the current packet
            return {
                ...current,
                ...data.feeds
            };
        });
    }
}

// Helper: Get data for a specific instrument safely
export function getInstrumentData(key: string): InstrumentFeed | null {
    const data = get(marketDataStore);
    return data[key] || null;
}

// Helper: Get LTP for a specific instrument
export function getLTP(key: string): number {
    const data = get(marketDataStore);
    return data[key]?.fullFeed?.marketFF?.ltpc?.ltp || 0;
}
