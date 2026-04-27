<script lang="ts">
  import { onMount } from 'svelte';
  
  onMount(() => {
    // Check if we're online and redirect
    if (navigator.onLine) {
      window.location.href = '/';
    }
  });
</script>

<svelte:head>
  <title>Offline - MOSPI</title>
  <meta name="description" content="You are currently offline. Please check your internet connection." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
  <div class="max-w-md w-full text-center">
    <div class="mb-6">
      <img 
        src="/MOSPI-Logo.svg" 
        alt="MOSPI Logo" 
        class="h-16 w-auto mx-auto mb-4" 
      />
      
      <div class="w-16 h-16 mx-auto mb-4 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
        <svg class="w-8 h-8 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 1 0 0 19.5 9.75 9.75 0 0 0 0-19.5z" />
        </svg>
      </div>
      
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        You're Offline
      </h1>
      
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        It looks like you've lost your internet connection. Please check your network settings and try again.
      </p>
    </div>
    
    <div class="space-y-3">
      <button
        onclick={() => window.location.reload()}
        class="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
      >
        Try Again
      </button>
      
      <button
        onclick={() => window.history.back()}
        class="w-full bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      >
        Go Back
      </button>
    </div>
    
    <div class="mt-6 text-xs text-gray-500 dark:text-gray-400">
      <p>Some cached content may still be available</p>
    </div>
  </div>
</div>

