<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { user, authToken, logoutUser } from '$lib/stores';
  import { settingsStore, type AppSettings } from '$lib/stores/settings';
  import { Input } from '$lib/components/ui/input';
  import { Button } from '$lib/components/ui/button';
  import { Label } from '$lib/components/ui/label';
  import { updateNamespaceConfig } from '$lib/apis/settings';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import MessageSquare from 'lucide-svelte/icons/message-square';
  import LogOut from 'lucide-svelte/icons/log-out';
  import AuthGuard from '../../../lib/components/auth/AuthGuard.svelte';

  let saving = false;
  let error = '';
  let config: AppSettings = {
    file_size_limit_mb: 20,
    questions_per_chat: 10,
    chats_per_day: 50
  };
  
  // Original values to track changes
  let originalConfig: AppSettings = {
    file_size_limit_mb: 20,
    questions_per_chat: 10,
    chats_per_day: 50
  };
  
  // Check if any values have changed
  $: hasChanges = config.file_size_limit_mb !== originalConfig.file_size_limit_mb ||
                  config.questions_per_chat !== originalConfig.questions_per_chat ||
                  config.chats_per_day !== originalConfig.chats_per_day;

  // Subscribe to settings store
  $: if ($settingsStore.settings) {
    config = { ...$settingsStore.settings };
    originalConfig = { ...$settingsStore.settings };
  }

  async function loadConfig() {
    const token = $authToken;
    if (token) {
      await settingsStore.loadSettings(token, true); // Force refresh
    }
  }

  async function saveConfig() {
    saving = true;
    error = '';
    try {
      const token = $authToken;
      if (!token) throw new Error('Not authenticated');
      
      await updateNamespaceConfig(token, 'chat', {
        file_size_limit_mb: Number(config.file_size_limit_mb),
        questions_per_chat: Number(config.questions_per_chat),
        chats_per_day: Number(config.chats_per_day)
      });
      
      // Update the settings store cache
      settingsStore.updateSettings(config);
      
      // Update original config to reflect saved changes
      originalConfig = { ...config };
      
      toast.success('Settings updated successfully');
    } catch (err: any) {
      error = err?.detail || err?.message || 'Failed to update settings';
      toast.error(error);
    } finally {
      saving = false;
    }
  }

  function logout() {
    logoutUser();
    goto('/login');
  }

  onMount(loadConfig);
</script>

<svelte:head>
  <title>Settings - Mospi PS2</title>
</svelte:head>

<AuthGuard requireAdmin={true}>
<div class="w-full h-full bg-background overflow-auto p-6">
  <!-- Settings Content -->
  <div class="max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Application Settings</h1>
    
    {#if $settingsStore.loading}
      <div class="text-center text-muted-foreground">Loading settings...</div>
    {:else}
      <form onsubmit={(e) => { e.preventDefault(); saveConfig(); }} class="space-y-6">
        <div>
          <Label for="file_size_limit_mb">File Size Limit (MB)</Label>
          <Input
            id="file_size_limit_mb"
            type="number"
            min="1"
            bind:value={config.file_size_limit_mb}
            class="mt-1"
            required
          />
        </div>
        
        <div>
          <Label for="questions_per_chat">Questions per Chat</Label>
          <Input
            id="questions_per_chat"
            type="number"
            min="1"
            bind:value={config.questions_per_chat}
            class="mt-1"
            required
          />
        </div>
        
        <div>
          <Label for="chats_per_day">Chats per Day</Label>
          <Input
            id="chats_per_day"
            type="number"
            min="1"
            bind:value={config.chats_per_day}
            class="mt-1"
            required
          />
        </div>
        
        {#if error}
          <div class="text-red-500 text-sm">{error}</div>
        {/if}
        <Button type="submit" disabled={saving || !hasChanges} class="w-full">
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </form>
    {/if}
  </div>
</div>
</AuthGuard>
