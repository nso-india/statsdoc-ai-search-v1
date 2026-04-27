<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let value = '';
	export let disabled = false;
	export let placeholder = 'Type your message...';

	const dispatch = createEventDispatcher();

	let textareaElement: HTMLTextAreaElement;

	function handleSubmit() {
		if (value.trim() && !disabled) {
			dispatch('send', value.trim());
			value = '';
			resizeTextarea();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}

	function resizeTextarea() {
		if (textareaElement) {
			textareaElement.style.height = 'auto';
			textareaElement.style.height = Math.min(textareaElement.scrollHeight, 120) + 'px';
		}
	}

	function handleInput() {
		resizeTextarea();
	}
</script>

<div class="flex items-end space-x-3">
	<div class="flex-1 relative">
		<textarea
			bind:this={textareaElement}
			bind:value
			on:keydown={handleKeydown}
			on:input={handleInput}
			{placeholder}
			{disabled}
			rows="1"
			class="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 pr-12 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
			style="min-height: 2.5rem; max-height: 120px;"
		></textarea>
		
		<button
			on:click={handleSubmit}
			{disabled}
			aria-label="Send message"
			class="absolute right-2 bottom-2 p-2 text-blue-500 hover:text-blue-600 disabled:text-gray-400 disabled:cursor-not-allowed"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
			</svg>
		</button>
	</div>
</div>

<style>
	textarea::-webkit-scrollbar {
		width: 6px;
	}
	
	textarea::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 3px;
	}
	
	textarea::-webkit-scrollbar-thumb {
		background: #c1c1c1;
		border-radius: 3px;
	}
	
	textarea::-webkit-scrollbar-thumb:hover {
		background: #a8a8a8;
	}
</style>
