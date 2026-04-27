<script lang="ts">
  import { user } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import AppSidebar from "$lib/components/app-sidebar.svelte";
  import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";

  let { children } = $props();

  // Permission check for admin access
  onMount(() => {
    if ($user && !($user.role === 'SUPERADMIN' || $user.is_staff || $user.is_superuser)) {
      toast.error('Access denied. Admin privileges required.');
      goto('/c');
    }
  });

  $effect(() => {
    if ($user && !($user.role === 'SUPERADMIN' || $user.is_staff || $user.is_superuser)) {
      toast.error('Access denied. Admin privileges required.');
      goto('/c');
    }
  });
</script>

<svelte:head>
  <style>
    /* Use CSS custom properties for proper mobile viewport height */
    :root {
      --app-height: 100vh;
    }
    @supports (height: 100dvh) {
      :root {
        --app-height: 100dvh; /* Dynamic viewport height - accounts for mobile browser UI */
      }
    }
  </style>
</svelte:head>

<Sidebar.Provider>
  <AppSidebar />
  <Sidebar.Inset class="flex flex-col overflow-hidden" style="height: var(--app-height); max-height: var(--app-height);">
    <header class="flex h-11 shrink-0 items-center gap-2 bg-gradient-to-b from-white to-white/80 dark:from-gray-900 dark:to-gray-900/80 backdrop-blur-sm fixed top-0 left-0 right-0 md:sticky md:top-0 z-20 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-2 px-4">
        <Sidebar.Trigger class="-ml-1" />
        <Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumb.Root>
          <Breadcrumb.List>
            <Breadcrumb.Item>
              <Breadcrumb.Page>Settings</Breadcrumb.Page>
            </Breadcrumb.Item>
          </Breadcrumb.List>
        </Breadcrumb.Root>
      </div>
    </header>
    <main class="flex-1 overflow-hidden min-h-0 max-h-full mt-11 md:mt-0">
      {@render children?.()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>