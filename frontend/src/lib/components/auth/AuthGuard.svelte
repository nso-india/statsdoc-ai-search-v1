<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user, isAuthenticated } from '$lib/stores';
	import { toast } from 'svelte-sonner';

	export let requireAdmin = false;
	export let redirectTo = '/login';

	let authorized = false;
	let checking = true;

	onMount(() => {
		// Check authentication
		if (!$isAuthenticated || !$user) {
			toast.error('Please log in to access this page');
			goto(redirectTo);
			return;
		}

		// Check admin role if required
		if (requireAdmin && !['STAFF', 'SUPERADMIN'].includes($user.role || '')) {
			toast.error('Access denied. Staff privileges required.');
			goto('/c');
			return;
		}

		authorized = true;
		checking = false;
	});

	// Reactive check for auth state changes
	$: if ($isAuthenticated === false || !$user) {
		authorized = false;
		checking = false;
		goto(redirectTo);
	}

	$: if (requireAdmin && $user && !['STAFF', 'SUPERADMIN'].includes($user.role || '')) {
		authorized = false;
		checking = false;
		goto('/c');
	}
</script>

{#if checking}
	<div class="w-full h-full flex items-center justify-center min-h-[50vh]">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
			<p class="text-gray-600">Checking permissions...</p>
		</div>
	</div>
{:else if authorized}
	<slot />
{:else}
	<div class="w-full h-full flex items-center justify-center min-h-[50vh]">
		<div class="text-center">
			<p class="text-red-600 text-lg mb-4">Access Denied</p>
			<p class="text-gray-600">You don't have permission to access this page.</p>
		</div>
	</div>
{/if}
