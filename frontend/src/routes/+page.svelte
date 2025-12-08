<!-- Home Page - Landing/Dashboard redirect -->
<script lang="ts">
</script>

<div class="home-container">
    <div class="hero">
        <h1>📈 Antony <span class="highlight">HFT</span></h1>
        <p class="tagline">High-Frequency Algorithmic Trading System</p>

        <div class="status-cards">
            <div class="status-card">
                <span class="icon">🔗</span>
                <span class="label">Backend</span>
                <span class="value text-green">Connected</span>
            </div>
            <div class="status-card">
                <span class="icon">📊</span>
                <span class="label">Market</span>
                <span class="value text-muted">Waiting...</span>
            </div>
        </div>

        <div class="cta-buttons">
            <a href="/settings/credentials" class="btn-primary">
                🔑 Setup API Credentials
            </a>
            <a href="/dashboard" class="btn-secondary"> 📊 Go to Dashboard </a>
        </div>
    </div>
</div>

<style>
    .home-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 70vh;
        text-align: center;
    }

    .hero h1 {
        font-size: 48px;
        font-weight: 800;
        margin-bottom: 16px;
        letter-spacing: -1px;
    }

    .hero .highlight {
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .tagline {
        font-size: 18px;
        color: var(--text-secondary);
        margin-bottom: 40px;
    }

    .status-cards {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 40px;
    }

    .status-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 20px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }

    .status-card .icon {
        font-size: 20px;
    }

    .status-card .label {
        font-size: 14px;
        color: var(--text-secondary);
    }

    .status-card .value {
        font-size: 14px;
        font-weight: 600;
    }

    .cta-buttons {
        display: flex;
        gap: 16px;
        justify-content: center;
        flex-wrap: wrap;
    }

    .btn-primary,
    .btn-secondary {
        padding: 14px 28px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 15px;
        text-decoration: none;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .btn-primary {
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        color: white;
    }

    .btn-primary:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
    }

    .btn-secondary {
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .btn-secondary:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 0 16px var(--border-glow);
    }
</style>
