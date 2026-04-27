<script lang="ts">
  import AppSidebar from "$lib/components/app-sidebar.svelte";
  import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { page } from "$app/stores";

  let { children } = $props();
  
  // Get page title from route
  const pageTitle = $derived('Admin');
</script>

<Sidebar.Provider>
  <AppSidebar />
  <Sidebar.Inset class="flex flex-col h-screen overflow-hidden">
    <header class="flex h-11 shrink-0 items-center gap-2 bg-gradient-to-b from-white to-white/80 dark:from-gray-900 dark:to-gray-900/80 backdrop-blur-sm">
      <div class="flex items-center gap-2 px-4">
        <Sidebar.Trigger class="-ml-1" />
        <Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumb.Root>
          <Breadcrumb.List>
            <Breadcrumb.Item>
              <Breadcrumb.Page>{pageTitle}</Breadcrumb.Page>
            </Breadcrumb.Item>
          </Breadcrumb.List>
        </Breadcrumb.Root>
      </div>
    </header>
    <main class="flex-1 overflow-auto min-h-0">
      {@render children?.()}
    </main>
  </Sidebar.Inset>
</Sidebar.Provider>
