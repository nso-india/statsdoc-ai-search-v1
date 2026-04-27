import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  plugins: [sveltekit()],
  optimizeDeps: {
    include: [],
    exclude: []
  },
  resolve: {
    alias: []
  },
  server: {
    fs: {
      // Allow serving files from the project root
      allow: [
        path.resolve(__dirname, '..')
      ]
    }
  }
});
