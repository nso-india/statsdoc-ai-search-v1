<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import * as Sheet from "$lib/components/ui/sheet";
  import { Button } from "$lib/components/ui/button";
  import { toast } from 'svelte-sonner';
  
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  export let open: boolean = false;
  export let loading: boolean = false;
  export let selectedFiles: any[] = [];

  async function handleConfirm() {
    try {
      loading = true;
      dispatch('confirm', { files: selectedFiles });
    } catch (error) {
      toast.error('Failed to delete files');
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    open = false;
    dispatch('cancel');
  }
</script>

<Sheet.Root bind:open>
  <Sheet.Content side="right" class="sm:max-w-[425px]">
    <Sheet.Header>
      <Sheet.Title>Delete Files</Sheet.Title>
      <Sheet.Description>
        Are you sure you want to delete {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}? 
        This action cannot be undone.
      </Sheet.Description>
    </Sheet.Header>
    
    {#if selectedFiles.length > 0}
      <div class="max-h-40 overflow-y-auto border rounded-md p-2 bg-muted/50 my-4">
        {#each selectedFiles as file}
          <div class="text-sm py-1 px-2 rounded hover:bg-muted">
            {file.file_name}
          </div>
        {/each}
      </div>
    {/if}

    <Sheet.Footer class="flex gap-2 pt-4">
      <Button variant="outline" onclick={handleCancel} disabled={loading} class="flex-1">
          Cancel
      </Button>
      <Button variant="destructive" onclick={handleConfirm} disabled={loading} class="flex-1">
          {#if loading}
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          {/if}
          Delete
      </Button>
    </Sheet.Footer>
  </Sheet.Content>
</Sheet.Root>