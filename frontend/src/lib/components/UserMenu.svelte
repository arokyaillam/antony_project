<!-- User Menu Component - Right corner dropdown -->
<script lang="ts">
  import { slide, fade } from "svelte/transition";

  let isOpen = $state(false);

  // Settings menu items - 4 essential options only
  const menuItems = [
    { icon: "📡", label: "Upstox Feed Connect", href: "/settings/connect" },
    { icon: "🔑", label: "API Credentials", href: "/settings/credentials" },
    { divider: true },
    { icon: "🔄", label: "Refresh Token", href: "/auth/refresh" },
    { icon: "🚪", label: "Logout", href: "/auth/logout", danger: true },
  ];

  function toggleMenu() {
    isOpen = !isOpen;
  }

  function closeMenu() {
    isOpen = false;
  }

  // Close on outside click
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest(".user-menu")) {
      closeMenu();
    }
  }
</script>

<svelte:window onclick={handleClickOutside} />

<div class="user-menu">
  <button class="user-icon" onclick={toggleMenu} aria-label="User menu">
    <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
      <path
        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"
      />
    </svg>
    <span class="status-dot"></span>
  </button>

  {#if isOpen}
    <div class="dropdown" transition:slide={{ duration: 200 }}>
      <div class="dropdown-header">
        <span class="user-name">Antony HFT</span>
        <span class="user-status">● Connected</span>
      </div>

      <div class="menu-items">
        {#each menuItems as item}
          {#if item.divider}
            <hr class="divider" />
          {:else}
            <a
              href={item.href}
              class="menu-item"
              class:danger={item.danger}
              onclick={closeMenu}
            >
              <span class="icon">{item.icon}</span>
              <span class="label">{item.label}</span>
            </a>
          {/if}
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .user-menu {
    position: relative;
  }

  .user-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--bg-card), var(--bg-hover));
    border: 2px solid var(--border-color);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .user-icon:hover {
    border-color: var(--accent-blue);
    box-shadow: 0 0 16px var(--border-glow);
    transform: scale(1.05);
  }

  .status-dot {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 10px;
    height: 10px;
    background: var(--accent-green);
    border-radius: 50%;
    border: 2px solid var(--bg-primary);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .dropdown {
    position: absolute;
    top: 54px;
    right: 0;
    width: 220px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    z-index: 1000;
  }

  .dropdown-header {
    padding: 16px;
    background: linear-gradient(135deg, var(--bg-hover), var(--bg-card));
    border-bottom: 1px solid var(--border-color);
  }

  .user-name {
    display: block;
    font-weight: 600;
    font-size: 14px;
    color: var(--text-primary);
  }

  .user-status {
    font-size: 12px;
    color: var(--accent-green);
  }

  .menu-items {
    padding: 8px 0;
  }

  .menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .menu-item:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .menu-item.danger {
    color: var(--accent-red);
  }

  .menu-item.danger:hover {
    background: rgba(255, 71, 87, 0.1);
  }

  .icon {
    font-size: 16px;
  }

  .label {
    font-size: 13px;
    font-weight: 500;
  }

  .divider {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 8px 0;
  }
</style>
