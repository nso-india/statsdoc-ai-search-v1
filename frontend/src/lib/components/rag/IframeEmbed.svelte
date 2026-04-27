<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { ExternalLink, Shield } from '@lucide/svelte/icons';
	import DOMPurify from 'dompurify';

	const dispatch = createEventDispatcher();

	export let html: string;
	export let options: IframeOptions = {};

	interface IframeOptions {
		maxHeight?: number;
		theme?: 'light' | 'dark' | 'auto';
		sandbox?: string;
		allowFullscreen?: boolean;
	}

	let iframeElement: HTMLIFrameElement;
	let loading = true;
	let error = false;

	// Default options
	const defaultOptions: IframeOptions = {
		maxHeight: 400,
		theme: 'auto',
		sandbox: 'allow-scripts allow-same-origin',
		allowFullscreen: false,
		...options
	};

	// Extract iframe attributes
	$: iframeProps = parseIframeHtml(html);

	function parseIframeHtml(htmlString: string): any {
		try {
			const parser = new DOMParser();
			const doc = parser.parseFromString(htmlString, 'text/html');
			const iframe = doc.querySelector('iframe');
			
			if (!iframe) {
				throw new Error('No iframe found in HTML');
			}

			return {
				src: iframe.getAttribute('src') || '',
				width: iframe.getAttribute('width') || '100%',
				height: iframe.getAttribute('height') || '300',
				title: iframe.getAttribute('title') || 'Embedded content',
				frameborder: iframe.getAttribute('frameborder') || '0',
				scrolling: iframe.getAttribute('scrolling') || 'no'
			};
		} catch (err) {
			dispatch('error', new Error('Failed to parse iframe HTML'));
			return null;
		}
	}

	function onIframeLoad() {
		loading = false;
		error = false;
	}

	function onIframeError() {
		loading = false;
		error = true;
		dispatch('error', new Error('Failed to load iframe content'));
	}

	function openInNewTab() {
		if (iframeProps?.src) {
			window.open(iframeProps.src, '_blank', 'noopener,noreferrer');
		}
	}
</script>

{#if iframeProps}
	<div class="iframe-embed" data-theme={defaultOptions.theme}>
		<!-- Header -->
		<div class="iframe-header">
			<div class="iframe-info">
				<Shield class="w-4 h-4" />
				<span class="iframe-label">Embedded Content</span>
				{#if iframeProps.title}
					<span class="iframe-title">{iframeProps.title}</span>
				{/if}
			</div>
			
			<div class="iframe-actions">
				{#if iframeProps.src}
					<button 
						class="action-btn external-btn"
						on:click={openInNewTab}
						title="Open in new tab"
					>
						<ExternalLink class="w-4 h-4" />
						<span>Open</span>
					</button>
				{/if}
			</div>
		</div>

		<!-- Content -->
		<div class="iframe-content" style={defaultOptions.maxHeight ? `max-height: ${defaultOptions.maxHeight}px` : ''}>
			{#if loading}
				<div class="iframe-loading">
					<div class="loading-spinner"></div>
					<span>Loading embedded content...</span>
				</div>
			{/if}

			{#if error}
				<div class="iframe-error">
					<Shield class="w-8 h-8 text-red-500" />
					<div class="error-details">
						<h4>Failed to load content</h4>
						<p>The embedded content could not be loaded. This might be due to security restrictions or network issues.</p>
						{#if iframeProps.src}
							<button class="retry-btn" on:click={openInNewTab}>
								<ExternalLink class="w-4 h-4" />
								View in new tab
							</button>
						{/if}
					</div>
				</div>
			{:else}
				<iframe
					bind:this={iframeElement}
					src={iframeProps.src}
					width={iframeProps.width}
					height={iframeProps.height}
					title={iframeProps.title}
					frameborder={iframeProps.frameborder}
					scrolling={iframeProps.scrolling}
					sandbox={defaultOptions.sandbox}
					allowfullscreen={defaultOptions.allowFullscreen}
					class="embedded-iframe"
					class:loading
					on:load={onIframeLoad}
					on:error={onIframeError}
				></iframe>
			{/if}
		</div>

		<!-- Footer with security info -->
		<div class="iframe-footer">
			<div class="security-info">
				<Shield class="w-3 h-3" />
				<span>Content is sandboxed for security</span>
				{#if iframeProps.src}
					<span class="iframe-url">
						{new URL(iframeProps.src).hostname}
					</span>
				{/if}
			</div>
		</div>
	</div>
{:else}
	<div class="iframe-error">
		<Shield class="w-8 h-8 text-red-500" />
		<div class="error-details">
			<h4>Invalid iframe content</h4>
			<p>The provided HTML does not contain a valid iframe element.</p>
		</div>
	</div>
{/if}

<style>
	.iframe-embed {
		border-radius: 0.5rem;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		font-size: 0.875rem;
	}

	.iframe-embed[data-theme="dark"] {
		border-color: #374151;
		background: #1f2937;
	}

	.iframe-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #f3e8ff;
		border-bottom: 1px solid #c4b5fd;
	}

	.iframe-embed[data-theme="dark"] .iframe-header {
		background: #581c87;
		border-bottom-color: #7c3aed;
	}

	.iframe-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #6b21a8;
	}

	.iframe-embed[data-theme="dark"] .iframe-info {
		color: #e9d5ff;
	}

	.iframe-label {
		font-size: 0.875rem;
	}

	.iframe-title {
		font-size: 0.75rem;
		color: #7c3aed;
		background: #ede9fe;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.iframe-embed[data-theme="dark"] .iframe-title {
		color: #c4b5fd;
		background: #4c1d95;
	}

	.iframe-actions {
		display: flex;
		gap: 0.5rem;
	}

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.375rem 0.5rem;
		border: none;
		border-radius: 0.25rem;
		background: transparent;
		color: #6b21a8;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
	}

	.action-btn:hover {
		background: #ede9fe;
		color: #581c87;
	}

	.iframe-embed[data-theme="dark"] .action-btn {
		color: #c4b5fd;
	}

	.iframe-embed[data-theme="dark"] .action-btn:hover {
		background: #4c1d95;
		color: #f3e8ff;
	}

	.iframe-content {
		position: relative;
		overflow: hidden;
	}

	.iframe-loading {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 3rem;
		color: #6b7280;
	}

	.loading-spinner {
		width: 1.5rem;
		height: 1.5rem;
		border: 2px solid #e5e7eb;
		border-top: 2px solid #7c3aed;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.iframe-error {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		padding: 2rem;
		background: #fee2e2;
		color: #7f1d1d;
	}

	.error-details h4 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #dc2626;
	}

	.error-details p {
		margin: 0 0 1rem 0;
		font-size: 0.875rem;
		line-height: 1.5;
	}

	.retry-btn {
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

	.retry-btn:hover {
		background: #dc2626;
		color: #ffffff;
	}

	.embedded-iframe {
		width: 100%;
		height: 100%;
		border: none;
		background: #ffffff;
		transition: opacity 0.3s ease;
	}

	.embedded-iframe.loading {
		opacity: 0;
		position: absolute;
		top: 0;
		left: 0;
	}

	.iframe-footer {
		padding: 0.5rem 1rem;
		background: #f8fafc;
		border-top: 1px solid #e5e7eb;
	}

	.iframe-embed[data-theme="dark"] .iframe-footer {
		background: #374151;
		border-top-color: #4b5563;
	}

	.security-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: #6b7280;
	}

	.iframe-embed[data-theme="dark"] .security-info {
		color: #9ca3af;
	}

	.iframe-url {
		background: #e5e7eb;
		color: #374151;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-family: 'JetBrains Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
	}

	.iframe-embed[data-theme="dark"] .iframe-url {
		background: #4b5563;
		color: #d1d5db;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.iframe-header {
			padding: 0.5rem 0.75rem;
		}

		.iframe-title {
			display: none;
		}

		.iframe-loading {
			padding: 2rem 1rem;
		}

		.iframe-error {
			padding: 1.5rem 1rem;
			flex-direction: column;
			gap: 0.75rem;
		}
	}
</style>
