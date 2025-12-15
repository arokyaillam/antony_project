// Global Stream Store - SSE connection to backend
// Any component can import and use this store
import { writable, get } from 'svelte/store';
import { updateMarketData } from './marketData';

import { API_BASE } from '$lib/config';

// Store state
export const streamStore = writable<any>(null);
// Connection status store
export const isStreamActive = writable(false);

let eventSource: EventSource | null = null;
let isConnected = false; // Keep local for internal checks if needed, but rely on store

// Connect to SSE stream with optional instrument filter
export function connectStream(instruments?: string[]) {
    if (eventSource) {
        eventSource.close();
    }

    let url = `${API_BASE}/api/v1/stream/live`;
    if (instruments && instruments.length > 0) {
        url += `?instruments=${instruments.join(',')}`;
    }

    eventSource = new EventSource(url);

    eventSource.onopen = () => {
        isStreamActive.set(true);
        console.log('Stream connected');
    };

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            streamStore.set(data);

            // Auto-update the structured market data store
            if (data && data.type === 'live_feed') {
                updateMarketData(data);
            }
        } catch {
            // Skip invalid JSON
        }
    };

    eventSource.onerror = () => {
        isStreamActive.set(false);
    };
}

// Disconnect stream
export function disconnectStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isStreamActive.set(false);
        console.log('Stream disconnected');
    }
}

// Subscribe to stream data (Legacy wrapper)
export function subscribeToStream(callback: (data: any) => void) {
    return streamStore.subscribe((data) => {
        if (data !== null) {
            callback(data);
        }
    });
}

// Get current connection status (Legacy accessor)
export function isStreamConnected() {
    return get(isStreamActive);
}

// Get latest data
export function getLatestData() {
    return get(streamStore);
}
