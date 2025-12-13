<script lang="ts">
    import PatternTable from "$lib/components/PatternTable.svelte";
    import PriceActionTable from "$lib/components/PriceActionTable.svelte";
</script>

<div class="analysis-page">
    <div class="header-section">
        <h1>Pattern Analysis</h1>
    </div>

    <div class="content-section">
        <PatternTable />
        <PriceActionTable />
    </div>
</div>

<style>
    .analysis-page {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
    }

    .header-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }

    h1 {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
    }

    .content-section {
        min-height: 500px;
    }
</style>
