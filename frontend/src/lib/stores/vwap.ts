import { writable, get } from 'svelte/store';
import { subscriptionStore } from './feed';
import { API_BASE } from '$lib/config';

// --------------------------------------------------------------------------
// Types
// --------------------------------------------------------------------------
export interface VwapData {
    instrument_key: string;
    timestamp: number;
    vwap: number;
    ltp: number;
    volume: number;
}

// --------------------------------------------------------------------------
// Stores
// --------------------------------------------------------------------------
// Holds the latest VWAP data for each instrument: { instrument_key: VwapData }
export const vwapStore = writable<Record<string, VwapData>>({});

// Connection status for the VWAP stream
export const isVwapConnected = writable(false);

// --------------------------------------------------------------------------
// Internal State
// --------------------------------------------------------------------------
let eventSource: EventSource | null = null;
let currentSubscriptions: Set<string> = new Set();

// --------------------------------------------------------------------------
// Functions
// --------------------------------------------------------------------------

/**
 * Connect to the VWAP SSE stream.
 * 
 * @param instruments Optional list of instruments to filter. 
 *                    If not provided, it usually defaults to all (depending on backend).
 *                    However, we typically want to stream what we are subscribed to.
 */
export function connectVwapStream(instruments?: string[]) {
    // Close existing connection if any
    disconnectVwapStream();

    let url = `${API_BASE}/api/v1/stream/vwap`;
    if (instruments && instruments.length > 0) {
        url += `?instruments=${instruments.join(',')}`;
    }

    console.log(`Connecting VWAP Stream: ${url}`);
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
        isVwapConnected.set(true);
        console.log('VWAP stream connected');
    };

    eventSource.onmessage = (event: MessageEvent) => {
        try {
            const data: VwapData = JSON.parse(event.data);

            // Update the store with the new data
            vwapStore.update(store => {
                store[data.instrument_key] = data;
                return store;
            });
        } catch (err) {
            // Ignore keep-alive or malformed data
        }
    };

    eventSource.onerror = () => {
        console.error('VWAP stream error/disconnect');
        isVwapConnected.set(false);
        // EventSource automatically attempts to reconnect, but we update status
    };
}

/**
 * Disconnect the VWAP stream.
 */
export function disconnectVwapStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isVwapConnected.set(false);
        console.log('VWAP stream disconnected');
    }
}

/**
 * Sync VWAP stream with global feed subscriptions.
 * 
 * Logic:
 * 1. Subscribe to `subscriptionStore`.
 * 2. When subscriptions change, reconnect the VWAP stream with the new list of instruments.
 * 3. This ensures we only stream VWAP for what we are interested in.
 */
export function autoSyncVwapWithSubscriptions() {
    subscriptionStore.subscribe(subs => {
        const subList = Array.from(subs);

        // Simple check to avoid reconnecting if the set hasn't effectively changed 
        // (though Set order iteration is insertion order, simple length+content check is good enough)
        // For robustness, we just reconnect if the count > 0.

        if (subList.length > 0) {
            // Debounce re-connection slightly if needed, but for now direct is fine.
            // Check if we are already connected to these exact instruments? 
            // The backend stream endpoint requires query params for filtering.
            // So we MUST reconnect to update the filter on the server side 
            // (unless the backend supports dynamic filter updates via another channel, which it doesn't - it's a GET stream).

            // Reconnect with new list
            connectVwapStream(subList);
        } else {
            disconnectVwapStream();
        }
    });
}
