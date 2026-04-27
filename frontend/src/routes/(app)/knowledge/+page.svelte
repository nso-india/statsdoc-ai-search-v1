<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  
  // UI Components
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import * as Card from '$lib/components/ui/card';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import { Spinner } from '$lib/components/ui/loading';
  
  // Icons
  import Plus from 'lucide-svelte/icons/plus';
  import Search from 'lucide-svelte/icons/search';
  import MoreVertical from 'lucide-svelte/icons/more-vertical';
  import Trash2 from 'lucide-svelte/icons/trash-2';
  import Edit from 'lucide-svelte/icons/edit';
  import FolderOpen from 'lucide-svelte/icons/folder-open';
  import Database from 'lucide-svelte/icons/database';
  
  // API and Components
  import { getKnowledgeBases, deleteKnowledgeBase, type KnowledgeBase } from '$lib/api/knowledgebase';
  import CreateKnowledgeBaseModal from '$lib/components/knowledge/CreateKnowledgeBaseModal.svelte';
  import EditKnowledgeBaseModal from '$lib/components/knowledge/EditKnowledgeBaseModal.svelte';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import { user } from '$lib/stores';
  
  let knowledgeBases = $state<KnowledgeBase[]>([]);
  let filteredKnowledgeBases = $state<KnowledgeBase[]>([]);
  let loading = $state(true);
  let searchQuery = $state('');
  let showCreateModal = $state(false);
  let showEditModal = $state(false);
  let selectedKnowledgeBase = $state<KnowledgeBase | null>(null);
  let isAdmin = $derived($user?.is_staff || $user?.is_superuser || false);
  
  // Filter knowledge bases based on search query
  $effect(() => {
    if (searchQuery.trim() === '') {
      filteredKnowledgeBases = knowledgeBases;
    } else {
      const query = searchQuery.toLowerCase();
      filteredKnowledgeBases = knowledgeBases.filter(kb => 
        kb.name.toLowerCase().includes(query) || 
        kb.description.toLowerCase().includes(query)
      );
    }
  });
  
  async function loadKnowledgeBases() {
    loading = true;
    try {
      knowledgeBases = await getKnowledgeBases();
    } catch (error) {
      console.error('Error loading knowledge bases:', error);
      toast.error('Failed to load knowledge bases');
    } finally {
      loading = false;
    }
  }
  
  async function handleDelete(id: number, name: string) {
    if (!confirm(`Are you sure you want to delete "${name}"? This will also remove all associated files.`)) {
      return;
    }
    
    try {
      await deleteKnowledgeBase(id);
      knowledgeBases = knowledgeBases.filter(kb => kb.id !== id);
      toast.success('Knowledge base deleted successfully');
    } catch (error) {
      console.error('Error deleting knowledge base:', error);
      toast.error('Failed to delete knowledge base');
    }
  }
  
  function handleKnowledgeBaseClick(id: number) {
    goto(`/knowledge/${id}`);
  }
  
  function handleCreateSuccess() {
    showCreateModal = false;
    loadKnowledgeBases();
  }
  
  function handleEdit(kb: KnowledgeBase) {
    selectedKnowledgeBase = kb;
    showEditModal = true;
  }
  
  function handleEditSuccess() {
    showEditModal = false;
    selectedKnowledgeBase = null;
    loadKnowledgeBases();
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  onMount(() => {
    loadKnowledgeBases();
  });
</script>

<AuthGuard>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="border-b bg-white dark:bg-gray-900 flex-shrink-0">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h1 class="text-2xl font-bold tracking-tight">Knowledge Bases</h1>
            <p class="text-sm text-muted-foreground mt-1">
              Manage your organization's knowledge repositories
            </p>
          </div>
          {#if isAdmin}
          <Button onclick={() => showCreateModal = true}>
            <Plus class="size-4 mr-2" />
            Create Knowledge Base
          </Button>
          {/if}
        </div>
        
        <!-- Search Bar -->
        <div class="relative max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search knowledge bases..."
            class="pl-10"
            bind:value={searchQuery}
          />
        </div>
      </div>
    </div>
    
    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 min-h-0">
      {#if loading}
        <div class="flex items-center justify-center h-64">
          <Spinner class="size-8" />
        </div>
      {:else if filteredKnowledgeBases.length === 0}
        <div class="flex flex-col items-center justify-center h-64 text-center">
          <Database class="size-16 text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium mb-2">
            {searchQuery ? 'No knowledge bases found' : 'No knowledge bases yet'}
          </h3>
          <p class="text-sm text-muted-foreground mb-4">
            {searchQuery 
              ? 'Try adjusting your search query' 
              : 'Create your first knowledge base to get started'}
          </p>
          {#if !searchQuery}
            <Button onclick={() => showCreateModal = true}>
              <Plus class="size-4 mr-2" />
              Create Knowledge Base
            </Button>
          {/if}
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each filteredKnowledgeBases as kb (kb.id)}
            <Card.Root 
              class="group hover:shadow-lg transition-all duration-200 cursor-pointer relative"
            >
              <Card.Header class="pb-3">
                <div class="flex items-start justify-between gap-2">
                  <div 
                    class="flex-1 min-w-0"
                    onclick={() => handleKnowledgeBaseClick(kb.id)}
                  >
                    <Card.Title class="text-lg truncate">
                      {kb.name}
                    </Card.Title>
                  </div>
                  {#if isAdmin}
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger asChild>
                      {#snippet child({ props })}
                        <Button 
                          {...props}
                          variant="ghost" 
                          size="icon"
                          class="size-8 opacity-0 group-hover:opacity-100 transition-opacity"
                          onclick={(e: MouseEvent) => e.stopPropagation()}
                        >
                          <MoreVertical class="size-4" />
                        </Button>
                      {/snippet}
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Content align="end">
                      <DropdownMenu.Item 
                        class="cursor-pointer"
                        onclick={(e: MouseEvent) => {
                          e.stopPropagation();
                          handleEdit(kb);
                        }}
                      >
                        <Edit class="size-4 mr-2" />
                        Rename
                      </DropdownMenu.Item>
                      <DropdownMenu.Item 
                        class="text-red-600 focus:text-red-600 cursor-pointer"
                        onclick={(e: MouseEvent) => {
                          e.stopPropagation();
                          handleDelete(kb.id, kb.name);
                        }}
                      >
                        <Trash2 class="size-4 mr-2" />
                        Delete
                      </DropdownMenu.Item>
                    </DropdownMenu.Content>
                  </DropdownMenu.Root>
                  {/if}
                </div>
                <Card.Description class="line-clamp-2 mt-1.5">
                  {kb.description || 'No description provided'}
                </Card.Description>
              </Card.Header>
              <Card.Content 
                class="pb-4"
                onclick={() => handleKnowledgeBaseClick(kb.id)}
              >
                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center gap-2 text-muted-foreground">
                    <FolderOpen class="size-4" />
                    <span>{kb.files_count} {kb.files_count === 1 ? 'file' : 'files'}</span>
                  </div>
                  <div class="text-xs text-muted-foreground">
                    {formatDate(kb.created_at)}
                  </div>
                </div>
              </Card.Content>
            </Card.Root>
          {/each}
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Create Modal -->
  <CreateKnowledgeBaseModal 
    bind:show={showCreateModal}
    onSuccess={handleCreateSuccess}
  />
  
  <!-- Edit Modal -->
  <EditKnowledgeBaseModal 
    bind:show={showEditModal}
    bind:knowledgeBase={selectedKnowledgeBase}
    onSuccess={handleEditSuccess}
  />
</AuthGuard>
