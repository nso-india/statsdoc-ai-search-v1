<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import { formatDateToIST } from "$lib/utils";
  import { createEventDispatcher } from 'svelte';

  import Eye from "lucide-svelte/icons/eye";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";

  export let files = [];
  export let loading = false;
  export let selectedFiles = [];
  export let currentPage = 1;
  export let totalPages = 3;

  const dispatch = createEventDispatcher();

  function toggleSelect(id: number) {
    if (selectedFiles.includes(id)) {
      selectedFiles = selectedFiles.filter(fileId => fileId !== id);
    } else {
      selectedFiles = [...selectedFiles, id];
    }
    dispatch('select', { selectedFiles });
  }

  function toggleSelectAll(event: Event) {
    if ((event.target as HTMLInputElement)?.checked) {
      selectedFiles = files.map(file => file.id);
    } else {
      selectedFiles = [];
    }
    dispatch('select', { selectedFiles });
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      dispatch('pageChange', { page });
    }
  }

  function handleEdit(id: number) {
    dispatch('edit', { id });
  }

  function handleDelete(id: number) {
    dispatch('delete', { id });
  }

  function viewFormatted(id: number) {
    dispatch('viewFormatted', { id });
  }

  function viewOriginal(id: number) {
    dispatch('viewOriginal', { id });
  }
</script>

<Card.Root>
  <div class="p-1 overflow-x-auto">
    <Table.Root>
      <Table.Header>
        <Table.Row>
          <Table.Head class="w-[50px]">
            <input type="checkbox" on:change={toggleSelectAll} />
          </Table.Head>
          <Table.Head>File Name</Table.Head>
          <Table.Head>Date Created</Table.Head>
          <Table.Head>Approve Status</Table.Head>
          <Table.Head>Status</Table.Head>
          <Table.Head class="text-center">Actions</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {#if loading}
          <Table.Row>
            <Table.Cell colspan="6" class="text-center py-8">
              <div class="flex items-center justify-center">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
                Loading files...
              </div>
            </Table.Cell>
          </Table.Row>
        {:else if files.length === 0}
          <Table.Row>
            <Table.Cell colspan="6" class="text-center py-8 text-gray-500">
              No files uploaded yet. Upload your first file to get started.
            </Table.Cell>
          </Table.Row>
        {:else}
          {#each files as file}
            <Table.Row on:click|self|stopPropagation|preventDefault={() => handleRowClick(file, event)} class="cursor-pointer hover:bg-gray-50">
              <Table.Cell>
                <input 
                  type="checkbox" 
                  checked={selectedFiles.includes(file.id)} 
                  on:change={() => toggleSelect(file.id)}
                />
              </Table.Cell>
              <Table.Cell class="font-medium">
                {file.file_name}
              </Table.Cell>
              <Table.Cell>{formatDateToIST(file.uploaded_at)}</Table.Cell>
              <Table.Cell>{file.approve_status || 'Pending'}</Table.Cell>
              <Table.Cell>
                <Badge variant={
                  file.status === 'Success' ? "outline" : 
                  file.status === 'Failed' ? "secondary" : 
                  "outline"
                }>
                  {file.status}
                </Badge>
              </Table.Cell>
              <Table.Cell class="text-center">
                <div class="flex items-center justify-center space-x-2">
                  <!-- View button with dropdown -->
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger asChild let:builder>
                      <Button
                        builders={[builder]}
                        size="icon" 
                        variant="ghost" 
                        class="h-8 w-8"
                      >
                        <Eye class="h-4 w-4" />
                        <span class="sr-only">View</span>
                      </Button>
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Content align="end">
                      <DropdownMenu.Label>View options</DropdownMenu.Label>
                      <DropdownMenu.Item on:click={() => viewFormatted(file.id)}>
                        View Formatted
                      </DropdownMenu.Item>
                      <DropdownMenu.Item on:click={() => viewOriginal(file.id)}>
                        View Original
                      </DropdownMenu.Item>
                    </DropdownMenu.Content>
                  </DropdownMenu.Root>

                  <!-- Edit button -->
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    class="h-8 w-8"
                    on:click={() => handleEdit(file.id)}
                  >
                      <Pencil class="h-4 w-4" />
                      <span class="sr-only">Edit</span>
                  </Button>
                  
                  <!-- Delete button -->
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    class="h-8 w-8 text-red-500 hover:text-red-600"
                    on:click={() => handleDelete(file.id)}
                  >
                      <Trash2 class="h-4 w-4" />
                      <span class="sr-only">Delete</span>
                  </Button>
                </div>
              </Table.Cell>
            </Table.Row>
          {/each}
        {/if}
      </Table.Body>
    </Table.Root>
  </div>
  <Card.Footer class="flex flex-col sm:flex-row items-center justify-between gap-4">
    <div class="text-muted-foreground text-xs order-2 sm:order-1">
      Showing <strong>1-{files.length}</strong> of <strong>{files.length}</strong> files
    </div>

    <div class="flex items-center space-x-2 order-1 sm:order-2">
      <Button 
        variant="outline" 
        size="sm" 
        on:click={() => goToPage(currentPage - 1)}
        disabled={currentPage === 1}
      >
          Previous
      </Button>
      
      {#each Array(totalPages) as _, i}
        <Button 
          variant={currentPage === i + 1 ? "default" : "outline"} 
          size="sm"
          on:click={() => goToPage(i + 1)}
        >
            {i + 1}
        </Button>
      {/each}
      
      <Button 
        variant="outline" 
        size="sm" 
        on:click={() => goToPage(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
          Next
      </Button>
    </div>
  </Card.Footer>
</Card.Root>