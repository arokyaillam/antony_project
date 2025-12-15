// Feed Subscription Store - Manage backend subscriptions
// Calls /api/v1/feed/subscribe and /api/v1/feed/unsubscribe

import { writable, get } from 'svelte/store';

import { API_BASE } from '$lib/config';

// Global Connection Status Store
export const isFeedConnected = writable(false);

// Subscriptions Store
export const subscriptionStore = writable<Set<string>>(new Set());

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
            subscriptionStore.update(subs => {
                instrumentKeys.forEach(key => subs.add(key));
                return new Set(subs); // Return new Set to trigger reactivity
            });
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
            subscriptionStore.update(subs => {
                instrumentKeys.forEach(key => subs.delete(key));
                return new Set(subs); // Return new Set to trigger reactivity
            });
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
    return Array.from(get(subscriptionStore));
}

// Sync with backend
export async function syncSubscriptions() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/feed/subscriptions`);
        const data = await res.json();
        const newSubs = new Set<string>(data.subscriptions || []);
        subscriptionStore.set(newSubs);
        return data;
    } catch (err) {
        console.error('Sync failed:', err);
        return { count: 0, subscriptions: [] };
    }
}

// Clear local tracking
export function clearLocalSubscriptions() {
    subscriptionStore.set(new Set());
}
