<script lang="ts">
  import { toast } from 'svelte-sonner';
  import Modal from '$lib/components/common/Modal.svelte';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Button } from '$lib/components/ui/button';
  import { Spinner } from '$lib/components/ui/loading';
  import X from 'lucide-svelte/icons/x';
  import { createKnowledgeBase } from '$lib/api/knowledgebase';
  
  interface Props {
    show?: boolean;
    onSuccess?: () => void;
  }
  
  let { show = $bindable(false), onSuccess }: Props = $props();
  
  let loading = $state(false);
  let formData = $state({
    name: '',
    description: ''
  });
  
  // Reset form when modal is opened
  $effect(() => {
    if (show) {
      formData = {
        name: '',
        description: ''
      };
    }
  });
  
  async function handleSubmit() {
    // Validation
    if (!formData.name.trim()) {
      toast.error('Please enter a name for the knowledge base');
      return;
    }
    
    loading = true;
    try {
      await createKnowledgeBase({
        name: formData.name.trim(),
        description: formData.description.trim()
      });
      
      toast.success('Knowledge base created successfully');
      show = false;
      onSuccess?.();
    } catch (error) {
      console.error('Error creating knowledge base:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to create knowledge base');
    } finally {
      loading = false;
    }
  }
  
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
</script>

<Modal size="sm" bind:show>
  <div>
    <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
      <div class="text-lg font-medium self-center">Create Knowledge Base</div>
      <Button
        variant="ghost"
        size="icon"
        onclick={() => (show = false)}
      >
        <X class="size-4" />
      </Button>
    </div>
    
    <div class="px-5 pb-4 pt-2">
      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="space-y-4">
          <!-- Name Field -->
          <div class="space-y-2">
            <Label for="kb-name">
              Name <span class="text-red-500">*</span>
            </Label>
            <Input
              id="kb-name"
              type="text"
              placeholder="e.g., Product Documentation"
              bind:value={formData.name}
              onkeydown={handleKeyDown}
              disabled={loading}
              required
            />
          </div>
          
          <!-- Description Field -->
          <div class="space-y-2">
            <Label for="kb-description">Description</Label>
            <textarea
              id="kb-description"
              placeholder="Enter a description for this knowledge base..."
              bind:value={formData.description}
              disabled={loading}
              rows="4"
              class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            ></textarea>
          </div>
          
          <!-- Action Buttons -->
          <div class="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onclick={() => (show = false)}
              disabled={loading}
              type="button"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading || !formData.name.trim()}
            >
              {#if loading}
                <Spinner class="size-4 mr-2" />
                Creating...
              {:else}
                Create
              {/if}
            </Button>
          </div>
        </div>
      </form>
    </div>
  </div>
</Modal>
