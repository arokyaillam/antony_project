// Portfolio Store - Funds, Positions, Holdings
const API_BASE = 'http://localhost:8000';

// Get Funds
export async function getFunds(segment: 'SEC' | 'COM' = 'SEC') {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/funds?segment=${segment}`);
        return await res.json();
    } catch (err) {
        console.error('getFunds failed:', err);
        return null;
    }
}

// Get Positions
export async function getPositions() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/positions`);
        return await res.json();
    } catch (err) {
        console.error('getPositions failed:', err);
        return null;
    }
}

// Get Holdings
export async function getHoldings() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/holdings`);
        return await res.json();
    } catch (err) {
        console.error('getHoldings failed:', err);
        return null;
    }
}

// Get Trades
export async function getTrades() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/trades`);
        return await res.json();
    } catch (err) {
        console.error('getTrades failed:', err);
        return null;
    }
}

// Get Order Book
export async function getOrderBook() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/orders`);
        return await res.json();
    } catch (err) {
        console.error('getOrderBook failed:', err);
        return null;
    }
}

// Get Order Details
export async function getOrderDetails(orderId: string) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/portfolio/orders/${orderId}`);
        return await res.json();
    } catch (err) {
        console.error('getOrderDetails failed:', err);
        return null;
    }
}
