// Feed Subscription Store - Manage backend subscriptions
// Calls /api/v1/feed/subscribe and /api/v1/feed/unsubscribe

const API_BASE = 'http://localhost:8000';

// Track current subscriptions locally
let subscriptions: Set<string> = new Set();

// Subscribe to instruments
export async function subscribeToFeed(instrumentKeys: string[], mode: 'full' | 'ltpc' = 'full') {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instrument_keys: instrumentKeys, mode })
        });

        if (res.ok) {
            instrumentKeys.forEach(key => subscriptions.add(key));
            console.log('Subscribed:', instrumentKeys);
        }

        return res.ok;
    } catch (err) {
        console.error('Subscribe failed:', err);
        return false;
    }
}

// Unsubscribe from instruments
export async function unsubscribeFromFeed(instrumentKeys: string[]) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/unsubscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instrument_keys: instrumentKeys, mode: 'full' })
        });

        if (res.ok) {
            instrumentKeys.forEach(key => subscriptions.delete(key));
            console.log('Unsubscribed:', instrumentKeys);
        }

        return res.ok;
    } catch (err) {
        console.error('Unsubscribe failed:', err);
        return false;
    }
}

// Get current local subscriptions
export function getLocalSubscriptions(): string[] {
    return Array.from(subscriptions);
}

// Sync with backend
export async function syncSubscriptions() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/subscriptions`);
        const data = await res.json();
        subscriptions = new Set(data.subscriptions || []);
        return data;
    } catch (err) {
        console.error('Sync failed:', err);
        return { count: 0, subscriptions: [] };
    }
}

// Clear local tracking
export function clearLocalSubscriptions() {
    subscriptions.clear();
}
