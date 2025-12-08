<!-- Settings/Credentials Page - Configure Upstox API Keys -->
<script lang="ts">
    import { enhance } from "$app/forms";

    let { data } = $props();

    let isSubmitting = $state(false);
    let message = $state("");
    let messageType = $state<"success" | "error" | "">("");

    // Form values
    let apiKey = $state(data.credentials?.apiKey || "");
    let apiSecret = $state(data.credentials?.apiSecret || "");
    let redirectUri = $state(
        data.credentials?.redirectUri ||
            "http://localhost:8000/api/v1/auth/callback",
    );

    async function handleSubmit(event: Event) {
        event.preventDefault();
        isSubmitting = true;
        message = "";

        try {
            const response = await fetch(
                "http://localhost:8000/api/v1/auth/configure",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        api_key: apiKey,
                        api_secret: apiSecret,
                        redirect_uri: redirectUri,
                    }),
                },
            );

            const result = await response.json();

            if (response.ok) {
                message = "✅ Credentials saved successfully!";
                messageType = "success";
            } else {
                message = `❌ Error: ${result.detail || "Failed to save"}`;
                messageType = "error";
            }
        } catch (err) {
            message = "❌ Failed to connect to backend";
            messageType = "error";
        } finally {
            isSubmitting = false;
        }
    }
</script>

<div class="settings-page">
    <div class="page-header">
        <h1>🔑 API Credentials</h1>
        <p>Configure your Upstox API credentials for trading</p>
    </div>

    <form class="credentials-form" onsubmit={handleSubmit}>
        <div class="form-group">
            <label for="apiKey">API Key</label>
            <input
                type="text"
                id="apiKey"
                bind:value={apiKey}
                placeholder="Enter your Upstox API Key"
                required
            />
        </div>

        <div class="form-group">
            <label for="apiSecret">API Secret</label>
            <input
                type="password"
                id="apiSecret"
                bind:value={apiSecret}
                placeholder="Enter your Upstox API Secret"
                required
            />
        </div>

        <div class="form-group">
            <label for="redirectUri">Redirect URI</label>
            <input
                type="text"
                id="redirectUri"
                bind:value={redirectUri}
                placeholder="http://localhost:8000/api/v1/auth/callback"
                required
            />
            <small>This should match your Upstox app settings</small>
        </div>

        {#if message}
            <div
                class="message"
                class:success={messageType === "success"}
                class:error={messageType === "error"}
            >
                {message}
            </div>
        {/if}

        <div class="form-actions">
            <button type="submit" class="btn-primary" disabled={isSubmitting}>
                {#if isSubmitting}
                    <span class="spinner-small"></span> Saving...
                {:else}
                    💾 Save Credentials
                {/if}
            </button>
            <a href="/auth/refresh" class="btn-secondary">
                🔄 Login with Upstox
            </a>
        </div>
    </form>

    <div class="help-card">
        <h3>📖 How to get API credentials?</h3>
        <ol>
            <li>
                Go to <a
                    href="https://login.upstox.com/developer/apps"
                    target="_blank">Upstox Developer Portal</a
                >
            </li>
            <li>Create a new app or select existing app</li>
            <li>Copy the API Key and API Secret</li>
            <li>Set Redirect URI to match above</li>
            <li>Save credentials and click "Login with Upstox"</li>
        </ol>
    </div>
</div>

<style>
    .settings-page {
        max-width: 600px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: 32px;
    }

    .page-header h1 {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .page-header p {
        color: var(--text-secondary);
    }

    .credentials-form {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
    }

    .form-group {
        margin-bottom: 24px;
    }

    .form-group label {
        display: block;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 8px;
        color: var(--text-primary);
    }

    .form-group input {
        width: 100%;
        padding: 12px 16px;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 14px;
        font-family: var(--font-mono);
        transition: all 0.2s ease;
    }

    .form-group input:focus {
        outline: none;
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px var(--border-glow);
    }

    .form-group input::placeholder {
        color: var(--text-muted);
    }

    .form-group small {
        display: block;
        margin-top: 6px;
        font-size: 12px;
        color: var(--text-muted);
    }

    .message {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-size: 14px;
    }

    .message.success {
        background: rgba(0, 210, 106, 0.1);
        border: 1px solid rgba(0, 210, 106, 0.3);
        color: var(--accent-green);
    }

    .message.error {
        background: rgba(255, 71, 87, 0.1);
        border: 1px solid rgba(255, 71, 87, 0.3);
        color: var(--accent-red);
    }

    .form-actions {
        display: flex;
        gap: 12px;
    }

    .btn-primary,
    .btn-secondary {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
    }

    .btn-primary {
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        color: white;
        border: none;
    }

    .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    .btn-primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .btn-secondary {
        background: var(--bg-hover);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .btn-secondary:hover {
        border-color: var(--accent-green);
        color: var(--accent-green);
    }

    .spinner-small {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .help-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
    }

    .help-card h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
    }

    .help-card ol {
        padding-left: 20px;
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 2;
    }

    .help-card a {
        color: var(--accent-blue);
    }

    .help-card a:hover {
        text-decoration: underline;
    }
</style>
