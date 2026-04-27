<script lang="ts">
	export let show = false;
	
	$: console.log('TestModal show prop:', show);
</script>

{#if show}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
			<h2 class="text-lg font-semibold mb-4">Test Modal</h2>
			<p class="mb-4">This is a test modal to verify the modal system is working.</p>
			<button 
				class="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
				on:click={() => show = false}
			>
				Close
			</button>
		</div>
	</div>
{/if}
