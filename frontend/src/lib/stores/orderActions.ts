// Order Actions Store - Place, Modify, Cancel orders
const API_BASE = 'http://localhost:8000';

export type OrderType = 'MARKET' | 'LIMIT' | 'SL' | 'SL-M';
export type TransactionType = 'BUY' | 'SELL';
export type ProductType = 'I' | 'D' | 'CO' | 'MTF'; // Intraday, Delivery, Cover Order, MTF

export interface OrderRequest {
    quantity: number;
    product: ProductType;
    validity: 'DAY' | 'IOC';
    price: number;
    instrument_token: string;
    order_type: OrderType;
    transaction_type: TransactionType;
    trigger_price?: number;
    disclosed_quantity?: number;
}

export interface OrderModifyRequest {
    order_id: string;
    quantity?: number;
    price?: number;
    order_type?: OrderType;
    trigger_price?: number;
    validity?: 'DAY' | 'IOC';
}

// Get Order Mode (Sandbox/Live)
export async function getOrderMode() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/order/mode`);
        return await res.json();
    } catch (err) {
        console.error('getOrderMode failed:', err);
        return { sandbox_mode: true };
    }
}

// Place Order
export async function placeOrder(order: OrderRequest) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/order/place`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });
        return await res.json();
    } catch (err) {
        console.error('placeOrder failed:', err);
        return { error: String(err) };
    }
}

// Modify Order
export async function modifyOrder(request: OrderModifyRequest) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/order/modify`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return await res.json();
    } catch (err) {
        console.error('modifyOrder failed:', err);
        return { error: String(err) };
    }
}

// Cancel Order
export async function cancelOrder(orderId: string) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/order/cancel/${orderId}`, {
            method: 'DELETE'
        });
        return await res.json();
    } catch (err) {
        console.error('cancelOrder failed:', err);
        return { error: String(err) };
    }
}

// Place Multiple Orders
export async function placeMultiOrder(orders: OrderRequest[]) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/order/place-multi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orders)
        });
        return await res.json();
    } catch (err) {
        console.error('placeMultiOrder failed:', err);
        return { error: String(err) };
    }
}
