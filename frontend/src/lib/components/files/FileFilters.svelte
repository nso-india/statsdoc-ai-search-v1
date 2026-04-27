<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import Search from "lucide-svelte/icons/search";
  import ListFilter from "lucide-svelte/icons/list-filter";
  
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  export let searchQuery: string = '';
  export let selectedStatus: string = '';
  export let selectedApprovalStatus: string = '';

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'Success', label: 'Success' },
    { value: 'Failed', label: 'Failed' },
    { value: 'Uploading', label: 'Uploading' },
    { value: 'Processing', label: 'Processing' }
  ];

  const approvalStatusOptions = [
    { value: '', label: 'All Approval Status' },
    { value: 'Approved', label: 'Approved' },
    { value: 'Pending', label: 'Pending' },
    { value: 'Rejected', label: 'Rejected' }
  ];

  function handleSearchChange(event: Event) {
    searchQuery = (event.target as HTMLInputElement).value;
    dispatch('searchChange', { query: searchQuery });
  }

  function handleStatusFilter(status: string) {
    selectedStatus = status;
    dispatch('statusFilter', { status });
  }

  function handleApprovalFilter(approvalStatus: string) {
    selectedApprovalStatus = approvalStatus;
    dispatch('approvalFilter', { approvalStatus });
  }

  function clearFilters() {
    searchQuery = '';
    selectedStatus = '';
    selectedApprovalStatus = '';
    dispatch('clearFilters');
  }
</script>

<div class="flex flex-col md:flex-row gap-4 mb-6">
  <!-- Search Input -->
  <div class="relative flex-1">
    <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
    <Input 
      placeholder="Search files..." 
      value={searchQuery}
      on:input={handleSearchChange}
      class="pl-10"
    />
  </div>

  <!-- Status Filter -->
  <DropdownMenu.Root>
    <DropdownMenu.Trigger asChild let:builder>
      <Button builders={[builder]} variant="outline" size="sm" class="min-w-[140px]">
        <ListFilter class="h-4 w-4 mr-2" />
        {selectedStatus || 'Status'}
      </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="start">
      <DropdownMenu.Label>Filter by Status</DropdownMenu.Label>
      <DropdownMenu.Separator />
      {#each statusOptions as option}
        <DropdownMenu.CheckboxItem 
          checked={selectedStatus === option.value}
          on:click={() => handleStatusFilter(option.value)}
        >
          {option.label}
        </DropdownMenu.CheckboxItem>
      {/each}
    </DropdownMenu.Content>
  </DropdownMenu.Root>

  <!-- Approval Status Filter -->
  <DropdownMenu.Root>
    <DropdownMenu.Trigger asChild let:builder>
      <Button builders={[builder]} variant="outline" size="sm" class="min-w-[140px]">
        <ListFilter class="h-4 w-4 mr-2" />
        {selectedApprovalStatus || 'Approval'}
      </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="start">
      <DropdownMenu.Label>Filter by Approval</DropdownMenu.Label>
      <DropdownMenu.Separator />
      {#each approvalStatusOptions as option}
        <DropdownMenu.CheckboxItem 
          checked={selectedApprovalStatus === option.value}
          on:click={() => handleApprovalFilter(option.value)}
        >
          {option.label}
        </DropdownMenu.CheckboxItem>
      {/each}
    </DropdownMenu.Content>
  </DropdownMenu.Root>

  <!-- Clear Filters -->
  {#if searchQuery || selectedStatus || selectedApprovalStatus}
    <Button variant="ghost" size="sm" onclick={clearFilters}>
        Clear Filters
    </Button>
  {/if}
</div>