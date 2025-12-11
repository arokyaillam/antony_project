// Global Orders Stream Store - Order updates SSE
// Uses /api/v1/stream/orders endpoint
import { writable, get } from 'svelte/store';

const API_BASE = 'http://localhost:8000';

export const orderStore = writable<any>(null);

let eventSource: EventSource | null = null;
let isConnected = false;

// Connect to orders SSE stream
export function connectOrderStream() {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`${API_BASE}/api/v1/stream/orders`);

    eventSource.onopen = () => {
        isConnected = true;
        console.log('Order stream connected');
    };

    // Listen for 'order' events
    eventSource.addEventListener('order', (event: MessageEvent) => {
        try {
            const data = JSON.parse(event.data);
            orderStore.set(data);
        } catch {
            // Skip
        }
    });

    eventSource.onerror = () => {
        isConnected = false;
    };
}

// Disconnect
export function disconnectOrderStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isConnected = false;
        console.log('Order stream disconnected');
    }
}

// Subscribe (Legacy wrapper)
export function subscribeToOrderStream(callback: (data: any) => void) {
    return orderStore.subscribe((data) => {
        if (data !== null) {
            callback(data);
        }
    });
}

// Status
export function isOrderStreamConnected() {
    return isConnected;
}

// Get latest
export function getLatestOrder() {
    return get(orderStore);
}
