// Global Stream Store - SSE connection to backend
// Any component can import and use this store

const API_BASE = 'http://localhost:8000';

// Store state
let eventSource: EventSource | null = null;
let subscribers: Set<(data: any) => void> = new Set();
let currentData: any = null;
let isConnected = false;

// Subscribe callback function
function notifySubscribers(data: any) {
    currentData = data;
    subscribers.forEach(cb => cb(data));
}

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
        isConnected = true;
        console.log('Stream connected');
    };

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            notifySubscribers(data);
        } catch {
            // Skip invalid JSON
        }
    };

    eventSource.onerror = () => {
        isConnected = false;
    };
}

// Disconnect stream
export function disconnectStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isConnected = false;
        console.log('Stream disconnected');
    }
}

// Subscribe to stream data
export function subscribeToStream(callback: (data: any) => void) {
    subscribers.add(callback);

    // Return unsubscribe function
    return () => {
        subscribers.delete(callback);
    };
}

// Get current connection status
export function isStreamConnected() {
    return isConnected;
}

// Get latest data
export function getLatestData() {
    return currentData;
}
