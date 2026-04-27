<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Copy, Check, Download, Expand, Minimize, Search } from '@lucide/svelte/icons';
	import { toast } from 'svelte-sonner';

	const dispatch = createEventDispatcher();

	export let json: string;
	export let options: JsonViewerOptions = {};

	interface JsonViewerOptions {
		enableFormatting?: boolean;
		copyButtonStyle?: 'icon' | 'text' | 'both';
		theme?: 'light' | 'dark' | 'auto';
		maxHeight?: number;
		enableSearch?: boolean;
		enableDownload?: boolean;
		collapsible?: boolean;
		expandLevel?: number;
	}

	let copied = false;
	let expanded = false;
	let searchTerm = '';
	let searchResults: number = 0;
	let parsedJson: any = null;
	let validationError: string | null = null;
	let searchInputElement: HTMLInputElement;

	// Default options
	const defaultOptions: JsonViewerOptions = {
		enableFormatting: true,
		copyButtonStyle: 'icon',
		theme: 'auto',
		maxHeight: 400,
		enableSearch: false,
		enableDownload: true,
		collapsible: true,
		expandLevel: 2,
		...options
	};

	// Parse and validate JSON
	$: {
		try {
			parsedJson = JSON.parse(json);
			validationError = null;
		} catch (error) {
			parsedJson = null;
			validationError = error instanceof Error ? error.message : 'Invalid JSON';
		}
	}

	// Format JSON with syntax highlighting
	$: formattedJson = formatJson(json, searchTerm);

	function formatJson(jsonString: string, highlight: string = ''): string {
		try {
			const parsed = JSON.parse(jsonString);
			let formatted = JSON.stringify(parsed, null, 2);
			
			if (defaultOptions.enableFormatting) {
				formatted = highlightJsonSyntax(formatted, highlight);
			}
			
			return formatted;
		} catch {
			return escapeHtml(jsonString);
		}
	}

	function highlightJsonSyntax(jsonString: string, highlight: string = ''): string {
		let highlighted = escapeHtml(jsonString);
		
		// Keys
		highlighted = highlighted.replace(/"([^"]+)"(\s*:)/g, '<span class="json-key">"$1"</span><span class="json-colon">$2</span>');
		
		// String values
		highlighted = highlighted.replace(/(:)\s*"([^"]*?)"/g, '$1 <span class="json-string">"$2"</span>');
		
		// Numbers
		highlighted = highlighted.replace(/(:)\s*(-?\d+\.?\d*)/g, '$1 <span class="json-number">$2</span>');
		
		// Booleans and null
		highlighted = highlighted.replace(/(:)\s*(true|false|null)/g, '$1 <span class="json-boolean">$2</span>');
		
		// Brackets and braces
		highlighted = highlighted.replace(/([{}[\],])/g, '<span class="json-punctuation">$1</span>');
		
		// Highlight search terms
		if (highlight && highlight.trim()) {
			const searchRegex = new RegExp(`(${escapeRegex(highlight)})`, 'gi');
			highlighted = highlighted.replace(searchRegex, '<mark class="json-highlight">$1</mark>');
			
			// Count search results
			const matches = highlighted.match(searchRegex);
			searchResults = matches ? matches.length : 0;
		} else {
			searchResults = 0;
		}
		
		return highlighted;
	}

	function escapeHtml(text: string): string {
		const div = document.createElement('div');
		div.textContent = text;
		return div.innerHTML;
	}

	function escapeRegex(string: string): string {
		return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	}

	async function copyToClipboard() {
		try {
			const textToCopy = defaultOptions.enableFormatting ? 
				JSON.stringify(parsedJson, null, 2) : json;
			await navigator.clipboard.writeText(textToCopy);
			copied = true;
			toast.success('Copied to clipboard successfully!');
			setTimeout(() => { copied = false; }, 2000);
		} catch (error) {
			toast.error('Failed to copy to clipboard');
			dispatch('error', new Error('Failed to copy to clipboard'));
		}
	}

	function downloadJson() {
		try {
			const content = defaultOptions.enableFormatting ? 
				JSON.stringify(parsedJson, null, 2) : json;
			const blob = new Blob([content], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = 'data.json';
			a.click();
			URL.revokeObjectURL(url);
		} catch (error) {
			dispatch('error', new Error('Failed to download JSON'));
		}
	}

	function toggleExpanded() {
		expanded = !expanded;
	}

	function toggleSearch() {
		defaultOptions.enableSearch = !defaultOptions.enableSearch;
		if (defaultOptions.enableSearch) {
			setTimeout(() => searchInputElement?.focus(), 100);
		} else {
			searchTerm = '';
		}
	}

	function getJsonStats() {
		if (!parsedJson) return null;
		
		const stats = {
			keys: 0,
			objects: 0,
			arrays: 0,
			primitives: 0,
			depth: 0
		};

		function analyze(obj: any, currentDepth = 0) {
			stats.depth = Math.max(stats.depth, currentDepth);
			
			if (Array.isArray(obj)) {
				stats.arrays++;
				obj.forEach(item => analyze(item, currentDepth + 1));
			} else if (obj && typeof obj === 'object') {
				stats.objects++;
				Object.keys(obj).forEach(key => {
					stats.keys++;
					analyze(obj[key], currentDepth + 1);
				});
			} else {
				stats.primitives++;
			}
		}

		analyze(parsedJson);
		return stats;
	}

	$: stats = getJsonStats();
</script>

<div class="json-viewer" data-theme={defaultOptions.theme}>
	<!-- Header -->
	<div class="json-header">
		<div class="json-info">
			<span class="json-icon">📄</span>
			<span class="json-label">JSON Data</span>
			{#if stats}
				<span class="json-stats">
					{stats.keys} keys • {stats.objects} objects • {stats.arrays} arrays
				</span>
			{/if}
			{#if validationError}
				<span class="json-error">❌ Invalid JSON</span>
			{/if}
		</div>
		
		<div class="json-actions">
			{#if defaultOptions.enableSearch && parsedJson}
				<button 
					class="action-btn search-btn"
					class:active={defaultOptions.enableSearch}
					on:click={toggleSearch}
					title="Search JSON"
				>
					<Search class="w-4 h-4" />
				</button>
			{/if}
			
			{#if defaultOptions.collapsible}
				<button 
					class="action-btn expand-btn"
					on:click={toggleExpanded}
					title={expanded ? 'Collapse' : 'Expand'}
				>
					{#if expanded}
						<Minimize class="w-4 h-4" />
					{:else}
						<Expand class="w-4 h-4" />
					{/if}
				</button>
			{/if}
			
			{#if defaultOptions.enableDownload && parsedJson}
				<button 
					class="action-btn download-btn"
					on:click={downloadJson}
					title="Download JSON"
				>
					<Download class="w-4 h-4" />
					{#if defaultOptions.copyButtonStyle === 'text' || defaultOptions.copyButtonStyle === 'both'}
						<span>Download</span>
					{/if}
				</button>
			{/if}
			
			<button 
				class="action-btn copy-btn"
				on:click={copyToClipboard}
				title="Copy JSON"
			>
				{#if copied}
					<Check class="w-4 h-4 text-green-500" />
				{:else}
					<Copy class="w-4 h-4" />
				{/if}
				{#if defaultOptions.copyButtonStyle === 'text' || defaultOptions.copyButtonStyle === 'both'}
					<span>{copied ? 'Copied!' : 'Copy'}</span>
				{/if}
			</button>
		</div>
	</div>

	<!-- Search Bar -->
	{#if defaultOptions.enableSearch}
		<div class="json-search">
			<input 
				bind:this={searchInputElement}
				bind:value={searchTerm}
				type="text"
				placeholder="Search JSON content..."
				class="search-input"
			>
			{#if searchTerm && searchResults > 0}
				<span class="search-results">{searchResults} results</span>
			{/if}
		</div>
	{/if}

	<!-- Content -->
	<div class="json-content" class:expanded>
		{#if validationError}
			<div class="json-error-content">
				<div class="error-icon">⚠️</div>
				<div class="error-details">
					<h4>Invalid JSON</h4>
					<p>{validationError}</p>
					<details>
						<summary>Raw content</summary>
						<pre class="raw-json">{json}</pre>
					</details>
				</div>
			</div>
		{:else}
			<pre 
				class="json-pre"
				style={defaultOptions.maxHeight ? `max-height: ${defaultOptions.maxHeight}px` : ''}
			><code class="json-code">{@html formattedJson}</code></pre>
		{/if}
	</div>

	<!-- Footer with metadata -->
	{#if parsedJson && stats}
		<div class="json-footer">
			<div class="json-metadata">
				<span>Depth: {stats.depth}</span>
				<span>Size: {new Blob([json]).size} bytes</span>
				{#if searchTerm}
					<span>Found: {searchResults} matches</span>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.json-viewer {
		border-radius: 0.5rem;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		font-family: 'JetBrains Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
		font-size: 0.875rem;
		line-height: 1.5;
	}

	.json-viewer[data-theme="dark"] {
		border-color: #374151;
		background: #1f2937;
	}

	.json-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #dbeafe;
		border-bottom: 1px solid #3b82f6;
	}

	.json-viewer[data-theme="dark"] .json-header {
		background: #1e40af;
		border-bottom-color: #3b82f6;
	}

	.json-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #1e40af;
	}

	.json-viewer[data-theme="dark"] .json-info {
		color: #dbeafe;
	}

	.json-icon {
		font-size: 1.125rem;
	}

	.json-label {
		font-size: 0.875rem;
	}

	.json-stats {
		font-size: 0.75rem;
		color: #3b82f6;
		background: #eff6ff;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
	}

	.json-viewer[data-theme="dark"] .json-stats {
		color: #93c5fd;
		background: #1e3a8a;
	}

	.json-error {
		font-size: 0.75rem;
		color: #dc2626;
		background: #fee2e2;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
	}

	.json-viewer[data-theme="dark"] .json-error {
		color: #fca5a5;
		background: #7f1d1d;
	}

	.json-actions {
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
		color: #1e40af;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
	}

	.action-btn:hover {
		background: #eff6ff;
		color: #1e3a8a;
	}

	.json-viewer[data-theme="dark"] .action-btn {
		color: #93c5fd;
	}

	.json-viewer[data-theme="dark"] .action-btn:hover {
		background: #1e3a8a;
		color: #dbeafe;
	}

	.action-btn.active {
		background: #eff6ff;
		color: #1e3a8a;
	}

	.json-viewer[data-theme="dark"] .action-btn.active {
		background: #1e3a8a;
		color: #dbeafe;
	}

	.json-search {
		padding: 0.75rem 1rem;
		background: #f8fafc;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.json-viewer[data-theme="dark"] .json-search {
		background: #374151;
		border-bottom-color: #4b5563;
	}

	.search-input {
		flex: 1;
		padding: 0.375rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		background: #ffffff;
		color: #374151;
		font-size: 0.875rem;
	}

	.json-viewer[data-theme="dark"] .search-input {
		border-color: #4b5563;
		background: #1f2937;
		color: #f3f4f6;
	}

	.search-input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.search-results {
		font-size: 0.75rem;
		color: #6b7280;
		background: #f3f4f6;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
	}

	.json-viewer[data-theme="dark"] .search-results {
		color: #9ca3af;
		background: #4b5563;
	}

	.json-content {
		position: relative;
		overflow: auto;
	}

	.json-content.expanded {
		max-height: none !important;
	}

	.json-error-content {
		padding: 1.5rem;
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.error-icon {
		font-size: 2rem;
		color: #dc2626;
	}

	.error-details h4 {
		margin: 0 0 0.5rem 0;
		color: #dc2626;
		font-size: 1rem;
		font-weight: 600;
	}

	.error-details p {
		margin: 0 0 1rem 0;
		color: #6b7280;
		font-size: 0.875rem;
	}

	.raw-json {
		margin-top: 0.5rem;
		padding: 0.75rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		max-height: 150px;
		overflow: auto;
	}

	.json-viewer[data-theme="dark"] .raw-json {
		background: #374151;
		border-color: #4b5563;
		color: #f3f4f6;
	}

	.json-pre {
		margin: 0;
		padding: 1rem;
		background: #1e1e1e;
		color: #d4d4d4;
		overflow: auto;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.json-code {
		background: none;
		padding: 0;
		font-family: inherit;
		font-size: inherit;
		line-height: inherit;
	}

	/* JSON syntax highlighting */
	.json-code :global(.json-key) {
		color: #79c0ff;
		font-weight: 600;
	}

	.json-code :global(.json-colon) {
		color: #e6edf3;
	}

	.json-code :global(.json-string) {
		color: #a5d6ff;
	}

	.json-code :global(.json-number) {
		color: #79c0ff;
	}

	.json-code :global(.json-boolean) {
		color: #ff7b72;
		font-weight: 600;
	}

	.json-code :global(.json-punctuation) {
		color: #e6edf3;
	}

	.json-code :global(.json-highlight) {
		background: #fbbf24;
		color: #92400e;
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
	}

	.json-footer {
		padding: 0.5rem 1rem;
		background: #f8fafc;
		border-top: 1px solid #e5e7eb;
	}

	.json-viewer[data-theme="dark"] .json-footer {
		background: #374151;
		border-top-color: #4b5563;
	}

	.json-metadata {
		display: flex;
		gap: 1rem;
		font-size: 0.75rem;
		color: #6b7280;
	}

	.json-viewer[data-theme="dark"] .json-metadata {
		color: #9ca3af;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.json-viewer {
			font-size: 0.75rem;
		}

		.json-header {
			padding: 0.5rem 0.75rem;
			flex-direction: column;
			gap: 0.5rem;
			align-items: stretch;
		}

		.json-actions {
			justify-content: center;
			gap: 0.25rem;
		}

		.action-btn {
			padding: 0.25rem 0.375rem;
		}

		.json-stats {
			display: none;
		}

		.json-metadata {
			flex-direction: column;
			gap: 0.25rem;
		}
	}
</style>
