<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  
  // UI Components
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import * as Table from '$lib/components/ui/table';
  import { Badge } from '$lib/components/ui/badge';
  import { Spinner } from '$lib/components/ui/loading';
  import * as AlertDialog from '$lib/components/ui/alert-dialog';
  import * as Tooltip from '$lib/components/ui/tooltip';
  
  // Icons
  import Plus from 'lucide-svelte/icons/plus';
  import ArrowLeft from 'lucide-svelte/icons/arrow-left';
  import Upload from 'lucide-svelte/icons/upload';
  import FileText from 'lucide-svelte/icons/file-text';
  import Search from 'lucide-svelte/icons/search';
  import Trash2 from 'lucide-svelte/icons/trash-2';
  import ExternalLink from 'lucide-svelte/icons/external-link';
  import AlertCircle from 'lucide-svelte/icons/alert-circle';
  
  // API and Components
  import { 
    getKnowledgeBase, 
    getKnowledgeBaseFiles, 
    uploadFilesToKnowledgeBase,
    deleteKnowledgeBaseFile,
    type KnowledgeBase,
    type UploadedFile
  } from '$lib/api/knowledgebase';
  import { openProtectedMedia } from '$lib/utils/mediaAccess';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import { user } from '$lib/stores';
  
  const knowledgeBaseId = $derived(parseInt($page.params.id));
  
  let knowledgeBase = $state<KnowledgeBase | null>(null);
  let files = $state<UploadedFile[]>([]);
  let filteredFiles = $state<UploadedFile[]>([]);
  let loading = $state(true);
  let uploading = $state(false);
  let searchQuery = $state('');
  let fileInput: HTMLInputElement;
  let deleting = $state(false);
  let fileToDelete = $state<UploadedFile | null>(null);
  let showDeleteDialog = $state(false);
  let isAdmin = $derived($user?.is_staff || $user?.is_superuser || false);
  
  // Pagination
  let currentPage = $state(1);
  let pageSize = $state(10);
  let totalPages = $derived(Math.ceil(filteredFiles.length / pageSize));
  let paginatedFiles = $derived(
    filteredFiles.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  );
  
  // Filter files based on search query (and hide FAILED files from normal users)
  $effect(() => {
    let baseFiles = isAdmin ? files : files.filter(file => file.status !== 'FAILED');
    if (searchQuery.trim() === '') {
      filteredFiles = baseFiles;
    } else {
      const query = searchQuery.toLowerCase();
      filteredFiles = baseFiles.filter(file => 
        file.file_name.toLowerCase().includes(query)
      );
    }
    // Reset to first page when search changes
    currentPage = 1;
  });
  
  async function loadKnowledgeBase() {
    try {
      knowledgeBase = await getKnowledgeBase(knowledgeBaseId);
    } catch (error) {
      console.error('Error loading knowledge base:', error);
      toast.error('Failed to load knowledge base');
      goto('/knowledge');
    }
  }
  
  async function loadFiles() {
    loading = true;
    try {
      files = await getKnowledgeBaseFiles(knowledgeBaseId);
    } catch (error) {
      console.error('Error loading files:', error);
      toast.error('Failed to load files');
    } finally {
      loading = false;
    }
  }
  
  async function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    const selectedFiles = input.files;
    
    if (!selectedFiles || selectedFiles.length === 0) {
      return;
    }
    
    uploading = true;
    try {
      const filesArray = Array.from(selectedFiles);
      
      // Validate each file before upload
      const invalidFiles: string[] = [];
      const validFiles: File[] = [];
      
      for (const file of filesArray) {
        // Check for double extensions (security check)
        const fileName = file.name.toLowerCase();
        const parts = fileName.split('.');
        
        // Check file extension
        const allowedExtensions = [
          '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
          '.txt', '.csv', '.json', '.xml', '.html', '.htm',
          '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
          '.zip', '.tar', '.gz'
        ];
        
        const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        
        if (!hasValidExtension) {
          invalidFiles.push(`${file.name}: Invalid file type. Allowed types: ${allowedExtensions.join(', ')}`);
          continue;
        }
        
        // Check for double extensions (security)
        if (parts.length > 2) {
          const dangerousExts = ['.exe', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.js'];
          let isDangerous = false;
          for (let i = 1; i < parts.length - 1; i++) {
            if (dangerousExts.includes('.' + parts[i])) {
              invalidFiles.push(`${file.name}: Double extension detected. This is not allowed for security reasons.`);
              isDangerous = true;
              break;
            }
          }
          if (isDangerous) continue;
        }
        
        // Check file size (100MB limit)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
          invalidFiles.push(`${file.name}: File size exceeds 100MB limit`);
          continue;
        }
        
        validFiles.push(file);
      }
      
      // Show errors for invalid files
      if (invalidFiles.length > 0) {
        for (const error of invalidFiles) {
          toast.error(error);
        }
      }
      
      // Upload valid files
      if (validFiles.length === 0) {
        toast.error('No valid files to upload');
        return;
      }
      
      const uploadedFiles = await uploadFilesToKnowledgeBase(knowledgeBaseId, validFiles);
      
      // Add uploaded files to the list
      files = [...uploadedFiles, ...files];
      
      toast.success(`Successfully uploaded ${uploadedFiles.length} file(s)`);
      
      // Reload knowledge base to update file count
      await loadKnowledgeBase();
    } catch (error) {
      console.error('Error uploading files:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload files';
      toast.error(errorMessage);
    } finally {
      uploading = false;
      // Reset file input
      if (fileInput) {
        fileInput.value = '';
      }
    }
  }
  
  function triggerFileInput() {
    fileInput?.click();
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
  
  function getStatusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
    switch (status) {
      case 'completed':
        return 'default';
      case 'processing':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  }
  
  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
    }
  }
  
  function openDeleteDialog(file: UploadedFile) {
    fileToDelete = file;
    showDeleteDialog = true;
  }
  
  async function confirmDelete() {
    if (!fileToDelete) return;
    
    deleting = true;
    try {
      await deleteKnowledgeBaseFile(fileToDelete.id);
      
      // Remove file from local state
      files = files.filter(f => f.id !== fileToDelete.id);
      
      toast.success(`File "${fileToDelete.file_name}" deleted successfully`);
      
      // Reload knowledge base to update file count
      await loadKnowledgeBase();
    } catch (error) {
      console.error('Error deleting file:', error);
      toast.error('Failed to delete file');
    } finally {
      deleting = false;
      showDeleteDialog = false;
      fileToDelete = null;
    }
  }
  
  function cancelDelete() {
    showDeleteDialog = false;
    fileToDelete = null;
  }
  
  onMount(async () => {
    await loadKnowledgeBase();
    await loadFiles();
  });
</script>

<AuthGuard>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="border-b bg-white dark:bg-gray-900 flex-shrink-0">
      <div class="px-6 py-4">
        <div class="flex items-center gap-4 mb-4">
          <Button 
            variant="ghost" 
            size="icon"
            onclick={() => goto('/knowledge')}
          >
            <ArrowLeft class="size-4" />
          </Button>
          <div class="flex-1">
            <h1 class="text-2xl font-bold tracking-tight">
              {knowledgeBase?.name || 'Loading...'}
            </h1>
            {#if knowledgeBase?.description}
              <p class="text-sm text-muted-foreground mt-1">
                {knowledgeBase.description}
              </p>
            {/if}
          </div>
          {#if isAdmin}
          <input
            type="file"
            bind:this={fileInput}
            onchange={handleFileUpload}
            multiple
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
            class="hidden"
          />
          <Button 
            onclick={triggerFileInput}
            disabled={uploading}
          >
            {#if uploading}
              <Spinner class="size-4 mr-2" />
              Uploading...
            {:else}
              <Plus class="size-4 mr-2" />
              Add Files
            {/if}
          </Button>
          {/if}
        </div>
        
        <!-- Search Bar -->
        <div class="relative max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search files..."
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
      {:else if filteredFiles.length === 0}
        <div class="flex flex-col items-center justify-center h-64 text-center">
          <Upload class="size-16 text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium mb-2">
            {searchQuery ? 'No files found' : 'No files uploaded yet'}
          </h3>
          <p class="text-sm text-muted-foreground mb-4">
            {searchQuery 
              ? 'Try adjusting your search query' 
              : 'Upload files to add them to this knowledge base'}
          </p>
          {#if !searchQuery && isAdmin}
            <Button onclick={triggerFileInput}>
              <Plus class="size-4 mr-2" />
              Add Files
            </Button>
          {/if}
        </div>
      {:else}
        <div class="bg-white dark:bg-gray-900 rounded-lg border">
          <Table.Root>
            <Table.Header>
              <Table.Row>
                <Table.Head class="w-[45%]">File Name</Table.Head>
                {#if isAdmin}
                <Table.Head>Status</Table.Head>
                {/if}
                <Table.Head>Uploaded At</Table.Head>
                {#if isAdmin}
                <Table.Head class="w-[100px]">Actions</Table.Head>
                {/if}
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {#each paginatedFiles as file (file.id)}
                <Table.Row>
                  <Table.Cell class="font-medium">
                    <div class="flex items-center gap-2">
                      <FileText class="size-4 text-muted-foreground" />
                      {#if file.file_url}
                        <button
                          type="button"
                          onclick={() => {
                            openProtectedMedia(file.file_url);
                          }}
                          class="truncate text-left hover:text-blue-600 dark:hover:text-blue-400 hover:underline transition-colors flex items-center gap-1.5 flex-1 min-w-0"
                        >
                          <span class="truncate">{file.file_name}</span>
                          <ExternalLink class="size-3 flex-shrink-0 opacity-60" />
                        </button>
                      {:else}
                        <span class="truncate text-muted-foreground">{file.file_name}</span>
                      {/if}
                    </div>
                  </Table.Cell>
                  {#if isAdmin}
                  <Table.Cell>
                    <div class="flex items-center gap-2">
                      <Badge variant={getStatusBadgeVariant(file.status)}>
                        {file.status}
                      </Badge>
                      {#if file.status === 'FAILED' && file.other_info}
                        <Tooltip.Root>
                          <Tooltip.Trigger>
                            <AlertCircle class="size-4 text-destructive cursor-help" />
                          </Tooltip.Trigger>
                          <Tooltip.Content class="max-w-md">
                            <div class="space-y-1">
                              {#if file.other_info.message}
                                <p class="text-sm">{file.other_info.message}</p>
                              {:else if file.other_info.error}
                                <p class="text-sm font-medium">Error:</p>
                                <p class="text-sm">{file.other_info.error}</p>
                              {/if}
                              {#if file.other_info.json_size_mb}
                                <p class="text-xs text-muted-foreground mt-2">
                                  File size: {file.other_info.json_size_mb}MB (max: {file.other_info.max_size_mb}MB)
                                </p>
                              {/if}
                            </div>
                          </Tooltip.Content>
                        </Tooltip.Root>
                      {/if}
                    </div>
                  </Table.Cell>
                  {/if}
                  <Table.Cell class="text-sm text-muted-foreground">
                    {formatDate(file.uploaded_at)}
                  </Table.Cell>
                  {#if isAdmin}
                  <Table.Cell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onclick={() => openDeleteDialog(file)}
                      disabled={deleting}
                    >
                      <Trash2 class="size-4 text-destructive" />
                    </Button>
                  </Table.Cell>
                  {/if}
                </Table.Row>
              {/each}
            </Table.Body>
          </Table.Root>
          
          <!-- Pagination -->
          {#if totalPages > 1}
            <div class="flex items-center justify-between px-4 py-3 border-t">
              <div class="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredFiles.length)} of {filteredFiles.length} files
              </div>
              <div class="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onclick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <div class="flex items-center gap-1">
                  {#each Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    // Show pages around current page
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return pageNum;
                  }) as pageNum (pageNum)}
                    <Button
                      variant={currentPage === pageNum ? 'default' : 'outline'}
                      size="sm"
                      onclick={() => goToPage(pageNum)}
                      class="min-w-9"
                    >
                      {pageNum}
                    </Button>
                  {/each}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onclick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Delete Confirmation Dialog -->
  <AlertDialog.Root bind:open={showDeleteDialog}>
    <AlertDialog.Content>
      <AlertDialog.Header>
        <AlertDialog.Title>Delete File</AlertDialog.Title>
        <AlertDialog.Description>
          Are you sure you want to delete "{fileToDelete?.file_name}"? This will also remove all associated vector data from the knowledge base. This action cannot be undone.
        </AlertDialog.Description>
      </AlertDialog.Header>
      <AlertDialog.Footer>
        <AlertDialog.Cancel onclick={cancelDelete} disabled={deleting}>Cancel</AlertDialog.Cancel>
        <AlertDialog.Action onclick={confirmDelete} disabled={deleting}>
          {#if deleting}
            <Spinner class="size-4 mr-2" />
            Deleting...
          {:else}
            Delete
          {/if}
        </AlertDialog.Action>
      </AlertDialog.Footer>
    </AlertDialog.Content>
  </AlertDialog.Root>
</AuthGuard>
