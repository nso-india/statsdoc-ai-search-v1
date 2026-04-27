<script lang="ts">
	import { onMount } from 'svelte';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import CodeBlock from './CodeBlock.svelte';
	import JsonViewer from './JsonViewer.svelte';
	import MarkdownRenderer from './MarkdownRenderer.svelte';
	import IframeEmbed from './IframeEmbed.svelte';
	import ChartRenderer from './ChartRenderer.svelte';
	import TableRenderer from './TableRenderer.svelte';
	import ErrorBoundary from './ErrorBoundary.svelte';

	export let response: string;
	export let messageId: string;
	export let options: ResponseRendererOptions = {};

	interface ContentBlock {
		type: 'code' | 'json' | 'markdown' | 'iframe' | 'chart' | 'table' | 'html';
		content: string;
		language?: string;
		metadata?: any;
		id: string;
	}

	interface ResponseRendererOptions {
		enableCodeHighlighting?: boolean;
		enableJsonFormatting?: boolean;
		enableIframes?: boolean;
		enableCharts?: boolean;
		maxIframeHeight?: number;
		theme?: 'light' | 'dark' | 'auto';
		copyButtonStyle?: 'icon' | 'text' | 'both';
		onContentParsed?: (blocks: ContentBlock[]) => void;
		onError?: (error: Error, block?: ContentBlock) => void;
	}

	let parsedBlocks: ContentBlock[] = [];
	let isLoading = true;
	let parseError: string | null = null;

	// Default options
	const defaultOptions: ResponseRendererOptions = {
		enableCodeHighlighting: true,
		enableJsonFormatting: true,
		enableIframes: true,
		enableCharts: true,
		maxIframeHeight: 600,
		theme: 'auto',
		copyButtonStyle: 'icon',
		...options
	};

	onMount(async () => {
		await parseResponse();
	});

	async function parseResponse() {
		try {
			isLoading = true;
			parseError = null;
			
			const blocks = await parseContent(response);
			parsedBlocks = blocks;
			
			if (defaultOptions.onContentParsed) {
				defaultOptions.onContentParsed(blocks);
			}
		} catch (error) {
			parseError = error instanceof Error ? error.message : 'Failed to parse response';
			if (defaultOptions.onError) {
				defaultOptions.onError(error instanceof Error ? error : new Error(parseError));
			}
		} finally {
			isLoading = false;
		}
	}

	async function parseContent(content: string): Promise<ContentBlock[]> {
		const blocks: ContentBlock[] = [];
		let blockIdCounter = 0;

		// First, let's find all tables using a line-by-line approach (most reliable)
		const foundBlocks: Array<{start: number, end: number, type: string, content: string, language?: string, metadata?: any}> = [];
		
		// Find tables first (highest priority)
		const tableBlocks = findMarkdownTables(content);
		console.log('Found table blocks:', tableBlocks); // Debug
		foundBlocks.push(...tableBlocks);

		// Regex patterns for other content types
		const patterns = {
			codeBlock: /```(\w+)?\n([\s\S]*?)```/g,
			chart: /<chart[^>]*>([\s\S]*?)<\/chart>/g,
			iframe: /<iframe[^>]*>[\s\S]*?<\/iframe>/g,
			htmlTable: /<table[^>]*>[\s\S]*?<\/table>/g
		};

		let lastIndex = 0;

		// Find all code blocks
		let match;
		while ((match = patterns.codeBlock.exec(content)) !== null) {
			const language = match[1] || 'text';
			const codeContent = match[2].trim();
			
			foundBlocks.push({
				start: match.index,
				end: match.index + match[0].length,
				type: isValidJSON(codeContent) && language === 'json' ? 'json' : 'code',
				content: codeContent,
				language
			});
		}

		// Find chart blocks
		patterns.codeBlock.lastIndex = 0;
		while ((match = patterns.chart.exec(content)) !== null) {
			try {
				const chartConfig = JSON.parse(match[1]);
				foundBlocks.push({
					start: match.index,
					end: match.index + match[0].length,
					type: 'chart',
					content: match[1],
					metadata: chartConfig
				});
			} catch (e) {
				// If chart config is invalid, treat as HTML
				foundBlocks.push({
					start: match.index,
					end: match.index + match[0].length,
					type: 'html',
					content: match[0]
				});
			}
		}

		// Find iframe blocks
		patterns.chart.lastIndex = 0;
		while ((match = patterns.iframe.exec(content)) !== null) {
			foundBlocks.push({
				start: match.index,
				end: match.index + match[0].length,
				type: 'iframe',
				content: match[0]
			});
		}

		// Find HTML tables
		patterns.iframe.lastIndex = 0;
		while ((match = patterns.htmlTable.exec(content)) !== null) {
			foundBlocks.push({
				start: match.index,
				end: match.index + match[0].length,
				type: 'table',
				content: match[0]
			});
		}

		// Sort blocks by position
		foundBlocks.sort((a, b) => a.start - b.start);

		// Extract text between blocks and create final block list
		lastIndex = 0;
		for (const block of foundBlocks) {
			// Add text before this block
			if (block.start > lastIndex) {
				const textContent = content.slice(lastIndex, block.start).trim();
				if (textContent) {
					blocks.push({
						type: 'markdown',
						content: textContent,
						id: `${messageId}-block-${blockIdCounter++}`
					});
				}
			}

			// Add the block
			blocks.push({
				type: block.type as ContentBlock['type'],
				content: block.content,
				language: block.language,
				metadata: block.metadata,
				id: `${messageId}-block-${blockIdCounter++}`
			});

			lastIndex = block.end;
		}

		// Add remaining text
		if (lastIndex < content.length) {
			const remainingText = content.slice(lastIndex).trim();
			if (remainingText) {
				blocks.push({
					type: 'markdown',
					content: remainingText,
					id: `${messageId}-block-${blockIdCounter++}`
				});
			}
		}

		// If no special blocks found, treat entire content as markdown
		if (blocks.length === 0 && content.trim()) {
			blocks.push({
				type: 'markdown',
				content: content.trim(),
				id: `${messageId}-block-${blockIdCounter++}`
			});
		}

		return blocks;
	}

	function findMarkdownTables(content: string): Array<{start: number, end: number, type: string, content: string}> {
		const tables: Array<{start: number, end: number, type: string, content: string}> = [];
		const lines = content.split('\n');
		
		for (let i = 0; i < lines.length - 1; i++) {
			const currentLine = lines[i];
			const nextLine = lines[i + 1];
			
			// Check if current line has pipes and next line is a separator
			if (currentLine.includes('|') && nextLine && isSeparatorLine(nextLine)) {
				// Found table start
				let tableStart = i;
				let tableEnd = i + 2; // Include header and separator
				
				// Find all consecutive table rows
				while (tableEnd < lines.length) {
					const line = lines[tableEnd];
					if (line.trim() === '' || !line.includes('|')) {
						break;
					}
					tableEnd++;
				}
				
				// Must have at least header + separator + 1 data row
				if (tableEnd > i + 2) {
					const tableLines = lines.slice(tableStart, tableEnd);
					const tableContent = tableLines.join('\n');
					
					// Find the actual start and end positions in the content
					const contentStart = content.indexOf(currentLine);
					const contentEnd = contentStart + tableContent.length;
					
					tables.push({
						start: contentStart,
						end: contentEnd,
						type: 'table',
						content: tableContent
					});
					
					// Skip past this table
					i = tableEnd - 1;
				}
			}
		}
		
		return tables;
	}

	function isSeparatorLine(line: string): boolean {
		const trimmed = line.trim();
		// Must contain only pipes, dashes, colons, and spaces
		return /^[\|\-\:\s]+$/.test(trimmed) && trimmed.includes('-') && trimmed.includes('|');
	}

	function isValidJSON(str: string): boolean {
		try {
			JSON.parse(str);
			return true;
		} catch {
			return false;
		}
	}

	function isValidMarkdownTable(tableContent: string): boolean {
		const lines = tableContent.split('\n').filter(line => line.trim());
		
		// Must have at least 2 lines (header + separator)
		if (lines.length < 2) return false;
		
		// All lines must contain pipes
		if (!lines.every(line => line.includes('|'))) return false;
		
		// Second line should be separator with dashes, colons, and pipes
		const separatorLine = lines[1];
		if (!/^\|?[-:| ]+\|?$/.test(separatorLine.trim())) return false;
		
		// Header and separator should have similar column count
		const headerCols = lines[0].split('|').length;
		const separatorCols = separatorLine.split('|').length;
		
		return Math.abs(headerCols - separatorCols) <= 1;
	}

	function handleError(error: Error, block?: ContentBlock) {
		console.error('ResponseRenderer error:', error, block);
		if (defaultOptions.onError) {
			defaultOptions.onError(error, block);
		}
	}

	// Re-parse when response changes
	$: if (response) {
		parseResponse();
	}
</script>

<div class="response-renderer" data-theme={defaultOptions.theme}>
	{#if isLoading}
		<div class="flex items-center justify-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-gray-600 dark:text-gray-400">Processing response...</span>
		</div>
	{:else if parseError}
		<ErrorBoundary error={parseError} />
	{:else if parsedBlocks.length === 0}
		<div class="text-center py-8 text-gray-500 dark:text-gray-400">
			<p>No content to display</p>
		</div>
	{:else}
		{#each parsedBlocks as block, index (block.id)}
			<div class="content-block mb-4" data-block-type={block.type} data-block-index={index}>
				<ErrorBoundary>
					{#if block.type === 'code'}
						<CodeBlock 
							code={block.content} 
							language={block.language || 'text'}
							options={{
								enableHighlighting: defaultOptions.enableCodeHighlighting,
								copyButtonStyle: defaultOptions.copyButtonStyle,
								theme: defaultOptions.theme
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'json'}
						<JsonViewer 
							json={block.content}
							options={{
								enableFormatting: defaultOptions.enableJsonFormatting,
								copyButtonStyle: defaultOptions.copyButtonStyle,
								theme: defaultOptions.theme
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'markdown'}
						<MarkdownRenderer 
							markdown={block.content}
							options={{
								theme: defaultOptions.theme
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'iframe' && defaultOptions.enableIframes}
						<IframeEmbed 
							html={block.content}
							options={{
								maxHeight: defaultOptions.maxIframeHeight,
								theme: defaultOptions.theme
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'chart' && defaultOptions.enableCharts}
						<ChartRenderer 
							config={block.metadata}
							options={{
								theme: defaultOptions.theme
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'table'}
						<TableRenderer 
							content={block.content}
							options={{
								theme: defaultOptions.theme,
								searchable: true,
								downloadable: true,
								sortable: false
							}}
							on:error={(e) => handleError(e.detail, block)}
						/>
					{:else if block.type === 'html'}
						<div class="html-content">
							{@html DOMPurify.sanitize(block.content)}
						</div>
					{/if}
				</ErrorBoundary>
			</div>
		{/each}
	{/if}
</div>

<style>
	.response-renderer {
		max-width: 100%;
		overflow-wrap: break-word;
		word-wrap: break-word;
	}

	.content-block {
		position: relative;
		scroll-margin-top: 2rem;
	}

	.html-content {
		padding: 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		background: #f9fafb;
	}

	.response-renderer[data-theme="dark"] .html-content {
		border-color: #374151;
		background: #1f2937;
		color: #f3f4f6;
	}

	@media (max-width: 768px) {
		.response-renderer {
			font-size: 0.875rem;
		}
	}
</style>
