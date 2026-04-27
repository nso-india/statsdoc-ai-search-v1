<script lang="ts">
  import { updateAvailable, updateServiceWorker } from '$lib/stores/pwa';
  import { onMount } from 'svelte';

  let showUpdateBanner = false;

  onMount(() => {
    const unsubscribe = updateAvailable.subscribe((available) => {
      showUpdateBanner = available;
    });

    return unsubscribe;
  });

  const handleUpdate = async () => {
    await updateServiceWorker();
  };

  const dismissUpdate = () => {
    updateAvailable.set(false);
  };
</script>

{#if showUpdateBanner}
  <div class="fixed top-4 left-4 right-4 z-50 md:left-auto md:right-4 md:w-80">
    <div class="bg-[#fafafa] dark:bg-gray-800 border border-[#162f6a] dark:border-gray-700 rounded-lg shadow-lg p-4">
      <div class="flex items-start gap-3">
        <div class="flex-shrink-0">
          <div class="w-8 h-8 bg-[#f0f0f0] dark:bg-gray-700 rounded-full flex items-center justify-center">
            <svg class="w-4 h-4 text-[#162f6a] dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Update Available
          </h3>
          <p class="text-xs text-gray-700 dark:text-gray-300 mt-1">
            A new version of MOSPI is available. Update now to get the latest features and improvements.
          </p>
          <div class="flex gap-2 mt-3">
            <button
              onclick={handleUpdate}
              class="px-3 py-1.5 bg-[#162f6a] text-white text-xs font-medium rounded hover:bg-[#1a3575] transition-colors"
            >
              Update Now
            </button>
            <button
              onclick={dismissUpdate}
              class="px-3 py-1.5 text-gray-600 dark:text-gray-400 text-xs font-medium rounded hover:bg-[#f0f0f0] dark:hover:bg-gray-700 transition-colors"
            >
              Later
            </button>
          </div>
        </div>
        <button
          onclick={dismissUpdate}
          class="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          aria-label="Close"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
{/if}

