import { writable, get } from 'svelte/store';

const API_BASE = "http://localhost:8000";

export interface LiveQuote {
    timestamp: number;
    ltp: number;
    change: number;
    changePercent: number;
    open: number;
    high: number;
    low: number;
    close: number; // Previous Close
    lastTradedTime: number;
}

// Global Store: Key -> LiveQuote
export const liveFeedStore = writable<Record<string, LiveQuote>>({});

let eventSource: EventSource | null = null;
let activeKeys: Set<string> = new Set();
let reconnectTimer: any = null;

// Add instruments to the live stream
export function monitorInstruments(keys: string[]) {
    let changed = false;
    keys.forEach(k => {
        if (!activeKeys.has(k)) {
            activeKeys.add(k);
            changed = true;
        }
    });

    if (changed) {
        restartStream();
    }
}

function restartStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }

    if (activeKeys.size === 0) return;

    // Convert Set to comma-separated string
    const keysParam = Array.from(activeKeys).join(',');
    const url = `${API_BASE}/api/v1/stream/live?instruments=${encodeURIComponent(keysParam)}`;

    console.log("Connecting Live Stream for:", Array.from(activeKeys));

    eventSource = new EventSource(url);

    eventSource.onopen = () => {
        console.log("Live Feed Connected");
    };

    eventSource.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            processPayload(payload);
        } catch (e) {
            // Ignore keep-alive
        }
    };

    eventSource.onerror = (err) => {
        console.error("Live Feed Error", err);
        eventSource?.close();
        // Retry logic
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(() => restartStream(), 5000);
    };
}

function processPayload(data: any) {
    if (!data?.feeds) return;

    liveFeedStore.update(current => {
        const next = { ...current };
        let hasUpdates = false;

        Object.keys(data.feeds).forEach(key => {
            const feed = data.feeds[key];
            const ff = feed.fullFeed?.indexFF || feed.fullFeed?.marketFF;
            if (!ff) return;

            const ltpc = ff.ltpc;
            const ohlc = ff.marketOHLC?.ohlc?.[0]; // Today's OHLC

            // Get existing or init new
            const existing = next[key] || {
                timestamp: Date.now(),
                ltp: 0, change: 0, changePercent: 0,
                open: 0, high: 0, low: 0, close: 0,
                lastTradedTime: 0
            };

            // Update LTPC
            if (ltpc) {
                if (ltpc.ltp) existing.ltp = ltpc.ltp;
                if (ltpc.cp) existing.close = ltpc.cp; // Previous Close
                if (ltpc.ltt) existing.lastTradedTime = Number(ltpc.ltt);
            }

            // Calculate Change (Live)
            if (existing.ltp && existing.close) {
                existing.change = existing.ltp - existing.close;
                existing.changePercent = (existing.change / existing.close) * 100;
            }

            // Update OHLC
            if (ohlc) {
                if (ohlc.open) existing.open = ohlc.open;
                if (ohlc.high) existing.high = ohlc.high;
                if (ohlc.low) existing.low = ohlc.low;
                if (ohlc.close) existing.close = ohlc.close; // Some feeds send PC inside OHLC
            }

            existing.timestamp = Date.now();
            next[key] = existing;
            hasUpdates = true;
        });

        return hasUpdates ? next : current;
    });
}
