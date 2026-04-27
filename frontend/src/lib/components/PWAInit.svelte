<script lang="ts">
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import { pwaInstallPrompt, updateAvailable, swRegistration } from '$lib/stores/pwa';

  onMount(async () => {
    if (!browser) return;

    try {
      // Register service worker
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });

        swRegistration.set(registration);

        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available
                updateAvailable.set(true);
              }
            });
          }
        });

        console.log('Service Worker registered successfully');
      }

      // Handle service worker messages
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data && event.data.type === 'SKIP_WAITING') {
            window.location.reload();
          }
        });
      }

    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  });
</script>

