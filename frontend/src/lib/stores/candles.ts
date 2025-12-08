// Global Candles Stream Store - 1-Minute candle SSE
// Uses /api/v1/stream/candles endpoint

const API_BASE = 'http://localhost:8000';

let eventSource: EventSource | null = null;
let subscribers: Set<(data: any) => void> = new Set();
let currentCandle: any = null;
let isConnected = false;

function notifySubscribers(data: any) {
    currentCandle = data;
    subscribers.forEach(cb => cb(data));
}

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
        isConnected = true;
        console.log('Candle stream connected');
    };

    // Listen for 'candle' events
    eventSource.addEventListener('candle', (event: MessageEvent) => {
        try {
            const data = JSON.parse(event.data);
            notifySubscribers(data);
        } catch {
            // Skip invalid JSON
        }
    });

    eventSource.onerror = () => {
        isConnected = false;
    };
}

// Disconnect
export function disconnectCandleStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        isConnected = false;
        console.log('Candle stream disconnected');
    }
}

// Subscribe to candle data
export function subscribeToCandleStream(callback: (data: any) => void) {
    subscribers.add(callback);
    return () => {
        subscribers.delete(callback);
    };
}

// Status
export function isCandleStreamConnected() {
    return isConnected;
}

// Get latest candle
export function getLatestCandle() {
    return currentCandle;
}
