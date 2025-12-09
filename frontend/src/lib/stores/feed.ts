// Feed Subscription Store - Manage backend subscriptions
// Calls /api/v1/feed/subscribe and /api/v1/feed/unsubscribe

import { writable } from 'svelte/store';

const API_BASE = 'http://localhost:8000';

// Global Connection Status Store
export const isFeedConnected = writable(false);

// Track current subscriptions locally
let subscriptions: Set<string> = new Set();

// Check connection status
export async function checkConnectionStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/status`);
        if (res.ok) {
            const data = await res.json();
            isFeedConnected.set(data.connected);
            return data.connected;
        }
        return false;
    } catch (err) {
        console.error('Status check failed:', err);
        return false;
    }
}

// Subscribe to instruments
export async function subscribeToFeed(instrumentKeys: string[], mode: 'full' | 'ltpc' | 'full_d30' = 'full') {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instrument_keys: instrumentKeys, mode })
        });

        if (res.ok) {
            instrumentKeys.forEach(key => subscriptions.add(key));
            console.log('Subscribed:', instrumentKeys);
            // If subscription succeeds, it implies connected (or auto-connected)
            checkConnectionStatus();
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
