<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { flyAndScale } from '../../../lib/utils/transitions';

  // Import ShadCN UI components
  import { Badge } from '../../../lib/components/ui/badge';
  import { Button } from '../../../lib/components/ui/button';
  import { Input } from '../../../lib/components/ui/input';
  import * as Table from '../../../lib/components/ui/table';
  import { Label } from '../../../lib/components/ui/label';
  import * as Avatar from '../../../lib/components/ui/avatar';
  import * as DropdownMenu from '../../../lib/components/ui/dropdown-menu';

  // Icons
  import Search from 'lucide-svelte/icons/search';
  import UserPlus from 'lucide-svelte/icons/user-plus';
  import Upload from 'lucide-svelte/icons/upload';
  import Download from 'lucide-svelte/icons/download';
  import Pencil from 'lucide-svelte/icons/pencil';
  import MessageSquare from 'lucide-svelte/icons/message-square';
  import X from 'lucide-svelte/icons/x';
  import MoreHorizontal from 'lucide-svelte/icons/more-horizontal';
  import Trash2 from 'lucide-svelte/icons/trash-2';
  import LogOut from 'lucide-svelte/icons/log-out';
  import Settings from 'lucide-svelte/icons/settings';
  import Users from 'lucide-svelte/icons/users';
  import { Spinner } from '../../../lib/components/ui/loading';

  // Modals
  import AddUserModal from '../../../lib/components/admin/AddUserModal.svelte';
  import UserChatsModal from '../../../lib/components/admin/UserChatsModal.svelte';
  import AuthGuard from '../../../lib/components/auth/AuthGuard.svelte';

  // API
  import { UsersAPI, type ApiUser, type UserListResponse } from '../../../lib/api/users';
  import { AdminChatAPI, type UserChat, type UserChatMessage } from '../../../lib/apis/admin-chats';
  import { user, isAuthenticated, logoutUser } from '../../../lib/stores';

  // Interfaces
  interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role: 'SUPERADMIN' | 'STAFF' | 'USER';
    is_active: boolean;
    is_staff: boolean;
    is_superuser: boolean;
    last_login: string | null;
    date_joined: string;
  }

  interface Chat {
    id: number;
    title: string;
    created_at: string;
    updated_at: string;
    user?: number;
    message_count?: number;
  }

  // Component state
  let users = $state<User[]>([]);
  let filteredUsers = $state<User[]>([]);
  let loading = $state(false);
  let errorMessage = $state('');
  let searchQuery = $state('');
  let showAddUserModal = $state(false);
  let showEditUserModal = $state(false);
  let showUserChatsModal = $state(false);
  let selectedUser = $state<User | null>(null);
  let selectedUserChats = $state<Chat[]>([]);
  let loadingUserChats = $state(false);
  
  // Pagination state
  let currentPage = $state(1);
  let totalPages = $state(1);
  let totalCount = $state(0);
  let pageSize = $state(20);

  // Bulk upload state
  let fileInput: HTMLInputElement;
  let bulkUploading = $state(false);

  function handleAddUserClick() {
    showAddUserModal = true;
  }

  // Initialize component
  onMount(async () => {
    if (!loading) {
      await loadUsers();
    }
    
    // Cleanup function
    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  });

  async function loadUsers() {
    if (loading) return; // Prevent multiple simultaneous calls
    loading = true;
    errorMessage = '';
    const startTime = Date.now();
    try {
      const response: UserListResponse = await UsersAPI.listUsers(
        searchQuery || undefined,
        undefined, // is_active filter
        currentPage,
        pageSize
      );
      
      users = response.users.map(apiUser => ({
        id: apiUser.id,
        username: apiUser.username,
        email: apiUser.email,
        first_name: apiUser.first_name,
        last_name: apiUser.last_name,
        role: apiUser.is_superuser ? 'SUPERADMIN' : apiUser.is_staff ? 'STAFF' : 'USER',
        is_active: apiUser.is_active,
        is_staff: apiUser.is_staff,
        is_superuser: apiUser.is_superuser,
        last_login: apiUser.last_login,
        date_joined: apiUser.date_joined
      }));
      
      // Update pagination
      currentPage = response.pagination.page;
      totalPages = response.pagination.total_pages;
      totalCount = response.pagination.total_count;
      
      filteredUsers = users; // Since filtering is now done server-side
    } catch (error) {
      console.error('Error loading users:', error);
      errorMessage = error instanceof Error ? error.message : 'Failed to load users';
      toast.error('Failed to load users');
    } finally {
      // Ensure minimum loading time to prevent flickering
      const elapsed = Date.now() - startTime;
      const minLoadingTime = 300; // 300ms minimum
      if (elapsed < minLoadingTime) {
        setTimeout(() => {
          loading = false;
        }, minLoadingTime - elapsed);
      } else {
        loading = false;
      }
    }
  }

  // Remove the applyFilters function since filtering is now server-side
  
  // Debounced search function
  let searchTimeout: NodeJS.Timeout;
  function handleSearchChange() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      if (currentPage !== 1) {
        currentPage = 1; // Reset to first page when searching
      }
      loadUsers();
    }, 500); // Increased debounce time for better performance
  }

  // Only trigger search when user actually types
  function handleSearchInput() {
    handleSearchChange();
  }

  async function handleAddUser(event: CustomEvent) {
    const response = event.detail.user;
    try {
      // User was already created via API in the modal
      // Reload the users list to get the updated data
      await loadUsers();
    } catch (error) {
      console.error('Error refreshing users:', error);
      toast.error('Failed to refresh user list');
    }
  }

  async function deleteUser(userId: number) {
    if (!confirm('Are you sure you want to permanently delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      const result = await UsersAPI.deleteUser(userId);
      await loadUsers(); // Reload users after deletion
      toast.success(result.message || 'User deleted permanently');
    } catch (error) {
      console.error('Error deleting user:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        toast.error(error.message);
      } else {
        console.error('Unknown error:', error);
        toast.error('Failed to delete user');
      }
    }
  }

  async function activateUser(userId: number) {
    try {
      const result = await UsersAPI.activateUser(userId);
      await loadUsers(); // Reload users after activation
      toast.success(result.message || 'User activated successfully');
    } catch (error) {
      console.error('Error activating user:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        toast.error(error.message);
      } else {
        console.error('Unknown error:', error);
        toast.error('Failed to activate user');
      }
    }
  }

  async function deactivateUser(userId: number) {
    if (!confirm('Are you sure you want to deactivate this user?')) {
      return;
    }

    try {
      const result = await UsersAPI.deactivateUser(userId);
      await loadUsers(); // Reload users after deactivation
      toast.success(result.message || 'User deactivated successfully');
    } catch (error) {
      console.error('Error deactivating user:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        toast.error(error.message);
      } else {
        console.error('Unknown error:', error);
        toast.error('Failed to deactivate user');
      }
    }
  }

  async function toggleUserStatus(userId: number) {
    try {
      const result = await UsersAPI.toggleUserStatus(userId);
      await loadUsers(); // Reload users after status change
      toast.success(result.message || 'User status updated successfully');
    } catch (error) {
      console.error('Error toggling user status:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to update user status');
    }
  }

  async function openChatHistory(user: User) {
    
    selectedUser = user;
    selectedUserChats = [];
    loadingUserChats = true;
    showUserChatsModal = true;

    try {
      // Load user chats using existing API
      const userChats = await AdminChatAPI.getUserChats(user.id);
      selectedUserChats = userChats.map(chat => ({
        id: chat.id,
        title: chat.title,
        created_at: chat.created_at,
        updated_at: chat.updated_at,
        user: chat.user,
        message_count: chat.message_count
      }));
    } catch (error) {
      console.error('Error loading user chats:', error);
      toast.error(`Failed to load chats for ${user.username}`);
    } finally {
      loadingUserChats = false;
    }
  }

  async function handleDeleteChat(event: CustomEvent) {
    const { chatId } = event.detail;
    if (selectedUser) {
      try {
        // Delete chat using existing API
        await AdminChatAPI.deleteUserChat(Number(chatId));
        selectedUserChats = selectedUserChats.filter(chat => chat.id !== Number(chatId));
        toast.success('Chat deleted successfully');
      } catch (error) {
        console.error('Error deleting chat:', error);
        toast.error('Failed to delete chat');
      }
    }
  }

  // Debug function to test the chat API
  async function debugChatAPI(user: User) {
    try {
      const result = await AdminChatAPI.debugUserChatsAPI(user.id);
      
      if (result.success) {
        toast.success(`Debug successful! Found ${result.userChatsCount} chats for user ${user.username}`);
      } else {
        toast.error(`Debug failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Debug function failed:', error);
      toast.error('Debug function failed');
    }
  }

  function formatTimeAgo(dateStr: string): string {
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    const diffMonths = Math.floor(diffDays / 30);

    if (diffSecs < 60) return 'a few seconds ago';
    if (diffMins < 60) return diffMins === 1 ? 'a minute ago' : `${diffMins} minutes ago`;
    if (diffHours < 24) return diffHours === 1 ? 'an hour ago' : `${diffHours} hours ago`;
    if (diffDays < 30) return diffDays === 1 ? 'a day ago' : `${diffDays} days ago`;
    return diffMonths === 1 ? 'a month ago' : `${diffMonths} months ago`;
  }

  function formatCreatedDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function formatChatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return (
      date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }) +
      ' ' +
      date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    );
  }

  function getRoleBadgeVariant(role: string) {
    switch (role) {
      case 'SUPERADMIN':
        return 'destructive';
      case 'STAFF':
        return 'default';
      case 'USER':
      default:
        return 'secondary';
    }
  }

  function getRoleDisplayName(role: string) {
    switch (role) {
      case 'SUPERADMIN':
        return 'Super Admin';
      case 'STAFF':
        return 'Staff';
      case 'USER':
      default:
        return 'User';
    }
  }

  function getInitials(username: string): string {
    return username.charAt(0).toUpperCase();
  }

  function logout() {
    logoutUser();
    goto('/login');
  }

  async function handleBulkUpload() {
    fileInput.click();
  }

  async function handleFileSelected(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;

    if (!file.name.match(/\.(csv|xlsx|xls)$/i)) {
      toast.error('Please select a CSV or Excel file');
      return;
    }

    bulkUploading = true;
    try {
      const result = await UsersAPI.bulkCreateUsers(file);
      
      if (result.summary.successfully_created > 0) {
        toast.success(`Successfully created ${result.summary.successfully_created} users`);
        await loadUsers(); // Reload users list
      }
      
      // Show detailed results in console or modal
      
      if (result.validation_errors.length > 0 || result.creation_errors.length > 0) {
        let errorMessage = `Validation errors: ${result.validation_errors.length}, Creation errors: ${result.creation_errors.length}`;
        toast.warning(errorMessage);
      }
      
    } catch (error) {
      console.error('Error bulk uploading users:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to upload users');
    } finally {
      bulkUploading = false;
      // Reset file input
      target.value = '';
    }
  }

  async function downloadTemplate() {
    try {
      const blob = await UsersAPI.downloadTemplate();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'user_template.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Template downloaded successfully');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Failed to download template');
    }
  }
</script>

<svelte:head>
  <title>Users - Mospi PS2</title>
</svelte:head>

<AuthGuard requireAdmin={true}>
<div class="w-full bg-background overflow-auto">
  <!-- Blue bar at the top -->
  <div class="h-5 bg-[#16306b]"></div>
  
  <!-- Top Bar with User Menu -->
    <!-- Top Bar with User Menu -->
  <header class="bg-white text-gray-900 sticky top-0 z-50 shadow-md">
    <!-- Desktop Layout -->
    <div class="hidden md:block w-full">
      <div class="w-full flex items-center py-4 relative">
        <!-- Logo Section - Absolute Left -->
        <div class="absolute left-0 flex items-center pl-4">
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
              AI-Enabled Intelligent Search Solution for Documents
            </h1>
          </div>
        </div>
        
        <!-- User Menu - Absolute Right -->
        <div class="absolute right-0 flex items-center pr-4">
          <DropdownMenu.Root>
            <DropdownMenu.Trigger class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-300 bg-white text-gray-900 hover:bg-gray-50 h-10 px-4 py-2">
              {$user?.name || $user?.email || 'User'}
            </DropdownMenu.Trigger>
            <DropdownMenu.Content align="end" class="z-50">
              <DropdownMenu.Label>Account</DropdownMenu.Label>
              <DropdownMenu.Separator />
              {#if $user}
                <div class="px-2 py-1 text-xs text-muted-foreground">Role: {$user.role}</div>
                <DropdownMenu.Separator />
              {/if}
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                onclick={() => goto('/c')}
              >
                <MessageSquare class="h-4 w-4" />
                Chat
              </button>
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                onclick={logout}
              >
                <LogOut class="h-4 w-4" />
                Logout
              </button>
            </DropdownMenu.Content>
          </DropdownMenu.Root>
        </div>
      </div>
    </div>
    
    <!-- Mobile Layout -->
    <div class="md:hidden w-full">
      <div class="flex flex-col space-y-4 py-4 px-4">
        <!-- Top row: Logo and User Menu -->
        <div class="flex justify-between items-center">
          <img 
            src="/MOSPILOGO.webp" 
            alt="MOSPI Logo" 
            class="h-12 w-auto" 
          />
          <DropdownMenu.Root>
            <DropdownMenu.Trigger class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-300 bg-white text-gray-900 hover:bg-gray-50 h-10 px-3 py-2">
              {($user?.name || $user?.email || 'User').substring(0, 10)}{($user?.name || $user?.email || 'User').length > 10 ? '...' : ''}
            </DropdownMenu.Trigger>
            <DropdownMenu.Content align="end" class="z-50">
              <DropdownMenu.Label>Account</DropdownMenu.Label>
              <DropdownMenu.Separator />
              {#if $user}
                <div class="px-2 py-1 text-xs text-muted-foreground">Role: {$user.role}</div>
                <DropdownMenu.Separator />
              {/if}
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                onclick={() => goto('/c')}
              >
                <MessageSquare class="h-4 w-4" />
                Chat
              </button>
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                onclick={logout}
              >
                <LogOut class="h-4 w-4" />
                Logout
              </button>
            </DropdownMenu.Content>
          </DropdownMenu.Root>
        </div>
        
        <!-- Bottom row: Text content -->
        <div class="text-center">
          <h1 class="text-lg font-bold text-[#16306b]">
            AI-Enabled Intelligent Search Solution for Documents
          </h1>
        </div>
      </div>
    </div>
  </header>
  
  <!-- Main Content with responsive padding -->
  <div class="p-4 md:p-6">
    <!-- Search and Action Bar -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
      <div class="flex flex-col md:flex-row md:items-center gap-4">
        <h1 class="text-xl md:text-2xl text-gray-900">Users</h1>
        <span class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium">
          {totalCount}
        </span>
      </div>
      
      <div class="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <!-- Search Bar -->
        <div class="relative flex-1 sm:flex-none sm:w-64">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder="Search users..."
            bind:value={searchQuery}
            oninput={handleSearchInput}
            class="pl-9 w-full"
          />
        </div>
        
        <!-- Action Buttons -->
        <div class="flex gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onclick={downloadTemplate}
            class="flex items-center gap-2 text-xs sm:text-sm"
          >
            <Download class="h-4 w-4" />
            <span class="hidden sm:inline">Template</span>
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onclick={handleBulkUpload}
            disabled={bulkUploading}
            class="flex items-center gap-2 text-xs sm:text-sm"
          >
            {#if bulkUploading}
              <Spinner size="sm" className="h-4 w-4" />
            {:else}
              <Upload class="h-4 w-4" />
            {/if}
            <span class="hidden sm:inline">Bulk Upload</span>
          </Button>
          
          <Button 
            size="sm"
            onclick={handleAddUserClick}
            class="flex items-center gap-2 text-xs sm:text-sm"
          >
            <UserPlus class="h-4 w-4" />
            <span class="hidden sm:inline">Add User</span>
          </Button>
        </div>
      </div>
    </div>

  <!-- Users Table Container -->
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">

      <!-- Users Table -->
      {#if loading}
        <div class="flex items-center justify-center p-8">
          <Spinner className="h-8 w-8" />
          <span class="ml-2">Loading users...</span>
        </div>
      {:else if errorMessage}
        <div class="text-center p-8 text-red-500">{errorMessage}</div>
      {:else if filteredUsers.length > 0}
        <div class="w-full overflow-x-auto">
          <Table.Root class="w-full">
          <Table.Header>
            <Table.Row class="border-b">
              <Table.Head class="w-[100px] text-xs font-medium text-muted-foreground uppercase tracking-wider">ROLE</Table.Head>
              <Table.Head class="text-xs font-medium text-muted-foreground uppercase tracking-wider">NAME</Table.Head>
              <Table.Head class="text-xs font-medium text-muted-foreground uppercase tracking-wider">EMAIL</Table.Head>
              <Table.Head class="text-xs font-medium text-muted-foreground uppercase tracking-wider">LAST ACTIVE</Table.Head>
              <Table.Head class="text-xs font-medium text-muted-foreground uppercase tracking-wider">CREATED AT</Table.Head>
              <Table.Head class="text-xs font-medium text-muted-foreground uppercase tracking-wider">ACTIONS</Table.Head>
            </Table.Row>
          </Table.Header>
          <Table.Body>
                {#each filteredUsers as user (user.id)}
                  <Table.Row class="border-b hover:bg-muted/50">
                    <Table.Cell class="py-3">
                      <div class="flex items-center gap-2">
                        <Badge variant={getRoleBadgeVariant(user.role)} class="text-xs">
                          {getRoleDisplayName(user.role)}
                        </Badge>
                        {#if !user.is_active}
                          <Badge variant="outline" class="text-xs text-red-600 border-red-200">
                            Inactive
                          </Badge>
                        {/if}
                      </div>
                    </Table.Cell>
                    <Table.Cell class="py-3">
                      <div class="flex items-center gap-3">
                        <Avatar.Root class="h-8 w-8">
                          <Avatar.Fallback>{getInitials(user.username)}</Avatar.Fallback>
                        </Avatar.Root>
                        <div class="flex flex-col">
                          <span class="font-medium">{user.username}</span>
                          {#if user.first_name || user.last_name}
                            <span class="text-xs text-muted-foreground">
                              {user.first_name} {user.last_name}
                            </span>
                          {/if}
                        </div>
                      </div>
                    </Table.Cell>
                    <Table.Cell class="py-3 text-muted-foreground">{user.email}</Table.Cell>
                    <Table.Cell class="py-3 text-muted-foreground">
                      {user.last_login ? formatTimeAgo(user.last_login) : 'Never'}
                    </Table.Cell>
                    <Table.Cell class="py-3 text-muted-foreground">
                      {formatCreatedDate(user.date_joined)}
                    </Table.Cell>
                    <Table.Cell class="py-3">
                      <div class="flex items-center gap-2">
                        <Button 
                          variant="ghost"
                          size="icon"
                          class="h-8 w-8"
                          onclick={() => openChatHistory(user)}
                        >
                          <MessageSquare class="h-4 w-4" />
                        </Button>
                        <DropdownMenu.Root>
                          <DropdownMenu.Trigger asChild>
                            <Button variant="ghost" size="icon" class="h-8 w-8">
                              <MoreHorizontal class="h-4 w-4" />
                              <span class="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenu.Trigger>
                          <DropdownMenu.Content align="end">
                            <DropdownMenu.Separator />
                            <DropdownMenu.Item onclick={() => toggleUserStatus(user.id)}>
                              <LogOut class="mr-2 h-4 w-4" />
                              {user.is_active ? 'Deactivate' : 'Activate'}
                            </DropdownMenu.Item>
                            <DropdownMenu.Separator />
                            <DropdownMenu.Item class="text-red-600" onclick={() => deleteUser(user.id)}>
                              <Trash2 class="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenu.Item>
                          </DropdownMenu.Content>
                        </DropdownMenu.Root>
                      </div>
                    </Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
          
          <!-- Pagination -->
          {#if totalPages > 1}
            <div class="flex items-center justify-between mt-6">
              <div class="text-sm text-muted-foreground">
                Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} users
              </div>
              <div class="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1}
                  onclick={() => {
                    currentPage = currentPage - 1;
                    loadUsers();
                  }}
                >
                  Previous
                </Button>
                
                <div class="flex items-center gap-1">
                  {#each Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const startPage = Math.max(1, currentPage - 2);
                    return startPage + i;
                  }).filter(page => page <= totalPages) as page}
                    <Button
                      variant={page === currentPage ? "default" : "outline"}
                      size="sm"
                      class="w-8 h-8 p-0"
                      onclick={() => {
                        currentPage = page;
                        loadUsers();
                      }}
                    >
                      {page}
                    </Button>
                  {/each}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages}
                  onclick={() => {
                    currentPage = currentPage + 1;
                    loadUsers();
                  }}
                >
                  Next
                </Button>
              </div>
            </div>
          {/if}
          {:else}
            <div class="text-center py-8 text-muted-foreground">
              No users found.
            </div>
          {/if}
    </div>
  </div>
</div>
</AuthGuard>

<!-- Modals -->
<AddUserModal bind:show={showAddUserModal} on:save={handleAddUser} />
<UserChatsModal 
  bind:show={showUserChatsModal} 
  user={selectedUser} 
  chats={selectedUserChats} 
  loading={loadingUserChats}
  on:deleteChat={handleDeleteChat}
/>

<!-- Hidden file input for bulk upload -->
<input
  type="file"
  bind:this={fileInput}
  onchange={handleFileSelected}
  accept=".csv,.xlsx,.xls"
  style="display: none;"
/>