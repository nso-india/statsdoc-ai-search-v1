<script lang="ts">
	import { Toaster } from 'svelte-sonner';
	import { onMount } from 'svelte';
	import '../app.css';
	import { user, authToken, isAuthenticated, logoutUser } from '$lib/stores';
	import { getSessionUser, userSignOut } from '$lib/apis/auths';
	import { get } from 'svelte/store';

	let loaded = false;

	onMount(async () => {
		// Check authentication status following Open WebUI pattern
		const currentUser = get(user);
		const token = get(authToken);

		if (currentUser && token) {
			// User appears to be logged in, verify session is still valid
			const exp = (currentUser as any)?.expires_at; // token expiry time in unix timestamp
			
			if (exp && exp * 1000 < Date.now()) {
				// Token has expired, sign out user
				await logoutUser();
			} else {
				// Token is still valid, verify with backend
				try {
					const sessionUser: any = await getSessionUser(token);
					if (sessionUser) {
						// Update user store with fresh session data
						user.set(sessionUser);
						isAuthenticated.set(true);
					} else {
						// Invalid session, sign out user
						await logoutUser();
					}
				} catch (error) {
					console.error('Session verification failed:', error);
					await logoutUser();
				}
			}
		}

		loaded = true;
	});
</script>

{#if loaded}
	<div class="h-screen overflow-auto">
		<slot />
	</div>
{:else}
	<div class="w-full h-screen flex items-center justify-center overflow-auto">
		<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
	</div>
{/if}

<Toaster />
