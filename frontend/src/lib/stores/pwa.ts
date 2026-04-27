import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// PWA installation store
export const pwaInstallPrompt = writable<any>(null);
export const isPWAInstalled = writable<boolean>(false);
export const isOnline = writable<boolean>(true);
export const updateAvailable = writable<boolean>(false);

// Service worker registration store
export const swRegistration = writable<ServiceWorkerRegistration | null>(null);

if (browser) {
  // Track online/offline status
  const updateOnlineStatus = () => {
    isOnline.set(navigator.onLine);
  };
  
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();

  // Track PWA install prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    pwaInstallPrompt.set(e);
  });

  // Check if PWA is already installed
  window.addEventListener('appinstalled', () => {
    isPWAInstalled.set(true);
    pwaInstallPrompt.set(null);
  });

  // Check if running as PWA
  const checkPWAMode = () => {
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                        (window.navigator as any)?.standalone ||
                        document.referrer.includes('android-app://');
    isPWAInstalled.set(isStandalone);
  };
  
  checkPWAMode();
}

// Install PWA function
export const installPWA = async () => {
  return new Promise((resolve) => {
    const unsubscribe = pwaInstallPrompt.subscribe(async (prompt) => {
      if (prompt) {
        try {
          const result = await prompt.prompt();
          if (result.outcome === 'accepted') {
            isPWAInstalled.set(true);
            resolve(true);
          } else {
            resolve(false);
          }
        } catch (error) {
          console.error('Error installing PWA:', error);
          resolve(false);
        }
        pwaInstallPrompt.set(null);
      } else {
        resolve(false);
      }
    });
    unsubscribe();
  });
};

// Update service worker function
export const updateServiceWorker = async () => {
  return new Promise<void>((resolve) => {
    const unsubscribe = swRegistration.subscribe((registration) => {
      if (registration && registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        updateAvailable.set(false);
        
        // Reload page after update
        window.location.reload();
        resolve();
      } else {
        resolve();
      }
    });
    unsubscribe();
  });
};

