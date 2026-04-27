<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  function handleUpload() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = '.pdf,.docx,.doc,.pptx,.ppt,.txt';
    fileInput.onchange = (event) => {
      const files = (event.target as HTMLInputElement)?.files;
      if (files && files.length > 0) {
        dispatch('upload', { files: Array.from(files) });
      }
    };
    fileInput.click();
  }

  function handleButtonClick(event: Event) {
    event.stopPropagation();
    handleUpload();
  }

  function handleDrop(event: CustomEvent) {
    const dragEvent = event as any as DragEvent;
    dragEvent.preventDefault();
    const files = dragEvent.dataTransfer?.files;
    if (files && files.length > 0) {
      dispatch('upload', { files: Array.from(files) });
    }
  }

  function handleDragOver(event: CustomEvent) {
    const dragEvent = event as any as DragEvent;
    dragEvent.preventDefault();
  }

  function handleKeyDown(event: CustomEvent) {
    const keyEvent = event as any as KeyboardEvent;
    if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
      keyEvent.preventDefault();
      handleUpload();
    }
  }
</script>

<Card.Root class="mb-6">
  <Card.Content 
    class="flex flex-col items-center justify-center py-10 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400 transition-colors"
    ondrop={handleDrop}
    ondragover={handleDragOver}
    onclick={handleUpload}
    role="button"
    tabindex={0}
    onkeydown={handleKeyDown}
  >
    <p class="text-center mb-1">Drag and Drop, Upload a file or a URL</p>
    <p class="text-xs text-muted-foreground">PDF, DOCX, DOC, PPTX, PPT, or TXT</p>
    <Button variant="outline" class="mt-4" onclick={handleButtonClick}>
      Upload File
    </Button>
  </Card.Content>
</Card.Root>