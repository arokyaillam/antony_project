<!-- Header Component - Top navigation bar -->
<script lang="ts">
    import UserMenu from "./UserMenu.svelte";
</script>

<header class="header">
    <div class="header-left">
        <a href="/" class="logo">
            <span class="logo-icon">📈</span>
            <span class="logo-text"
                >Antony <span class="highlight">HFT</span></span
            >
        </a>
    </div>

    <nav class="nav">
        <a href="/dashboard" class="nav-link">Dashboard</a>
        <a href="/orders" class="nav-link">Orders</a>
        <a href="/portfolio" class="nav-link">Portfolio</a>
        <a href="/analyze" class="nav-link">Analyze</a>
    </nav>

    <div class="header-right">
        <div class="status-badge">
            <span class="status-dot"></span>
            <span class="status-text">Live</span>
        </div>
        <UserMenu />
    </div>
</header>

<style>
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: var(--header-height);
        padding: 0 24px;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border-color);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .header-left {
        display: flex;
        align-items: center;
    }

    .logo {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        transition: transform 0.2s ease;
    }

    .logo:hover {
        transform: scale(1.02);
    }

    .logo-icon {
        font-size: 28px;
    }

    .logo-text {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }

    .logo-text .highlight {
        background: linear-gradient(
            135deg,
            var(--accent-blue),
            var(--accent-purple)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .nav {
        display: flex;
        gap: 8px;
    }

    .nav-link {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        text-decoration: none;
        transition: all 0.2s ease;
    }

    .nav-link:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .status-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: rgba(0, 210, 106, 0.1);
        border: 1px solid rgba(0, 210, 106, 0.3);
        border-radius: 20px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-green);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%,
        100% {
            box-shadow: 0 0 0 0 rgba(0, 210, 106, 0.4);
        }
        50% {
            box-shadow: 0 0 0 6px rgba(0, 210, 106, 0);
        }
    }

    .status-text {
        font-size: 12px;
        font-weight: 600;
        color: var(--accent-green);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
