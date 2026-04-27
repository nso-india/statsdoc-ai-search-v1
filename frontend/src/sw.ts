import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { clientsClaim, skipWaiting } from 'workbox-core';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';

declare const self: ServiceWorkerGlobalScope & typeof globalThis & {
  __WB_MANIFEST: any;
};

// Enable immediate claiming and activation
skipWaiting();
clientsClaim();

// Clean up outdated caches
cleanupOutdatedCaches();

// Precache all static assets
precacheAndRoute(self.__WB_MANIFEST);

// Cache API responses with NetworkFirst strategy
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    networkTimeoutSeconds: 5,
  })
);

// Cache images with CacheFirst strategy  
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache',
  })
);

// Cache CSS and JS files with StaleWhileRevalidate
registerRoute(
  ({ request }) => 
    request.destination === 'style' ||
    request.destination === 'script',
  new StaleWhileRevalidate({
    cacheName: 'static-resources',
  })
);

// Cache fonts
registerRoute(
  ({ url }) => url.origin === 'https://fonts.googleapis.com' ||
             url.origin === 'https://fonts.gstatic.com',
  new StaleWhileRevalidate({
    cacheName: 'google-fonts',
  })
);

// Handle navigation requests (SPA routing)
const navigationRoute = new NavigationRoute(
  async () => {
    // Return cached version or fallback to index.html
    const cachedResponse = await caches.match('/') || await caches.match('/index.html');
    return cachedResponse || Response.redirect('/');
  },
  {
    allowlist: [/^\/$/, /^\/c/, /^\/settings/],
    denylist: [/\/api\//, /\/_app\//, /\.json$/],
  }
);

registerRoute(navigationRoute);
