<script lang="ts">
  import { goto } from '$app/navigation';
  import { Button } from '$lib/components/ui/button';
  import * as Card from '$lib/components/ui/card';
  import { ShieldX } from 'lucide-svelte';
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
  <Card.Root class="w-full max-w-md">
    <Card.Header class="text-center space-y-4">
      <div class="mx-auto w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
        <ShieldX class="w-6 h-6 text-red-600 dark:text-red-400" />
      </div>
      <div>
        <Card.Title class="text-xl font-semibold">Access Denied</Card.Title>
        <Card.Description class="text-gray-600 dark:text-gray-400">
          You don't have permission to access this page. Admin privileges are required.
        </Card.Description>
      </div>
    </Card.Header>
    <Card.Content class="flex flex-col space-y-4">
      <Button
        onclick={() => goto('/c')}
        class="w-full"
      >
          Go to Chat
      </Button>
      <Button
        variant="outline"
        onclick={() => history.back()}
        class="w-full"
      >
          Go Back
      </Button>
    </Card.Content>
  </Card.Root>
</div>
