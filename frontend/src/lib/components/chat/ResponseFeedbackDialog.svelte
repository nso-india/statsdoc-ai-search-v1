<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import {
		RESPONSE_FEEDBACK_CATEGORIES,
		submitResponseFeedback,
		type ResponseFeedbackRating
	} from '$lib/api/responseFeedback';
	import { authToken } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import X from '@lucide/svelte/icons/x';

	let {
		open = $bindable(false),
		messageId,
		onSubmitted
	}: {
		open?: boolean;
		messageId: number;
		onSubmitted?: (rating: ResponseFeedbackRating) => void;
	} = $props();

	let selectedCategory = $state('');
	let details = $state('');
	let submitting = $state(false);

	$effect(() => {
		if (open) {
			selectedCategory = '';
			details = '';
		}
	});

	function handleClose() {
		open = false;
	}

	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (!selectedCategory) {
			toast.error('Please select a reason for your feedback.');
			return;
		}

		submitting = true;
		try {
			await submitResponseFeedback({
				messageId,
				rating: 'down',
				category: selectedCategory,
				details: details.trim(),
				token: $authToken
			});
			toast.success('Thanks for your feedback.');
			onSubmitted?.('down');
			open = false;
		} catch (error) {
			toast.error(error instanceof Error ? error.message : 'Failed to submit feedback.');
		} finally {
			submitting = false;
		}
	}
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content
		class="sm:max-w-[480px] p-0 overflow-hidden gap-0 border border-gray-200 shadow-xl"
		oninteractoutside={() => (open = false)}
	>
		<div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
			<h2 class="text-lg font-semibold text-gray-900">Share feedback</h2>
			<button
				type="button"
				onclick={handleClose}
				class="rounded-md p-1 text-gray-500 transition hover:bg-gray-100 hover:text-gray-800"
				aria-label="Close"
			>
				<X class="h-4 w-4" />
			</button>
		</div>

		<form class="space-y-4 px-5 py-4" onsubmit={handleSubmit}>
			<div class="flex flex-wrap gap-2">
				{#each RESPONSE_FEEDBACK_CATEGORIES as category (category.value)}
					<button
						type="button"
						class="response-feedback-chip rounded-full border px-3 py-1.5 text-sm transition"
						class:selected={selectedCategory === category.value}
						onclick={() => (selectedCategory = category.value)}
					>
						{category.label}
					</button>
				{/each}
			</div>

			<textarea
				bind:value={details}
				placeholder="Share details (optional)"
				maxlength={2000}
				rows={4}
				class="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:border-[#1a337e] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1a337e]/20"
			></textarea>

			<p class="rounded-lg bg-gray-50 px-3 py-2 text-xs leading-relaxed text-gray-500">
				Your question and this answer will be included with your feedback to help improve
				StatsDoc AI Assistant.
			</p>

			<div class="flex justify-end pt-1">
				<button
					type="submit"
					class="rounded-lg bg-[#1a337e] px-5 py-2 text-sm font-medium text-white transition hover:bg-[#152966] disabled:cursor-not-allowed disabled:opacity-60"
					disabled={submitting}
				>
					{submitting ? 'Submitting...' : 'Submit'}
				</button>
			</div>
		</form>
	</AlertDialog.Content>
</AlertDialog.Root>

<style>
	.response-feedback-chip {
		border-color: #e5e7eb;
		background: #fff;
		color: #374151;
	}

	.response-feedback-chip:hover {
		border-color: #c7d2fe;
		background: #f8fafc;
	}

	.response-feedback-chip.selected {
		border-color: #1a337e;
		background: #eef2ff;
		color: #1a337e;
		font-weight: 500;
	}
</style>
