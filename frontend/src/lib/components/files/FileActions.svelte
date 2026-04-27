<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import Download from "lucide-svelte/icons/download";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import FileCheck from "lucide-svelte/icons/file-check";
  
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  export let selectedFiles: any[] = [];
  export let totalFiles: number = 0;

  function handleBulkDelete() {
    if (selectedFiles.length === 0) return;
    dispatch('bulkDelete', { files: selectedFiles });
  }

  function handleBulkDownload() {
    if (selectedFiles.length === 0) return;
    dispatch('bulkDownload', { files: selectedFiles });
  }

  function handleBulkApprove() {
    if (selectedFiles.length === 0) return;
    dispatch('bulkApprove', { files: selectedFiles });
  }

  function handleExportAll() {
    dispatch('exportAll');
  }

  $: hasSelection = selectedFiles.length > 0;
</script>

<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
  <!-- File Statistics -->
  <div class="flex items-center gap-4">
    <div class="text-sm text-muted-foreground">
      Total: <span class="font-medium">{totalFiles}</span> files
    </div>
    {#if hasSelection}
      <Badge variant="secondary">
        {selectedFiles.length} selected
      </Badge>
    {/if}
  </div>

  <!-- Action Buttons -->
  <div class="flex items-center gap-2">
    {#if hasSelection}
      <!-- Bulk Actions -->
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild let:builder>
          <Button builders={[builder]} variant="outline" size="sm">
            Bulk Actions
          </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end">
          <DropdownMenu.Label>Bulk Actions</DropdownMenu.Label>
          <DropdownMenu.Separator />
          
          <DropdownMenu.Item on:click={handleBulkDownload}>
            <Download class="h-4 w-4 mr-2" />
            Download Selected
          </DropdownMenu.Item>
          
          <DropdownMenu.Item on:click={handleBulkApprove}>
            <FileCheck class="h-4 w-4 mr-2" />
            Approve Selected
          </DropdownMenu.Item>
          
          <DropdownMenu.Separator />
          
          <DropdownMenu.Item 
            class="text-destructive focus:text-destructive"
            on:click={handleBulkDelete}
          >
            <Trash2 class="h-4 w-4 mr-2" />
            Delete Selected
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    {/if}

    <!-- Export All -->
    <Button variant="outline" size="sm" onclick={handleExportAll}>
        <Download class="h-4 w-4 mr-2" />
        Export All
    </Button>
  </div>
</div>