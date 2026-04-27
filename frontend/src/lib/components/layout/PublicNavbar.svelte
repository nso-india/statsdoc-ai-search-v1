<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  let headerEl: HTMLElement | null = null;

  function setHeaderHeight() {
    if (headerEl && typeof document !== 'undefined') {
      const h = headerEl.offsetHeight;
      document.documentElement.style.setProperty('--public-header-height', `${h}px`);
    }
  }

  onMount(() => {
    setHeaderHeight();
    window.addEventListener('resize', setHeaderHeight);
    const observer = new MutationObserver(setHeaderHeight);
    if (headerEl) observer.observe(headerEl, { childList: true, subtree: true, characterData: true });

    onDestroy(() => {
      window.removeEventListener('resize', setHeaderHeight);
      observer.disconnect();
    });
  });
</script>

<!-- Blue bar at the top -->
<div class="h-5 bg-[#16306b]"></div>

<header bind:this={headerEl} class="bg-white text-gray-900 sticky top-0 z-10 shadow-md">
  <!-- Desktop Layout -->
  <div class="hidden md:block w-full">
    <div class="w-full flex items-center py-4 relative">
      <!-- Logo Section - Absolute Left -->
      <div class="absolute left-0 flex items-center pl-4 gap-2">
        <img 
          src="/MOSPI-Logo.svg" 
          alt="MOSPI Logo" 
          class="h-16 w-auto" 
        />
        <img 
          src="/MOSPILOGO.webp" 
          alt="MOSPI Logo" 
          class="h-20 w-auto" 
        />
      </div>
      
      <!-- Center Content - Absolutely centered -->
      <div class="w-full flex justify-center">
        <div class="text-center">
          <h1 class="text-xl font-bold text-[#16306b]">
            MoSPI StatsDoc AI Assistant<span class="text-xs align-top">βeta</span>
          </h1>
          <p class="text-sm text-gray-600 mt-1">
            AI-Enabled Intelligent Search Solution for Documents
          </p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Mobile Layout -->
  <div class="md:hidden w-full">
    <div class="flex flex-col items-center py-4 px-4 space-y-4">
      <!-- Logo on top for mobile -->
      <div class="flex justify-center gap-2">
        <img 
          src="/MOSPI-Logo.svg" 
          alt="MOSPI Logo" 
          class="h-12 w-auto" 
        />
        <img 
          src="/MOSPILOGO.webp" 
          alt="MOSPI Logo" 
          class="h-16 w-auto" 
        />
      </div>
      
      <!-- Text below logo for mobile -->
      <div class="text-center">
        <h1 class="text-lg font-bold text-[#16306b]">
          MoSPI StatsDoc AI Assistant<span class="text-xs align-top">βeta</span>
        </h1>
        <p class="text-xs text-gray-600 mt-1">AI-Enabled Intelligent Search Solution for Documents</p>

      </div>
    </div>
  </div>
</header>
