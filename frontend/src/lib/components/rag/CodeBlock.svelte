<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { Copy, Check, Download, Play } from '@lucide/svelte/icons';
	import { toast } from 'svelte-sonner';
	import Prism from 'prismjs';
	import 'prismjs/themes/prism-tomorrow.css';
	
	// Import language components dynamically
	import 'prismjs/components/prism-javascript';
	import 'prismjs/components/prism-typescript';
	import 'prismjs/components/prism-python';
	import 'prismjs/components/prism-sql';
	import 'prismjs/components/prism-css';
	import 'prismjs/components/prism-scss';
	import 'prismjs/components/prism-html';
	import 'prismjs/components/prism-json';
	import 'prismjs/components/prism-bash';
	import 'prismjs/components/prism-yaml';
	import 'prismjs/components/prism-markdown';
	import 'prismjs/components/prism-java';
	import 'prismjs/components/prism-cpp';
	import 'prismjs/components/prism-c';
	import 'prismjs/components/prism-php';
	import 'prismjs/components/prism-ruby';
	import 'prismjs/components/prism-go';
	import 'prismjs/components/prism-rust';
	import 'prismjs/components/prism-swift';

	const dispatch = createEventDispatcher();

	export let code: string;
	export let language: string = 'text';
	export let options: CodeBlockOptions = {};

	interface CodeBlockOptions {
		enableHighlighting?: boolean;
		copyButtonStyle?: 'icon' | 'text' | 'both';
		theme?: 'light' | 'dark' | 'auto';
		showLineNumbers?: boolean;
		enableDownload?: boolean;
		enableRun?: boolean;
		filename?: string;
	}

	let codeElement: HTMLElement;
	let copied = false;
	let highlightedCode = '';
	let loading = true;

	// Default options
	const defaultOptions: CodeBlockOptions = {
		enableHighlighting: true,
		copyButtonStyle: 'icon',
		theme: 'auto',
		showLineNumbers: false,
		enableDownload: false,
		enableRun: false,
		...options
	};

	// Language mappings and metadata
	const languageInfo: Record<string, {icon: string, name: string, extension: string, runnable?: boolean}> = {
		javascript: { icon: '🟨', name: 'JavaScript', extension: 'js', runnable: true },
		typescript: { icon: '🔷', name: 'TypeScript', extension: 'ts', runnable: true },
		python: { icon: '🐍', name: 'Python', extension: 'py', runnable: true },
		sql: { icon: '🗃️', name: 'SQL', extension: 'sql', runnable: true },
		html: { icon: '🌐', name: 'HTML', extension: 'html' },
		css: { icon: '🎨', name: 'CSS', extension: 'css' },
		scss: { icon: '🎨', name: 'SCSS', extension: 'scss' },
		json: { icon: '📄', name: 'JSON', extension: 'json' },
		bash: { icon: '⚡', name: 'Bash', extension: 'sh', runnable: true },
		shell: { icon: '⚡', name: 'Shell', extension: 'sh', runnable: true },
		yaml: { icon: '📋', name: 'YAML', extension: 'yml' },
		markdown: { icon: '📝', name: 'Markdown', extension: 'md' },
		java: { icon: '☕', name: 'Java', extension: 'java', runnable: true },
		cpp: { icon: '⚙️', name: 'C++', extension: 'cpp', runnable: true },
		c: { icon: '⚙️', name: 'C', extension: 'c', runnable: true },
		php: { icon: '🐘', name: 'PHP', extension: 'php', runnable: true },
		ruby: { icon: '💎', name: 'Ruby', extension: 'rb', runnable: true },
		go: { icon: '🐹', name: 'Go', extension: 'go', runnable: true },
		rust: { icon: '🦀', name: 'Rust', extension: 'rs', runnable: true },
		swift: { icon: '🍎', name: 'Swift', extension: 'swift', runnable: true }
	};

	onMount(async () => {
		try {
			await highlightCode();
		} catch (error) {
			dispatch('error', error);
			highlightedCode = escapeHtml(code);
		} finally {
			loading = false;
		}
	});

	async function highlightCode() {
		if (!defaultOptions.enableHighlighting) {
			highlightedCode = escapeHtml(code);
			return;
		}

		try {
			// Normalize language name
			const normalizedLang = normalizeLanguage(language);
			
			// Check if language is supported
			if (Prism.languages[normalizedLang]) {
				highlightedCode = Prism.highlight(code, Prism.languages[normalizedLang], normalizedLang);
			} else {
				// Fallback to plain text
				highlightedCode = escapeHtml(code);
			}
		} catch (error) {
			console.warn(`Failed to highlight ${language}:`, error);
			highlightedCode = escapeHtml(code);
		}
	}

	function normalizeLanguage(lang: string): string {
		const mappings: Record<string, string> = {
			'js': 'javascript',
			'ts': 'typescript',
			'py': 'python',
			'sh': 'bash',
			'yml': 'yaml',
			'md': 'markdown'
		};
		return mappings[lang] || lang;
	}

	function escapeHtml(text: string): string {
		const div = document.createElement('div');
		div.textContent = text;
		return div.innerHTML;
	}

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(code);
			copied = true;
			toast.success('Copied to clipboard successfully!');
			setTimeout(() => { copied = false; }, 2000);
		} catch (error) {
			toast.error('Failed to copy to clipboard');
			dispatch('error', new Error('Failed to copy to clipboard'));
		}
	}

	function downloadCode() {
		try {
			const info = languageInfo[language] || { extension: 'txt' };
			const filename = defaultOptions.filename || `code.${info.extension}`;
			const blob = new Blob([code], { type: 'text/plain' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			URL.revokeObjectURL(url);
		} catch (error) {
			dispatch('error', new Error('Failed to download code'));
		}
	}

	function runCode() {
		// This would integrate with code execution services
		// For now, just dispatch an event
		dispatch('run', { code, language });
	}

	function getLangInfo() {
		return languageInfo[language] || { icon: '📝', name: language || 'Code', extension: 'txt' };
	}

	// Re-highlight when code or language changes
	$: if (code || language) {
		highlightCode();
	}
</script>

<div class="code-block" data-language={language} data-theme={defaultOptions.theme}>
	<!-- Header -->
	<div class="code-header">
		<div class="language-info">
			<span class="language-icon">{getLangInfo().icon}</span>
			<span class="language-name">{getLangInfo().name}</span>
			{#if defaultOptions.filename}
				<span class="filename">{defaultOptions.filename}</span>
			{/if}
		</div>
		
		<div class="code-actions">
			{#if defaultOptions.enableRun && getLangInfo().runnable}
				<button 
					class="action-btn run-btn"
					on:click={runCode}
					title="Run code"
				>
					<Play class="w-4 h-4" />
					{#if defaultOptions.copyButtonStyle === 'text' || defaultOptions.copyButtonStyle === 'both'}
						<span>Run</span>
					{/if}
				</button>
			{/if}
			
			{#if defaultOptions.enableDownload}
				<button 
					class="action-btn download-btn"
					on:click={downloadCode}
					title="Download code"
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
				title="Copy code"
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

	<!-- Code Content -->
	<div class="code-content">
		{#if loading}
			<div class="code-loading">
				<div class="loading-spinner"></div>
				<span>Highlighting code...</span>
			</div>
		{:else}
			<pre 
				bind:this={codeElement}
				class="code-pre"
				class:line-numbers={defaultOptions.showLineNumbers}
			><code class="language-{normalizeLanguage(language)}">{@html highlightedCode}</code></pre>
		{/if}
	</div>
</div>

<style>
	.code-block {
		border-radius: 0.5rem;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		font-family: 'JetBrains Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
		font-size: 0.875rem;
		line-height: 1.5;
	}

	.code-block[data-theme="dark"] {
		border-color: #374151;
		background: #1f2937;
	}

	.code-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #f8fafc;
		border-bottom: 1px solid #e5e7eb;
	}

	.code-block[data-theme="dark"] .code-header {
		background: #374151;
		border-bottom-color: #4b5563;
	}

	.language-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #374151;
	}

	.code-block[data-theme="dark"] .language-info {
		color: #d1d5db;
	}

	.language-icon {
		font-size: 1.125rem;
	}

	.language-name {
		font-size: 0.875rem;
	}

	.filename {
		font-size: 0.75rem;
		color: #6b7280;
		background: #e5e7eb;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
	}

	.code-block[data-theme="dark"] .filename {
		color: #9ca3af;
		background: #4b5563;
	}

	.code-actions {
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
		color: #6b7280;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
	}

	.action-btn:hover {
		background: #e5e7eb;
		color: #374151;
	}

	.code-block[data-theme="dark"] .action-btn {
		color: #9ca3af;
	}

	.code-block[data-theme="dark"] .action-btn:hover {
		background: #4b5563;
		color: #f3f4f6;
	}

	.run-btn:hover {
		background: #dcfce7;
		color: #166534;
	}

	.code-block[data-theme="dark"] .run-btn:hover {
		background: #166534;
		color: #dcfce7;
	}

	.download-btn:hover {
		background: #dbeafe;
		color: #1e40af;
	}

	.code-block[data-theme="dark"] .download-btn:hover {
		background: #1e40af;
		color: #dbeafe;
	}

	.copy-btn:hover {
		background: #fef3c7;
		color: #92400e;
	}

	.code-block[data-theme="dark"] .copy-btn:hover {
		background: #92400e;
		color: #fef3c7;
	}

	.code-content {
		position: relative;
		overflow-x: auto;
	}

	.code-loading {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 2rem;
		color: #6b7280;
	}

	.loading-spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid #e5e7eb;
		border-top: 2px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.code-pre {
		margin: 0;
		padding: 1rem;
		background: #1e1e1e;
		color: #d4d4d4;
		overflow-x: auto;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.code-pre code {
		background: none;
		padding: 0;
		font-family: inherit;
		font-size: inherit;
		line-height: inherit;
	}

	/* Line numbers */
	.line-numbers {
		counter-reset: linenumber;
	}

	.line-numbers code {
		counter-increment: linenumber;
	}

	.line-numbers code::before {
		content: counter(linenumber);
		position: absolute;
		left: 0;
		width: 2.5rem;
		padding-right: 0.5rem;
		color: #6b7280;
		text-align: right;
		border-right: 1px solid #374151;
		margin-right: 1rem;
	}

	.line-numbers .code-pre {
		padding-left: 4rem;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.code-block {
			font-size: 0.75rem;
		}

		.code-header {
			padding: 0.5rem 0.75rem;
		}

		.code-actions {
			gap: 0.25rem;
		}

		.action-btn {
			padding: 0.25rem 0.375rem;
		}

		.language-name,
		.filename {
			display: none;
		}
	}
</style>
