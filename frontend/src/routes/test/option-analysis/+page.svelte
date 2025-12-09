<script lang="ts">
    import IndexSelector from "$lib/components/IndexSelector.svelte";
    import OptionChainTable from "$lib/components/OptionChainTable.svelte";
</script>

<div class="analysis-page">
    <div class="header-section">
        <h1>Option Chain Analysis</h1>
        <IndexSelector />
    </div>

    <div class="content-section">
        <OptionChainTable />
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
