<script lang="ts">
  import NavUser from "./nav-user.svelte";
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import EditIcon from "@lucide/svelte/icons/edit";
  import FileTextIcon from "@lucide/svelte/icons/file-text";
  import MoreVertical from "@lucide/svelte/icons/more-vertical";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Database from "@lucide/svelte/icons/database";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import ClipboardList from "@lucide/svelte/icons/clipboard-list";
  import FeedbackFormDialog from "./FeedbackFormDialog.svelte";
  import { newChatApi } from "$lib/api/newchat";
  import { user } from "$lib/stores";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { browser } from "$app/environment";
  import type { ComponentProps } from "svelte";
  import { onMount, onDestroy } from "svelte";
  import { toast } from "svelte-sonner";
  
  let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();

  // Conversation state - adapted for Django backend
  interface ChatItem {
    id: number;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    last_message?: {
      id: number;
      role: string;
      content: any;
      created_at: string;
    } | null;
  }

  let conversations: ChatItem[] = $state([]);
  let loading = $state(true);
  let error = $state('');
  let feedbackOpen = $state(false);

  // Load conversations from Django API
  async function loadConversations() {
    loading = true;
    try {
      const chats = await newChatApi.getChats();
      conversations = chats;
      error = '';
    } catch (err) {
      console.error('Failed to load conversations:', err);
      error = 'Failed to load conversations';
      conversations = [];
    } finally {
      loading = false;
    }
  }

  // Format date for display
  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays-1}d ago`;
    
    return date.toLocaleDateString();
  }

  // Get display title
  function getDisplayTitle(conversation: ChatItem): string {
    return conversation.title || 'New Conversation';
  }

  // Get preview text (no longer used in UI, but keeping for potential future use)
  function getPreviewText(conversation: ChatItem): string {
    if (conversation.last_message) {
      // Handle both string and object content
      let content = '';
      if (typeof conversation.last_message.content === 'string') {
        content = conversation.last_message.content;
      } else if (conversation.last_message.content?.message || conversation.last_message.content?.content) {
        content = conversation.last_message.content.message || conversation.last_message.content.content;
      } else {
        content = JSON.stringify(conversation.last_message.content);
      }
      return content.length > 60 ? content.substring(0, 60) + '...' : content;
    }
    return `${conversation.message_count} messages`;
  }

  // Delete chat function
  async function deleteChat(chatId: number, event: Event) {
    event.preventDefault();
    event.stopPropagation();

    try {
      await newChatApi.deleteChat(chatId);
      
      // Remove from local conversations list
      conversations = conversations.filter(c => c.id !== chatId);
      
      // If we're currently viewing this chat, redirect to main chat page
      if ($page.params.id && parseInt($page.params.id) === chatId) {
        await goto('/c');
      }
      
      toast.success('Chat deleted successfully');
    } catch (error) {
      console.error('Error deleting chat:', error);
      toast.error('Failed to delete chat');
    }
  }

  // Lifecycle
  onMount(() => {
    loadConversations();
  });

  // Track last pathname to refetch conversations when navigating
  let lastPathname = '';
  
  // Refetch conversations when navigating to chat pages
  $effect(() => {
    if (browser && $page.url.pathname !== lastPathname) {
      const currentPath = $page.url.pathname;
      
      // Refetch conversations when:
      // 1. Going to /c (new chat) 
      // 2. Going to /c/id (specific chat)
      if (currentPath === '/c' || currentPath.match(/^\/c\/\d+$/)) {
        console.log('Navigating to chat page, refetching conversations:', currentPath);
        setTimeout(loadConversations, 300);
      }
      
      lastPathname = currentPath;
    }
  });
</script>

<style>
  /* Custom sidebar background color */
  :global(.sidebar-root) {
    background-color: #fafafa !important;
  }
  
  /* Custom highlighted/active item background */
  :global(.sidebar-active-item) {
    background-color: #dbe5ff !important;
  }
  
  /* Hover state for sidebar items */
  :global(.sidebar-item:hover) {
    background-color: #f0f0f0 !important;
  }
</style>

<Sidebar.Root bind:ref variant="inset" class="sidebar-root z-40" {...restProps}>
  <Sidebar.Content class="px-1 flex flex-col h-full">
    <!-- Logo Section -->
    <div class="mb-3 flex-shrink-0 flex justify-start items-center px-3 py-2 gap-2">
      <img 
        src="/MOSPI-Logo.svg" 
        alt="MOSPI Logo" 
        class="h-12 w-auto" 
      />
      <img 
        src="/MOSPILOGO.webp" 
        alt="MOSPI Logo" 
        class="h-12 w-auto" 
      />
    </div>
    
    <!-- Navigation - Fixed at top -->
    <div class="mb-6 flex-shrink-0">
      <nav class="space-y-1">
        <a 
          href="/c"
          class="flex items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors {$page.url.pathname === '/c' && !$page.params.id ? 'sidebar-active-item' : ''}"
        >
          <EditIcon class="size-4" />
          <span>New chat</span>
        </a>
        {#if $user}
        <a 
          href="/knowledge"
          class="flex items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors {$page.url.pathname.startsWith('/knowledge') ? 'sidebar-active-item' : ''}"
        >
          <Database class="size-4" />
          <span>Knowledge</span>
        </a>
        <button
          type="button"
          onclick={() => (feedbackOpen = true)}
          class="flex w-full items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors text-left"
        >
          <MessageSquare class="size-4" />
          <span>Feedback</span>
        </button>
        {/if}
        {#if $user && ($user.is_staff || $user.is_superuser)}
        <a 
          href="/analytics"
          class="flex items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors {$page.url.pathname.startsWith('/analytics') ? 'sidebar-active-item' : ''}"
        >
          <FileTextIcon class="size-4" />
          <span>Analytics</span>
        </a>
        <a 
          href="/admin-reports"
          class="flex items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors {$page.url.pathname.startsWith('/admin-reports') || $page.url.pathname.startsWith('/feedback-reports') ? 'sidebar-active-item' : ''}"
        >
          <ClipboardList class="size-4" />
          <span>Admin Reports</span>
        </a>
        <a 
          href="/settings"
          class="flex items-center gap-3 px-3 py-2 text-sm font-medium sidebar-item rounded-md transition-colors {$page.url.pathname.startsWith('/settings') ? 'sidebar-active-item' : ''}"
        >
          <FileTextIcon class="size-4" />
          <span>Settings</span>
        </a>
        {/if}
      </nav>
    </div>
    
    <!-- Chat List - Scrollable -->
    <div class="flex-1 min-h-0 flex flex-col">
      <div class="mb-4 flex-shrink-0">
        <h3 class="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">Chats</h3>
      </div>
      <div class="flex-1 overflow-y-auto">
        {#if loading}
          <div class="px-3 py-2 text-sm text-muted-foreground">Loading conversations...</div>
        {:else if error}
          <div class="px-3 py-2 text-sm text-red-500">{error}</div>
        {:else if conversations.length === 0}
          <div class="px-3 py-2 text-sm text-muted-foreground">No conversations yet</div>
        {:else}
          <div class="space-y-1">
            {#each conversations as conversation (conversation.id)}
              <div class="group relative">
                <!-- Chat item with three-dot menu -->
                <div class="flex items-center justify-between px-3 py-2 text-sm sidebar-item rounded-md transition-colors min-w-0 hover:bg-sidebar-accent {$page.params.id && parseInt($page.params.id) === conversation.id ? 'sidebar-active-item' : ''}">
                  <a 
                    href="/c/{conversation.id}" 
                    class="truncate font-medium flex-1 min-w-0 text-inherit no-underline"
                  >
                    {getDisplayTitle(conversation)}
                  </a>
                  
                  <!-- Three-dot menu -->
                  <div class="ml-2">
                    <DropdownMenu.Root>
                      <DropdownMenu.Trigger asChild>
                        {#snippet child({ props })}
                          <button 
                            {...props}
                            class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                            onclick={(e) => e.preventDefault()}
                            aria-label="Chat options"
                          >
                            <MoreVertical class="size-4" />
                          </button>
                        {/snippet}
                      </DropdownMenu.Trigger>
                      <DropdownMenu.Content align="end" class="w-48">
                        <DropdownMenu.Item 
                          class="text-red-600 focus:text-red-600 cursor-pointer"
                          onclick={(e) => deleteChat(conversation.id, e)}
                        >
                          <Trash2 class="size-4 mr-2" />
                          Delete chat
                        </DropdownMenu.Item>
                      </DropdownMenu.Content>
                    </DropdownMenu.Root>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </Sidebar.Content>
  <Sidebar.Footer>
    {#if $user}
      <NavUser user={$user} />
    {/if}
  </Sidebar.Footer>
</Sidebar.Root>

<FeedbackFormDialog bind:open={feedbackOpen} />