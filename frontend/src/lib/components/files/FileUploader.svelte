<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { toast } from 'svelte-sonner';
  
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  export let accept: string = '.pdf,.docx,.doc,.pptx,.ppt,.txt';
  export let multiple: boolean = false;
  export let loading: boolean = false;

  let dragOver = false;
  let fileInput: HTMLInputElement;

  function handleFileSelect(event: Event) {
    const files = (event.target as HTMLInputElement)?.files;
    if (files && files.length > 0) {
      handleFiles(Array.from(files));
    }
  }

  // Handle drag and drop events
  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      processFiles(Array.from(files));
    }
  }

  function handleFiles(files: File[]) {
    // Validate file types
    const allowedTypes = accept.split(',').map(type => type.trim());
    const validFiles = files.filter(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      return allowedTypes.includes(fileExtension);
    });

    if (validFiles.length !== files.length) {
      toast.error('Some files were not supported and were skipped.');
    }

    if (validFiles.length > 0) {
      dispatch('filesSelected', { files: validFiles });
    }
  }

  function openFileDialog() {
    fileInput.click();
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
  }
</script>

<Card.Root 
  class="mb-6 {dragOver ? 'border-primary bg-primary/5' : ''} transition-colors duration-200"
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <Card.Content class="flex flex-col items-center justify-center py-10 border-2 border-dashed border-gray-300 rounded-lg">
    {#if loading}
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
      <p class="text-center text-muted-foreground">Uploading files...</p>
    {:else}
      <div class="text-center">
        <svg 
          class="mx-auto h-12 w-12 text-gray-400 mb-4" 
          stroke="currentColor" 
          fill="none" 
          viewBox="0 0 48 48"
        >
          <path 
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" 
            stroke-width="2" 
            stroke-linecap="round" 
            stroke-linejoin="round"
          />
        </svg>
        
        <p class="text-center mb-1">Drag and Drop, Upload a file or a URL</p>
        <p class="text-xs text-muted-foreground mb-4">
          Supported formats: {accept.replace(/\./g, '').replace(/,/g, ', ').toUpperCase()}
        </p>
        
        <Button variant="outline" onclick={openFileDialog}>
            Upload File{multiple ? 's' : ''}
        </Button>
      </div>
    {/if}
  </Card.Content>
</Card.Root>

<input 
  bind:this={fileInput}
  type="file" 
  {accept}
  {multiple}
  on:change={handleFileSelect}
  class="hidden"
/>