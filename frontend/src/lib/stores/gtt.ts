// GTT Store - Good Till Triggered orders
const API_BASE = 'http://localhost:8000';

export type GTTType = 'SINGLE' | 'MULTIPLE';
export type TriggerType = 'ABOVE' | 'BELOW' | 'IMMEDIATE';
export type Strategy = 'ENTRY' | 'TARGET' | 'STOPLOSS';

export interface GTTRule {
    strategy: Strategy;
    trigger_type: TriggerType;
    trigger_price: number;
    trailing_gap?: number;
}

export interface GTTPlaceRequest {
    type: GTTType;
    quantity: number;
    product: 'I' | 'D';
    instrument_token: string;
    transaction_type: 'BUY' | 'SELL';
    rules: GTTRule[];
}

export interface GTTModifyRequest {
    gtt_order_id: string;
    type?: GTTType;
    quantity?: number;
    rules?: GTTRule[];
}

// Place GTT Order
export async function placeGTT(request: GTTPlaceRequest) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/gtt/place`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return await res.json();
    } catch (err) {
        console.error('placeGTT failed:', err);
        return { error: String(err) };
    }
}

// Modify GTT Order
export async function modifyGTT(request: GTTModifyRequest) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/gtt/modify`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return await res.json();
    } catch (err) {
        console.error('modifyGTT failed:', err);
        return { error: String(err) };
    }
}

// Cancel GTT Order
export async function cancelGTT(gttOrderId: string) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/gtt/cancel`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gtt_order_id: gttOrderId })
        });
        return await res.json();
    } catch (err) {
        console.error('cancelGTT failed:', err);
        return { error: String(err) };
    }
}

// Get GTT Order Details
export async function getGTT(gttOrderId: string) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/gtt/${gttOrderId}`);
        return await res.json();
    } catch (err) {
        console.error('getGTT failed:', err);
        return null;
    }
}

// Get All GTT Orders
export async function getAllGTT() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/gtt/`);
        return await res.json();
    } catch (err) {
        console.error('getAllGTT failed:', err);
        return [];
    }
}
