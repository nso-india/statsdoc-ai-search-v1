<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import { createEventDispatcher } from 'svelte';

  export let filters = {
    success: true,
    failed: false,
    uploading: false
  };

  const dispatch = createEventDispatcher();

  function updateFilter(key: string, value: boolean) {
    filters = { ...filters, [key]: value };
    dispatch('filter', { filters });
  }
</script>

<div class="mb-4">
  <DropdownMenu.Root>
    <DropdownMenu.Trigger asChild let:builder>
      <Button builders={[builder]} variant="outline" size="sm">
        Filter
      </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="start">
      <DropdownMenu.Label>Filter by</DropdownMenu.Label>
      <DropdownMenu.Separator />
      <DropdownMenu.CheckboxItem 
        checked={filters.success}
        on:click={() => updateFilter('success', !filters.success)}
      >
        Success
      </DropdownMenu.CheckboxItem>
      <DropdownMenu.CheckboxItem 
        checked={filters.failed}
        on:click={() => updateFilter('failed', !filters.failed)}
      >
        Failed
      </DropdownMenu.CheckboxItem>
      <DropdownMenu.CheckboxItem 
        checked={filters.uploading}
        on:click={() => updateFilter('uploading', !filters.uploading)}
      >
        Uploading
      </DropdownMenu.CheckboxItem>
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</div>