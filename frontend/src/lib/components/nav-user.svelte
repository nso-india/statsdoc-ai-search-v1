<script lang="ts">
  import BadgeCheckIcon from "@lucide/svelte/icons/badge-check";
  import ChevronsUpDownIcon from "@lucide/svelte/icons/chevrons-up-down";
  import LogOutIcon from "@lucide/svelte/icons/log-out";
  import UsersIcon from "@lucide/svelte/icons/users";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { useSidebar } from "$lib/components/ui/sidebar/index.js";
  import { logoutUser } from '$lib/stores';
  import { goto } from '$app/navigation';
  import type { SessionUser } from '$lib/stores';
  import ContactUsDialog from "./ContactUsDialog.svelte";
  import UserManualDialog from "./UserManualDialog.svelte";

  let contactUsOpen = $state(false);
  let userManualOpen = $state(false);
  let dropdownOpen = $state(false);

  let {
    user,
  }: {
    user: SessionUser | undefined;
  } = $props();
  
  const sidebar = useSidebar();

  // Handle contact us click
  function handleContactUs() {
    dropdownOpen = false;
    setTimeout(() => {
      contactUsOpen = true;
    }, 100);
  }

  // Open user manual in an embedded modal (iframe) so app remains visible
  function openUserManual() {
    dropdownOpen = false;
    setTimeout(() => {
      userManualOpen = true;
    }, 100);
  }

  // Handle logout
  async function handleLogout() {
    try {
      logoutUser();
      await goto('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  // Get user initials for fallback avatar
  function getUserInitials(username: string): string {
    return username.slice(0, 2).toUpperCase();
  }

  // Handle user management navigation
  function handleUserManagement() {
    goto('/users');
  }

  // Check if user has admin privileges
  function isAdmin(user: SessionUser | undefined): boolean {
    return !!(user?.role === 'SUPERADMIN' || user?.role === 'STAFF' || user?.is_staff || user?.is_superuser);
  }
</script>
<Sidebar.Menu>
  <Sidebar.MenuItem>
    <DropdownMenu.Root bind:open={dropdownOpen}>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Sidebar.MenuButton
            {...props}
            size="lg"
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          >
            <Avatar.Root class="size-8 rounded-lg">
              <Avatar.Image src={user?.profile_image_url} alt={user?.username} />
              <Avatar.Fallback class="rounded-lg">{user?.username ? getUserInitials(user.username) : 'U'}</Avatar.Fallback>
            </Avatar.Root>
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-medium">{user?.username || 'User'}</span>
              <span class="truncate text-xs">{user?.email || ''}</span>
            </div>
            <ChevronsUpDownIcon class="ml-auto size-4" />
          </Sidebar.MenuButton>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content
        class="w-(--bits-dropdown-menu-anchor-width) min-w-56 rounded-lg z-50"
        side={sidebar.isMobile ? "bottom" : "right"}
        align="end"
        sideOffset={4}
      >
        <DropdownMenu.Label class="p-0 font-normal">
          <div class="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
            <Avatar.Root class="size-8 rounded-lg">
              <Avatar.Image src={user?.profile_image_url} alt={user?.username} />
              <Avatar.Fallback class="rounded-lg">{user?.username ? getUserInitials(user.username) : 'U'}</Avatar.Fallback>
            </Avatar.Root>
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-medium">{user?.username || 'User'}</span>
              <span class="truncate text-xs">{user?.email || ''}</span>
            </div>
          </div>
        </DropdownMenu.Label>
        <DropdownMenu.Separator />
        <DropdownMenu.Group>
          {#if isAdmin(user)}
            <DropdownMenu.Item onclick={handleUserManagement}>
              <UsersIcon class="size-4 mr-2" />
              User Management
            </DropdownMenu.Item>
          {/if}
        </DropdownMenu.Group>
        <DropdownMenu.Separator />
        <DropdownMenu.Item onclick={openUserManual}>
          <BookOpen class="size-4 mr-2" />
          User Manual
        </DropdownMenu.Item>
        <DropdownMenu.Item onclick={handleContactUs}>
          <MessageCircle class="size-4 mr-2" />
          Contact Us
        </DropdownMenu.Item>
        <DropdownMenu.Item onclick={handleLogout}>
          <LogOutIcon class="size-4 mr-2" />
          Log out
        </DropdownMenu.Item>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </Sidebar.MenuItem>
</Sidebar.Menu>

<ContactUsDialog bind:open={contactUsOpen} />
<UserManualDialog bind:open={userManualOpen} />