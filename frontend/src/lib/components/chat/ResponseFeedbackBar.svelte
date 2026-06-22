<script lang="ts">
	import { Copy, ThumbsDown, ThumbsUp } from '@lucide/svelte/icons';
	import ResponseFeedbackDialog from '$lib/components/chat/ResponseFeedbackDialog.svelte';
	import {
		submitResponseFeedback,
		type ResponseFeedbackRating
	} from '$lib/api/responseFeedback';
	import { authToken } from '$lib/stores';
	import { toast } from 'svelte-sonner';

	let {
		messageId,
		rating = null,
		disabled = false,
		onCopy,
		onRated
	}: {
		messageId: string | number;
		rating?: ResponseFeedbackRating | null;
		disabled?: boolean;
		onCopy?: () => void;
		onRated?: (messageId: string, rating: ResponseFeedbackRating) => void;
	} = $props();

	let dialogOpen = $state(false);
	let submittingUp = $state(false);
	const numericMessageId = $derived(Number(messageId));
	const canRate = $derived(!disabled && Number.isFinite(numericMessageId) && numericMessageId > 0);

	async function handleThumbsUp() {
		if (!canRate || submittingUp) return;

		submittingUp = true;
		try {
			await submitResponseFeedback({
				messageId: numericMessageId,
				rating: 'up',
				token: $authToken
			});
			onRated?.(String(messageId), 'up');
		} catch (error) {
			toast.error(error instanceof Error ? error.message : 'Failed to save feedback.');
		} finally {
			submittingUp = false;
		}
	}

	function handleThumbsDown() {
		if (!canRate) return;
		dialogOpen = true;
	}

	function handleDownSubmitted(nextRating: ResponseFeedbackRating) {
		onRated?.(String(messageId), nextRating);
	}
</script>

<div class="flex items-center gap-0.5 text-gray-600 dark:text-gray-400 mt-2">
	<button
		type="button"
		aria-label="Good response"
		title="Good response"
		class="response-action-btn"
		class:active-up={rating === 'up'}
		disabled={!canRate || submittingUp}
		onclick={handleThumbsUp}
	>
		<ThumbsUp class="h-4 w-4" />
	</button>

	<button
		type="button"
		aria-label="Bad response"
		title="Bad response"
		class="response-action-btn"
		class:active-down={rating === 'down'}
		disabled={!canRate}
		onclick={handleThumbsDown}
	>
		<ThumbsDown class="h-4 w-4" />
	</button>

	{#if onCopy}
		<button
			type="button"
			aria-label="Copy response"
			title="Copy response"
			class="response-action-btn"
			onclick={onCopy}
		>
			<Copy class="h-4 w-4" />
		</button>
	{/if}
</div>

{#if canRate}
	<ResponseFeedbackDialog
		bind:open={dialogOpen}
		messageId={numericMessageId}
		onSubmitted={handleDownSubmitted}
	/>
{/if}

<style>
	.response-action-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.375rem;
		border-radius: 0.5rem;
		transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease;
	}

	.response-action-btn:hover:not(:disabled) {
		background: rgba(0, 0, 0, 0.05);
		color: #111827;
	}

	:global(.dark) .response-action-btn:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.08);
		color: #fff;
	}

	.response-action-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
	}

	.response-action-btn.active-up {
		color: #1a337e;
		background: #eef2ff;
	}

	.response-action-btn.active-down {
		color: #b45309;
		background: #fff7ed;
	}

	:global(.dark) .response-action-btn.active-up {
		color: #93c5fd;
		background: rgba(26, 51, 126, 0.35);
	}

	:global(.dark) .response-action-btn.active-down {
		color: #fdba74;
		background: rgba(180, 83, 9, 0.25);
	}
</style>
