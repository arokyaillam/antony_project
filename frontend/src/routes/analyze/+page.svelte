<script lang="ts">
    import IndexSelector from "$lib/components/IndexSelector.svelte";
    import UnifiedStrikeTable from "$lib/components/UnifiedStrikeTable.svelte";
    import IndexIndicatorTable from "$lib/components/IndexIndicatorTable.svelte";
</script>

<div class="analyze-page">
    <div class="header-section">
        <h1>Option Analysis</h1>
        <IndexSelector />
    </div>

    <!-- Indicator (ATM Straddle) Table -->
    <IndexIndicatorTable />

    <!-- Unified Strike Analysis Table -->
    <UnifiedStrikeTable />
</div>

<style>
    .analyze-page {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px;
    }
    .header-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
