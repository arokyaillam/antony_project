<!-- Auth Refresh Page - Shows loading while redirecting -->
<script lang="ts">
    import { onMount } from "svelte";
</script>

<div class="refresh-container">
    <div class="refresh-card">
        <div class="spinner"></div>
        <h2>Refreshing Token...</h2>
        <p>Redirecting to Upstox for authentication</p>
    </div>
</div>

<style>
    .refresh-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
    }

    .refresh-card {
        text-align: center;
        padding: 48px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
    }

    .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid var(--border-color);
        border-top-color: var(--accent-blue);
        border-radius: 50%;
        margin: 0 auto 24px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    h2 {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    p {
        color: var(--text-secondary);
        font-size: 14px;
    }
</style>
