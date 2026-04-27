<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated, initializeAuth } from '$lib/stores';

	onMount(async () => {
		// Initialize authentication from localStorage
		await initializeAuth();
		
		// Subscribe to auth state and redirect accordingly
		const unsubscribe = isAuthenticated.subscribe((authenticated) => {
			if (authenticated) {
				goto('/c');
			} else {
				goto('/login');
			}
		});

		// Cleanup subscription
		return unsubscribe;
	});
</script>

<!-- Show a loading state while determining authentication -->
<div class="flex items-center justify-center min-h-screen">
	<div class="text-center">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
		<p class="mt-2 text-gray-600">Loading...</p>
	</div>
</div>
