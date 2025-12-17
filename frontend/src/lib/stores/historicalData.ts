import { writable, get } from 'svelte/store';
import { API_BASE } from '$lib/config';

// --- Types ---

export interface HistoricalCandle {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    oi?: number;
}

export interface HistoryState {
    [instrumentKey: string]: {
        [interval: string]: HistoricalCandle[];
    };
}

// --- Store ---

// Key: Instrument Key -> Interval -> List of Candles
export const historicalDataStore = writable<HistoryState>({});

// --- Actions ---

export async function fetchHistory(
    instrumentKey: string,
    interval: string,
    fromDate: string,
    toDate: string
) {
    try {
        const url = new URL(`${API_BASE}/api/v1/history/candles`);
        url.searchParams.append('instrument_key', instrumentKey);
        url.searchParams.append('interval', interval);
        url.searchParams.append('from_date', fromDate);
        url.searchParams.append('to_date', toDate);

        const response = await fetch(url.toString());

        if (!response.ok) {
            throw new Error(`History fetch failed: ${response.statusText}`);
        }

        const data = await response.json();
        const candles = data?.data?.candles || data?.candles || data || [];

        // Upstox API format mapping if needed
        // Assuming the API returns [ [timestamp, open, high, low, close, vol, oi], ... ]
        // OR objects. Let's assume the API returns objects or we need to parse.
        // Based on Python service, it returns whatever Upstox SDK returns.
        // Standard Upstox Hist API returns: 
        // { status: "success", data: { candles: [ [ts, o, h, l, c, v, oi], ... ] } }

        // Let's handle the array format explicitly used by Upstox
        const mappedCandles: HistoricalCandle[] = Array.isArray(candles) ? candles.map((c: any) => {
            if (Array.isArray(c)) {
                return {
                    timestamp: c[0],
                    open: Number(c[1]),
                    high: Number(c[2]),
                    low: Number(c[3]),
                    close: Number(c[4]),
                    volume: Number(c[5]),
                    oi: c[6] ? Number(c[6]) : 0
                };
            }
            return c; // Already an object?
        }) : [];

        historicalDataStore.update(store => {
            const instrumentData = store[instrumentKey] || {};
            return {
                ...store,
                [instrumentKey]: {
                    ...instrumentData,
                    [interval]: mappedCandles
                }
            };
        });

        return mappedCandles;
    } catch (error) {
        console.error("Error fetching history:", error);
        return [];
    }
}

// Helper to get data
export function getHistory(key: string, interval: string): HistoricalCandle[] {
    const store = get(historicalDataStore);
    return store[key]?.[interval] || [];
}
