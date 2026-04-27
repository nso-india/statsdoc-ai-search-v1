<script lang="ts">
  import { Input } from "$lib/components/ui/input/index.js";
  import { createEventDispatcher } from 'svelte';

  export let placeholder = "Search your files";
  export let value = "";
  
  const dispatch = createEventDispatcher();

  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = target.value;
    dispatch('search', { query: value });
  }
</script>

<div class="flex justify-center mt-4">
  <div class="w-full max-w-2xl">
    <Input 
      {placeholder} 
      {value}
      on:input={handleInput}
      class="w-full" 
    />
  </div>
</div>