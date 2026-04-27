<script lang="ts">
	import MarkdownRenderer from './rag/MarkdownRenderer.svelte';

	export let content: string;
	export let messageId: string;
</script>

<div class="content-renderer">
	<!-- Use MarkdownRenderer for the entire content - it handles mixed content types -->
	<MarkdownRenderer 
		markdown={content}
		theme="auto"
		openLinksInNewTab={true}
		allowIframes={false}
		on:rendered={(e) => console.log('Content rendered:', e.detail.html)}
		on:error={(e) => console.error('Render error:', e.detail)}
	/>
</div>

<style>
	.content-renderer {
		width: 100%;
		max-width: none;
	}
	
	.content-renderer :global(.markdown-renderer) {
		background: transparent;
		border: none;
		border-radius: 0;
	}
</style>
