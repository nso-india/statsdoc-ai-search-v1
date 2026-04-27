<script lang="ts">
	import { marked } from 'marked';
	import hljs from 'highlight.js';
	import 'highlight.js/styles/github.css';
	import DOMPurify from 'dompurify';
	import { onMount, afterUpdate } from 'svelte';
	import { toast } from 'svelte-sonner';

	export let content: string = '';
	export let theme: 'light' | 'dark' | 'auto' = 'auto';
	export let className: string = '';

	let renderedContent = '';
	let markdownContainer: HTMLElement;

	// Simple marked configuration with syntax highlighting
	marked.setOptions({
		gfm: true,
		breaks: true,
		highlight: function(code: string, lang: string) {
			if (lang && hljs.getLanguage(lang)) {
				try {
					return hljs.highlight(code, { language: lang }).value;
				} catch (err) {
					console.error('Highlight error:', err);
				}
			}
			return hljs.highlightAuto(code).value;
		}
	});

	async function renderMarkdown() {
		// Ensure content is a string before calling trim
		const contentStr = typeof content === 'string' ? content : String(content || '');
		if (!contentStr || !contentStr.trim()) {
			renderedContent = '';
			return;
		}

		try {
			const html = await marked.parse(contentStr);
			const sanitized = DOMPurify.sanitize(html, {
				ADD_ATTR: ['target', 'rel', 'class'],
				ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp|data):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
			});
			renderedContent = sanitized;
		} catch (error) {
			console.error('Error rendering markdown:', error);
			renderedContent = `<p class="error">Error rendering content: ${error}</p>`;
		}
	}

	// Copy to clipboard functionality
	async function copyToClipboard(text: string) {
		try {
			await navigator.clipboard.writeText(text);
			toast.success('Copied to clipboard successfully!');
			return true;
		} catch (err) {
			console.error('Failed to copy text:', err);
			toast.error('Failed to copy to clipboard');
			return false;
		}
	}

	// Add simple copy buttons to code blocks
	function addCopyButtons() {
		if (!markdownContainer) return;
		
		const codeBlocks = markdownContainer.querySelectorAll('pre code');
		codeBlocks.forEach((block) => {
			const pre = block.parentElement;
			if (pre && !pre.querySelector('.copy-button')) {
				const button = document.createElement('button');
				button.className = 'copy-button';
				button.innerHTML = `
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
						<path d="m4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
					</svg>
				`;
				button.addEventListener('click', async () => {
					const success = await copyToClipboard(block.textContent || '');
					if (success) {
						button.innerHTML = `
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<polyline points="20,6 9,17 4,12"></polyline>
							</svg>
						`;
						setTimeout(() => {
							button.innerHTML = `
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
									<path d="m4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
								</svg>
							`;
						}, 2000);
					}
				});
				pre.style.position = 'relative';
				pre.appendChild(button);
			}
		});
	}

	onMount(() => {
		// Initialize highlight.js
		hljs.configure({
			languages: ['javascript', 'typescript', 'python', 'json', 'html', 'css', 'sql', 'bash', 'shell'],
			ignoreUnescapedHTML: true
		});
		renderMarkdown();
	});

	afterUpdate(() => {
		addCopyButtons();
		// Re-highlight any new code blocks
		if (markdownContainer) {
			const codeBlocks = markdownContainer.querySelectorAll('pre code:not(.hljs)');
			codeBlocks.forEach((block) => {
				hljs.highlightElement(block as HTMLElement);
			});
		}
	});

	$: if (content) {
		renderMarkdown();
	}
</script>

<div 
	bind:this={markdownContainer}
	class="markdown-renderer {className}" 
	class:theme-light={theme === 'light'} 
	class:theme-dark={theme === 'dark'}
	class:theme-auto={theme === 'auto'}
>
	{@html renderedContent}
</div>

<style>
	.markdown-renderer {
		line-height: 1.6;
		color: #1f2937;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
		word-wrap: break-word;
		overflow-wrap: break-word;
	}

	/* Typography */
	:global(.markdown-renderer h1),
	:global(.markdown-renderer h2),
	:global(.markdown-renderer h3),
	:global(.markdown-renderer h4),
	:global(.markdown-renderer h5),
	:global(.markdown-renderer h6) {
		margin: 1.5em 0 0.5em 0;
		font-weight: 600;
		line-height: 1.25;
		color: #1f2937;
	}

	:global(.markdown-renderer h1) { 
		font-size: 2em; 
		border-bottom: 1px solid #e5e7eb; 
		padding-bottom: 0.3em; 
	}
	
	:global(.markdown-renderer h2) { 
		font-size: 1.5em; 
		border-bottom: 1px solid #e5e7eb; 
		padding-bottom: 0.3em; 
	}
	
	:global(.markdown-renderer h3) { font-size: 1.25em; }
	:global(.markdown-renderer h4) { font-size: 1em; }
	:global(.markdown-renderer h5) { font-size: 0.875em; }
	:global(.markdown-renderer h6) { 
		font-size: 0.85em; 
		color: #6b7280; 
	}

	:global(.markdown-renderer p) {
		margin: 1em 0;
		line-height: 1.7;
	}

	/* Lists */
	:global(.markdown-renderer ul),
	:global(.markdown-renderer ol) {
		margin: 1em 0;
		padding-left: 2em;
	}

	:global(.markdown-renderer li) {
		margin: 0.25em 0;
	}

	/* Blockquotes */
	:global(.markdown-renderer blockquote) {
		margin: 1em 0;
		padding: 0 1em;
		border-left: 4px solid #d1d5db;
		color: #6b7280;
		font-style: italic;
		background: #e9e9e980;
		border-radius: 0 6px 6px 0;
	}

	/* Inline Code */
	:global(.markdown-renderer code) {
		background-color: #e9e9e980;
		color: #1f2937;
		padding: 0.2em 0.4em;
		border-radius: 3px;
		font-size: 0.9em;
		font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, 'Courier New', monospace;
		border: 1px solid #d1d5db;
	}

	/* Code Blocks */
	:global(.markdown-renderer pre) {
		background-color: #f8f9fa;
		border: 1px solid #e9ecef;
		border-radius: 8px;
		overflow-x: auto;
		margin: 1.5em 0;
		position: relative;
		padding: 1em;
	}

	:global(.markdown-renderer pre code) {
		background: none;
		padding: 0;
		border: none;
		border-radius: 0;
		font-size: 0.875em;
		font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, 'Courier New', monospace;
		line-height: 1.5;
		color: #1f2937;
		display: block;
	}

	/* Enhanced syntax highlighting styles */
	:global(.markdown-renderer .hljs) {
		background: transparent !important;
		color: #1f2937 !important;
		display: block;
		overflow-x: auto;
		padding: 0;
	}

	/* GitHub-style syntax highlighting */
	:global(.markdown-renderer .hljs-keyword),
	:global(.markdown-renderer .hljs-selector-tag),
	:global(.markdown-renderer .hljs-subst) { 
		color: #d73a49; 
		font-weight: bold; 
	}

	:global(.markdown-renderer .hljs-string),
	:global(.markdown-renderer .hljs-attr),
	:global(.markdown-renderer .hljs-symbol),
	:global(.markdown-renderer .hljs-bullet),
	:global(.markdown-renderer .hljs-addition) { 
		color: #032f62; 
	}

	:global(.markdown-renderer .hljs-number),
	:global(.markdown-renderer .hljs-literal),
	:global(.markdown-renderer .hljs-built_in) { 
		color: #005cc5; 
	}

	:global(.markdown-renderer .hljs-comment),
	:global(.markdown-renderer .hljs-quote) { 
		color: #6a737d; 
		font-style: italic; 
	}

	:global(.markdown-renderer .hljs-function),
	:global(.markdown-renderer .hljs-title),
	:global(.markdown-renderer .hljs-class),
	:global(.markdown-renderer .hljs-type) { 
		color: #6f42c1; 
		font-weight: 600;
	}

	:global(.markdown-renderer .hljs-variable),
	:global(.markdown-renderer .hljs-name),
	:global(.markdown-renderer .hljs-tag) { 
		color: #e36209; 
	}

	:global(.markdown-renderer .hljs-regexp),
	:global(.markdown-renderer .hljs-link) { 
		color: #032f62; 
	}

	:global(.markdown-renderer .hljs-meta),
	:global(.markdown-renderer .hljs-doctag) { 
		color: #6a737d; 
	}

	:global(.markdown-renderer .hljs-section),
	:global(.markdown-renderer .hljs-selector-id) { 
		color: #005cc5; 
		font-weight: bold; 
	}

	:global(.markdown-renderer .hljs-deletion) { 
		color: #d73a49; 
		background-color: #ffeef0; 
	}

	:global(.markdown-renderer .hljs-addition) { 
		color: #28a745; 
		background-color: #f0fff4; 
	}

	:global(.markdown-renderer .copy-button) {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid #d1d5db;
		border-radius: 6px;
		color: #6b7280;
		cursor: pointer;
		transition: all 0.2s ease;
		font-family: inherit;
		opacity: 1;
		backdrop-filter: blur(4px);
	}

	:global(.markdown-renderer .copy-button:hover) {
		background: rgba(255, 255, 255, 1);
		border-color: #9ca3af;
		color: #374151;
		transform: scale(1.05);
	}

	:global(.markdown-renderer .copy-button svg) {
		flex-shrink: 0;
	}

	/* Tables */
	:global(.markdown-renderer table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1.5em 0;
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		font-size: 0.875em;
		background: #ffffff;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
	}

	:global(.markdown-renderer th),
	:global(.markdown-renderer td) {
		padding: 0.75em 1em;
		text-align: left;
		border-bottom: 1px solid #e5e7eb;
		border-right: 1px solid #e5e7eb;
	}

	:global(.markdown-renderer th:last-child),
	:global(.markdown-renderer td:last-child) {
		border-right: none;
	}

	:global(.markdown-renderer th) {
		background-color: #f8f9fa;
		font-weight: 600;
		color: #1f2937;
		border-bottom: 2px solid #e5e7eb;
	}

	:global(.markdown-renderer tbody tr:nth-child(even)) {
		background-color: #fbfcfd;
	}

	:global(.markdown-renderer tbody tr:hover) {
		background-color: #f1f3f4;
	}

	:global(.markdown-renderer tbody tr:last-child td) {
		border-bottom: none;
	}

	/* Links */
	:global(.markdown-renderer a) {
		color: #2563eb;
		text-decoration: none;
		border-bottom: 1px solid transparent;
		transition: border-color 0.2s ease;
	}

	:global(.markdown-renderer a:hover) {
		border-bottom-color: #2563eb;
	}

	/* Images */
	:global(.markdown-renderer img) {
		max-width: 100%;
		height: auto;
		border-radius: 6px;
		margin: 1em 0;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
	}

	/* Horizontal Rules */
	:global(.markdown-renderer hr) {
		border: none;
		border-top: 1px solid #e5e7eb;
		margin: 2em 0;
	}

	/* Error Messages */
	:global(.markdown-renderer .error) {
		color: #dc2626;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 6px;
		padding: 1em;
		margin: 1em 0;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.markdown-renderer {
			font-size: 0.875em;
		}

		:global(.markdown-renderer pre) {
			padding: 0.75em;
		}

		:global(.markdown-renderer table) {
			font-size: 0.75em;
		}
	}
</style>