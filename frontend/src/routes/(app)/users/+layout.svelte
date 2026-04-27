<script lang="ts">
  import { user } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';

  let { children } = $props();

  // Permission check for admin access
  onMount(() => {
    if ($user && !($user.role === 'SUPERADMIN' || $user.is_staff || $user.is_superuser)) {
      toast.error('Access denied. Admin privileges required.');
      goto('/c');
    }
  });

  $effect(() => {
    if ($user && !($user.role === 'SUPERADMIN' || $user.is_staff || $user.is_superuser)) {
      toast.error('Access denied. Admin privileges required.');
      goto('/c');
    }
  });
</script>

<div class="min-h-screen bg-background">
  {@render children()}
</div>