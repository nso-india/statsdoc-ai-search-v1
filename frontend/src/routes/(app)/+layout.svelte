<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { user, authToken, isAuthenticated, logoutUser } from '$lib/stores';
	import { loadUserRole, userRole, userRoleLoading, clearUserRole } from '$lib/stores/userRole';
	import { getSessionUser } from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';
	import { get } from 'svelte/store';

	let loaded = false;
	let authChecked = false;

	onMount(async () => {
		console.log('App layout mounted, checking authentication...');
		
		// First, try to restore authentication from localStorage
		const storedToken = localStorage.getItem('access_token') || localStorage.getItem('token');
		const storedUser = localStorage.getItem('user');
		
		if (storedToken && storedUser) {
			try {
				// Parse stored user data
				const userData = JSON.parse(storedUser);
				
				// Verify the token is still valid by checking session
				const sessionUser = await getSessionUser(storedToken);
				
				if (sessionUser) {
					// Update stores with valid session data
					user.set(sessionUser);
					authToken.set(storedToken);
					isAuthenticated.set(true);
					// Load user role after setting user
					await loadUserRole();
					loaded = true;
					authChecked = true;
					console.log('Authentication restored successfully');
					return;
				} else {
					throw new Error('Invalid session');
				}
			} catch (error) {
				console.error('Session validation failed:', error);
				// Clear invalid session data
				localStorage.removeItem('access_token');
				localStorage.removeItem('token');
				localStorage.removeItem('user');
				logoutUser();
				clearUserRole();
			}
		}
		
		// No valid authentication found
		console.log('No valid authentication found, redirecting to login');
		const currentUrl = `${window.location.pathname}${window.location.search}`;
		const encodedUrl = encodeURIComponent(currentUrl);
		authChecked = true;
		goto(`/login?redirect=${encodedUrl}`);
	});

	// Reactive check for user state changes
	$: if (authChecked && $isAuthenticated && $user && !$userRoleLoading) {
		loaded = true;
	}
</script>

{#if loaded && $isAuthenticated && $user}
	<div class="w-full h-full">
		<slot />
	</div>
{:else if authChecked}
	<!-- Show loading while authentication is being verified -->
	<div class="w-full h-full flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
			<p class="text-gray-600">Verifying authentication...</p>
		</div>
	</div>
{:else}
	<!-- Initial loading state -->
	<div class="w-full h-full flex items-center justify-center">
		<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
	</div>
{/if}