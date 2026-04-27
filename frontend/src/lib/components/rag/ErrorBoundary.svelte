<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from '@lucide/svelte/icons';

	const dispatch = createEventDispatcher();

	export let error: string | Error | null = null;
	export let fallback: string = '';
	export let showDetails: boolean = false;
	export let retryable: boolean = false;

	let expanded = false;
	let errorDetails: string = '';
	let errorStack: string = '';

	$: if (error) {
		if (error instanceof Error) {
			errorDetails = error.message;
			errorStack = error.stack || '';
		} else if (typeof error === 'string') {
			errorDetails = error;
			errorStack = '';
		} else {
			errorDetails = 'An unknown error occurred';
			errorStack = '';
		}
	}

	function retry() {
		dispatch('retry');
	}

	function toggleExpanded() {
		expanded = !expanded;
	}
</script>

{#if error}
	<div class="error-boundary">
		<div class="error-content">
			<div class="error-header">
				<AlertTriangle class="w-5 h-5 text-red-500" />
				<div class="error-info">
					<h3 class="error-title">Something went wrong</h3>
					<p class="error-message">{errorDetails}</p>
				</div>
			</div>

			<div class="error-actions">
				{#if retryable}
					<button class="retry-btn" on:click={retry}>
						<RefreshCw class="w-4 h-4" />
						Try Again
					</button>
				{/if}
				
				{#if showDetails && errorStack}
					<button class="details-btn" on:click={toggleExpanded}>
						{#if expanded}
							<ChevronUp class="w-4 h-4" />
						{:else}
							<ChevronDown class="w-4 h-4" />
						{/if}
						{expanded ? 'Hide' : 'Show'} Details
					</button>
				{/if}
			</div>

			{#if expanded && errorStack}
				<div class="error-details">
					<h4>Error Details:</h4>
					<pre class="error-stack">{errorStack}</pre>
				</div>
			{/if}
		</div>

		{#if fallback}
			<div class="fallback-content">
				<h4>Fallback Content:</h4>
				<div class="fallback-text">{fallback}</div>
			</div>
		{/if}
	</div>
{:else}
	<slot />
{/if}

<style>
	.error-boundary {
		border: 1px solid #fca5a5;
		border-radius: 0.5rem;
		background: #fee2e2;
		padding: 1rem;
		margin: 1rem 0;
	}

	.error-content {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.error-header {
		display: flex;
		gap: 0.75rem;
		align-items: flex-start;
	}

	.error-info {
		flex: 1;
	}

	.error-title {
		margin: 0 0 0.25rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #dc2626;
	}

	.error-message {
		margin: 0;
		font-size: 0.875rem;
		color: #7f1d1d;
		line-height: 1.5;
	}

	.error-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.retry-btn,
	.details-btn {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.375rem 0.75rem;
		border: 1px solid #dc2626;
		border-radius: 0.375rem;
		background: #ffffff;
		color: #dc2626;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.retry-btn:hover,
	.details-btn:hover {
		background: #dc2626;
		color: #ffffff;
	}

	.details-btn {
		border-color: #6b7280;
		color: #6b7280;
	}

	.details-btn:hover {
		background: #6b7280;
		color: #ffffff;
	}

	.error-details {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #fca5a5;
	}

	.error-details h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #7f1d1d;
	}

	.error-stack {
		background: #ffffff;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
		padding: 0.75rem;
		font-family: 'JetBrains Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
		font-size: 0.75rem;
		color: #7f1d1d;
		overflow-x: auto;
		white-space: pre-wrap;
		word-wrap: break-word;
		max-height: 200px;
		overflow-y: auto;
	}

	.fallback-content {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #fca5a5;
	}

	.fallback-content h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #7f1d1d;
	}

	.fallback-text {
		background: #ffffff;
		border: 1px solid #fca5a5;
		border-radius: 0.375rem;
		padding: 0.75rem;
		font-size: 0.875rem;
		color: #374151;
		line-height: 1.5;
	}

	/* Dark theme */
	@media (prefers-color-scheme: dark) {
		.error-boundary {
			border-color: #dc2626;
			background: #7f1d1d;
		}

		.error-title {
			color: #fca5a5;
		}

		.error-message {
			color: #fecaca;
		}

		.retry-btn,
		.details-btn {
			background: #7f1d1d;
			color: #fca5a5;
			border-color: #fca5a5;
		}

		.retry-btn:hover,
		.details-btn:hover {
			background: #fca5a5;
			color: #7f1d1d;
		}

		.details-btn {
			border-color: #9ca3af;
			color: #9ca3af;
		}

		.details-btn:hover {
			background: #9ca3af;
			color: #1f2937;
		}

		.error-details {
			border-top-color: #dc2626;
		}

		.error-details h4 {
			color: #fca5a5;
		}

		.error-stack {
			background: #1f2937;
			border-color: #dc2626;
			color: #fca5a5;
		}

		.fallback-content {
			border-top-color: #dc2626;
		}

		.fallback-content h4 {
			color: #fca5a5;
		}

		.fallback-text {
			background: #1f2937;
			border-color: #dc2626;
			color: #d1d5db;
		}
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.error-boundary {
			padding: 0.75rem;
		}

		.error-header {
			gap: 0.5rem;
		}

		.error-actions {
			flex-direction: column;
			align-items: stretch;
		}

		.retry-btn,
		.details-btn {
			justify-content: center;
		}

		.error-stack {
			font-size: 0.625rem;
		}
	}
</style>
