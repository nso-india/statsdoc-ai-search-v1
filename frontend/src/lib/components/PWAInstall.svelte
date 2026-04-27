<script lang="ts">
  import { pwaInstallPrompt, isPWAInstalled, installPWA } from '$lib/stores/pwa';
  import { onMount } from 'svelte';

  let showInstallButton = false;

  onMount(() => {
    // Subscribe to PWA install prompt availability
    const unsubscribePrompt = pwaInstallPrompt.subscribe((prompt) => {
      showInstallButton = !!prompt;
    });

    const unsubscribeInstalled = isPWAInstalled.subscribe((installed) => {
      if (installed) {
        showInstallButton = false;
      }
    });

    return () => {
      unsubscribePrompt();
      unsubscribeInstalled();
    };
  });

  const handleInstall = async () => {
    await installPWA();
  };
</script>

{#if showInstallButton}
  <div class="fixed bottom-4 left-4 right-4 z-50 md:left-auto md:right-4 md:w-80">
    <div class="bg-[#fafafa] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4">
      <div class="flex items-start gap-3">
        <div class="flex-shrink-0">
          <img src="/pwa-192x192.png" alt="MOSPI" class="w-12 h-12 rounded-lg" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Install MOSPI App
          </h3>
          <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
            Add MOSPI to your home screen for quick access and a better experience.
          </p>
          <div class="flex gap-2 mt-3">
            <button
              onclick={handleInstall}
              class="px-3 py-1.5 bg-[#162f6a] text-white text-xs font-medium rounded hover:bg-[#1a3575] transition-colors"
            >
              Install
            </button>
            <button
              onclick={() => pwaInstallPrompt.set(null)}
              class="px-3 py-1.5 text-gray-600 dark:text-gray-400 text-xs font-medium rounded hover:bg-[#f0f0f0] dark:hover:bg-gray-700 transition-colors"
            >
              Maybe later
            </button>
          </div>
        </div>
        <button
          onclick={() => pwaInstallPrompt.set(null)}
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

