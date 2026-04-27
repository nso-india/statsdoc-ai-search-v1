<script lang="ts">
  import { isOnline } from '$lib/stores/pwa';
  import { onMount } from 'svelte';

  let online = true;
  let showOfflineToast = false;
  let toastTimer: NodeJS.Timeout;

  onMount(() => {
    const unsubscribe = isOnline.subscribe((status) => {
      const wasOffline = !online;
      online = status;
      
      if (!status) {
        // Just went offline
        showOfflineToast = true;
        if (toastTimer) clearTimeout(toastTimer);
      } else if (wasOffline && status) {
        // Just came back online
        showOfflineToast = true;
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
          showOfflineToast = false;
        }, 3000);
      }
    });

    return unsubscribe;
  });
</script>

{#if showOfflineToast}
  <div class="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
    <div class="bg-[#fafafa] dark:bg-gray-800 border {online ? 'border-green-200 dark:border-green-700' : 'border-amber-200 dark:border-amber-700'} rounded-lg shadow-lg p-3">
      <div class="flex items-center gap-2">
        {#if online}
          <div class="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full"></div>
          <span class="text-sm font-medium text-green-700 dark:text-green-300">
            Back online
          </span>
        {:else}
          <div class="flex-shrink-0 w-2 h-2 bg-amber-500 rounded-full"></div>
          <span class="text-sm font-medium text-amber-700 dark:text-amber-300">
            You're offline
          </span>
        {/if}
      </div>
    </div>
  </div>
{/if}

{#if !online}
  <!-- Persistent offline indicator -->
  <div class="fixed bottom-0 left-0 right-0 bg-amber-100 dark:bg-amber-900 border-t border-amber-200 dark:border-amber-800 px-4 py-2 z-40">
    <div class="flex items-center justify-center gap-2 text-amber-800 dark:text-amber-200">
      <div class="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
      <span class="text-sm font-medium">Offline mode - Some features may be limited</span>
    </div>
  </div>
{/if}

