// Global Candles Stream Store - 1-Minute candle SSE
// Uses /api/v1/stream/candles endpoint
import { writable, get } from 'svelte/store';
import { updateCandleData } from './candleData';

const API_BASE = 'http://localhost:8000';

export const candleStore = writable<any>(null);
// Reactive connection status
export const isCandleConnected = writable(false);

let eventSource: EventSource | null = null;

// Connect to candles SSE stream
export function connectCandleStream(instruments?: string[]) {
    if (eventSource) {
        eventSource.close();
    }

    let url = `${API_BASE}/api/v1/stream/candles`;
    if (instruments && instruments.length > 0) {
        url += `?instruments=${instruments.join(',')}`;
    }

    eventSource = new EventSource(url);

    eventSource.onopen = () => {
        isCandleConnected.set(true);
        console.log('Candle stream connected');
    };

    // Listen for 'candle' events
    eventSource.addEventListener('candle', (event: MessageEvent) => {
        try {
            const data = JSON.parse(event.data);
            candleStore.set(data);

            // Auto-update the structured candle data store
            if (data && data.instrument_key) {
                updateCandleData(data);
            }
        } catch {
            // Skip invalid JSON
        }
    });

    eventSource.onerror = () => {
        isCandleConnected.set(false);
    };
}

// Disconnect
export function disconnectCandleStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isCandleConnected.set(false);
        console.log('Candle stream disconnected');
    }
}

// Subscribe to candle data (Legacy wrapper for backward compatibility)
export function subscribeToCandleStream(callback: (data: any) => void) {
    return candleStore.subscribe((data) => {
        if (data !== null) {
            callback(data);
        }
    });
}

// Status (Legacy accessor)
export function isCandleStreamConnected() {
    return get(isCandleConnected);
}

// Get latest candle
export function getLatestCandle() {
    return get(candleStore);
}
