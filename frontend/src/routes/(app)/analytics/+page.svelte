<script lang="ts">
    import { onMount } from 'svelte';
    import { authToken } from '$lib/stores';
    import { toast } from 'svelte-sonner';
    import { get } from 'svelte/store';
    import { getAnalyticsDashboard } from '$lib/api/analytics';
    import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
    import * as Card from '$lib/components/ui/card';
    import { Spinner } from '$lib/components/ui/loading';
    import Database from '@lucide/svelte/icons/database';
    import TrendingUp from '@lucide/svelte/icons/trending-up';

    interface AnalyticsData {
        chats_per_day: Array<{ date: string; count: number }>;
        knowledge_base_counts: Array<{
            id: number;
            name: string;
            chat_count: number;
        }>;
        date_range_days: number;
    }

    let loading = $state(true);
    let analyticsData: AnalyticsData | null = $state(null);
    let selectedDays = $state(30);
    let error = $state('');

    async function fetchAnalytics() {
        try {
            loading = true;
            error = '';
            const token = get(authToken);
            
            if (!token) {
                throw new Error('No authentication token found');
            }
            
            analyticsData = await getAnalyticsDashboard(token, selectedDays);
        } catch (err: any) {
            error = err.message || 'Failed to load analytics';
            toast.error(error);
        } finally {
            loading = false;
        }
    }

    function formatDate(dateString: string) {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    function getUserName(user: any) {
        const name = `${user.first_name || ''} ${user.last_name || ''}`.trim();
        return name || user.email;
    }

    onMount(() => {
        fetchAnalytics();
    });
</script>

<svelte:head>
    <title>Analytics Dashboard - MoSPI StatsDoc</title>
</svelte:head>

<AuthGuard requireAdmin={true}>
    <div class="w-full h-full overflow-auto p-6">
            <!-- Header -->
            <div class="mb-6 flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Analytics Dashboard</h1>
                    <p class="text-gray-600 dark:text-gray-400 mt-1">System-wide statistics and insights</p>
                </div>
                
                <!-- Date Range Selector -->
                <select
                    bind:value={selectedDays}
                    onchange={fetchAnalytics}
                    class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                    <option value={365}>Last year</option>
                </select>
            </div>

            {#if loading}
                <div class="flex items-center justify-center h-64">
                    <Spinner size="lg" />
                </div>
            {:else if error}
                <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p class="text-red-800 dark:text-red-200">{error}</p>
                </div>
            {:else if analyticsData}
                <!-- Summary Stats Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <Card.Root>
                        <Card.Content class="p-6">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Chats</p>
                                    <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                        {analyticsData.chats_per_day.reduce((sum, day) => sum + day.count, 0)}
                                    </p>
                                    <p class="text-xs text-gray-500 dark:text-gray-500">Last {selectedDays} days</p>
                                </div>
                                <TrendingUp class="h-8 w-8 text-blue-600" />
                            </div>
                        </Card.Content>
                    </Card.Root>

                    <Card.Root>
                        <Card.Content class="p-6">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Knowledge Bases</p>
                                    <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                        {analyticsData.knowledge_base_counts.length}
                                    </p>
                                    <p class="text-xs text-gray-500 dark:text-gray-500">Total active</p>
                                </div>
                                <Database class="h-8 w-8 text-green-600" />
                            </div>
                        </Card.Content>
                    </Card.Root>
                </div>

                <!-- Daily Chat Activity Table -->
                <Card.Root class="mb-6">
                    <Card.Header>
                        <Card.Title class="flex items-center gap-2">
                            <TrendingUp class="h-5 w-5" />
                            Daily Chat Activity
                        </Card.Title>
                        <Card.Description>Chat volume over the last {selectedDays} days</Card.Description>
                    </Card.Header>
                    <Card.Content>
                        <div class="overflow-auto max-h-96">
                            {#if analyticsData.chats_per_day.length === 0}
                                <p class="text-center text-gray-500 dark:text-gray-400 py-8">No chat data available</p>
                            {:else}
                                <table class="w-full">
                                    <thead class="bg-gray-50 dark:bg-gray-800">
                                        <tr>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Day</th>
                                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Chats</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                                        {#each analyticsData.chats_per_day.slice().reverse() as day, i}
                                            <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                                                    {formatDate(day.date)}
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'long' })}
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-right text-gray-900 dark:text-gray-100">
                                                    {day.count}
                                                </td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            {/if}
                        </div>
                    </Card.Content>
                </Card.Root>

                <!-- Knowledge Base Analytics Table -->
                <Card.Root class="mb-6">
                    <Card.Header>
                        <Card.Title class="flex items-center gap-2">
                            <Database class="h-5 w-5" />
                            Knowledge Base Analytics
                        </Card.Title>
                        <Card.Description>Usage statistics per knowledge base ({analyticsData.knowledge_base_counts.length} total)</Card.Description>
                    </Card.Header>
                    <Card.Content>
                        <div class="overflow-auto max-h-96">
                            {#if analyticsData.knowledge_base_counts.length === 0}
                                <p class="text-center text-gray-500 dark:text-gray-400 py-8">No knowledge bases found</p>
                            {:else}
                                <table class="w-full">
                                    <thead class="bg-gray-50 dark:bg-gray-800">
                                        <tr>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Knowledge Base Name</th>
                                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Chats</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                                        {#each analyticsData.knowledge_base_counts as kb, i}
                                            <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                                                <td class="px-6 py-4">
                                                    <div class="flex items-center">
                                                        <Database class="h-5 w-5 text-gray-400 mr-3" />
                                                        <div class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                            {kb.name}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-right text-gray-900 dark:text-gray-100">
                                                    {kb.chat_count}
                                                </td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            {/if}
                        </div>
                    </Card.Content>
                </Card.Root>
            {/if}
    </div>
</AuthGuard>

<style>
    table {
        border-collapse: collapse;
    }
    th {
        position: sticky;
        top: 0;
        background: inherit;
    }
</style>
