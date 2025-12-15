<script lang="ts">
    import ActiveIndexCard from "$lib/components/ActiveIndexCard.svelte";
    import ActiveStrikes from "$lib/components/ActiveStrikes.svelte";
</script>

<div class="dashboard">
    <h1 class="page-title">📊 Live Dashboard</h1>

    <section class="index-cards">
        <ActiveIndexCard />
    </section>

    <!-- Active Strikes Section -->
    <ActiveStrikes />
</div>

<style>
    .dashboard {
        max-width: 1400px;
        margin: 0 auto;
    }

    .page-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 24px;
        color: var(--text-primary);
    }

    .index-cards {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
    }
</style>
