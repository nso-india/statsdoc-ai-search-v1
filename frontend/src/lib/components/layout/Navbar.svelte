<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import { goto } from "$app/navigation";
  import { createEventDispatcher } from 'svelte';

  export let userProfile = { username: 'Admin', email: 'admin@example.com' };
  
  const dispatch = createEventDispatcher();

  function handleLogout() {
    dispatch('logout');
  }
</script>

<header class="border-b bg-background sticky top-0 z-10">
  <div class="container max-w-full px-4 py-3">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-3">
        <img src="/MOSPI-Logo.svg" alt="MOSPI Logo" class="h-10 w-auto" />
        <img src="/MOSPILOGO.webp" alt="Logo" class="h-10 w-10" />
        <div class="flex flex-col leading-tight">
          <span class="text-sm font-semibold">MoSPI StatsDoc AI Assistantβeta</span>
          <span class="font-heading text-xs text-gray-500 hidden sm:block">MOSPI</span>
          <span class="font-heading text-xs text-gray-500 sm:hidden">MOSPI</span>
        </div>"
      </div>
      
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild let:builder>
          <Button builders={[builder]} variant="outline">
            {userProfile?.username || 'Loading...'}
          </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end">
          <DropdownMenu.Label>Account</DropdownMenu.Label>
          {#if userProfile}
            <DropdownMenu.Item disabled>{userProfile.email}</DropdownMenu.Item>
          {/if}
          <DropdownMenu.Separator />
          <DropdownMenu.Item>Settings</DropdownMenu.Item>
          <DropdownMenu.Item class="text-red-500" on:click={handleLogout}>Logout</DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
  </div>
</header>