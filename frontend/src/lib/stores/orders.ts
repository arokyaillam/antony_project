// Global Orders Stream Store - Order updates SSE
// Uses /api/v1/stream/orders endpoint

const API_BASE = 'http://localhost:8000';

let eventSource: EventSource | null = null;
let subscribers: Set<(data: any) => void> = new Set();
let latestOrder: any = null;
let isConnected = false;

function notifySubscribers(data: any) {
    latestOrder = data;
    subscribers.forEach(cb => cb(data));
}

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
            notifySubscribers(data);
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

// Subscribe
export function subscribeToOrderStream(callback: (data: any) => void) {
    subscribers.add(callback);
    return () => {
        subscribers.delete(callback);
    };
}

// Status
export function isOrderStreamConnected() {
    return isConnected;
}

// Get latest
export function getLatestOrder() {
    return latestOrder;
}
