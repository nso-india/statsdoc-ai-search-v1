<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  onMount(() => {
    goto('/admin-reports', { replaceState: true });
  });
</script>

<p class="p-6 text-sm text-muted-foreground">Redirecting to Admin Reports...</p>
