<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from "$lib/components/ui/button";
	
	function handleGoBack() {
		history.back();
	}
</script>

<svelte:head>
	<title>{$page.status || 'Error'} - Page Not Found | MOSPI</title>
</svelte:head>

<div class="min-h-screen bg-background flex items-center justify-center px-4">
	<div class="text-center space-y-6 max-w-md">
		<!-- MOSPI Logo -->
		<div class="flex justify-center">
			<img src="/MOSPILOGO.webp" alt="MOSPI Logo" class="h-16 w-16" />
		</div>
		
		<!-- Error Code -->
		<h1 class="text-6xl font-bold text-muted-foreground">{$page.status || 500}</h1>
		
		<!-- Message -->
		<div class="space-y-2">
			<h2 class="text-2xl font-semibold">
				{#if $page.status === 404}
					Page not found
				{:else if $page.status === 500}
					Internal server error
				{:else}
					Something went wrong
				{/if}
			</h2>
			<p class="text-muted-foreground">
				{$page.error?.message || 'Sorry, we couldn\'t find the page you\'re looking for.'}
			</p>
		</div>

		<!-- Go Back Button -->
		<div class="pt-2">
			<Button 
				variant="ghost"
				class="text-foreground underline underline-offset-4"
				on:click={handleGoBack}
			>
				Go back
			</Button>
		</div>
	</div>
</div>