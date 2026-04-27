<script lang="ts">
  import { toast } from 'svelte-sonner';
  import Modal from '$lib/components/common/Modal.svelte';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Button } from '$lib/components/ui/button';
  import { Spinner } from '$lib/components/ui/loading';
  import X from 'lucide-svelte/icons/x';
  import { updateKnowledgeBase, type KnowledgeBase } from '$lib/api/knowledgebase';
  
  interface Props {
    show?: boolean;
    knowledgeBase?: KnowledgeBase | null;
    onSuccess?: () => void;
  }
  
  let { show = $bindable(false), knowledgeBase = $bindable(null), onSuccess }: Props = $props();
  
  let loading = $state(false);
  let formData = $state({
    name: '',
    description: ''
  });
  
  // Update form when knowledge base changes
  $effect(() => {
    if (show && knowledgeBase) {
      formData = {
        name: knowledgeBase.name,
        description: knowledgeBase.description
      };
    }
  });
  
  // Check if form is valid (name is required and not empty)
  let isFormValid = $derived(formData.name.trim().length > 0);
  
  async function handleSubmit() {
    // Validation
    if (!formData.name.trim()) {
      toast.error('Please enter a name for the knowledge base');
      return;
    }
    
    if (!knowledgeBase) {
      toast.error('No knowledge base selected');
      return;
    }
    
    loading = true;
    try {
      await updateKnowledgeBase(knowledgeBase.id, {
        name: formData.name.trim(),
        description: formData.description.trim()
      });
      
      toast.success('Knowledge base updated successfully');
      show = false;
      onSuccess?.();
    } catch (error) {
      console.error('Error updating knowledge base:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to update knowledge base');
    } finally {
      loading = false;
    }
  }
  
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey && isFormValid) {
      event.preventDefault();
      handleSubmit();
    }
  }
</script>

<Modal size="sm" bind:show>
  <div>
    <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
      <div class="text-lg font-medium self-center">Edit Knowledge Base</div>
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
            <Label for="kb-name-edit">
              Name <span class="text-red-500">*</span>
            </Label>
            <Input
              id="kb-name-edit"
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
            <Label for="kb-description-edit">Description</Label>
            <textarea
              id="kb-description-edit"
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
              disabled={loading || !isFormValid}
            >
              {#if loading}
                <Spinner class="size-4 mr-2" />
                Saving...
              {:else}
                Save Changes
              {/if}
            </Button>
          </div>
        </div>
      </form>
    </div>
  </div>
</Modal>
