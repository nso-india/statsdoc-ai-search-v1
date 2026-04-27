import { SvelteComponent } from 'svelte';

export interface MarkdownRendererProps {
	markdown: string;
	theme?: 'light' | 'dark' | 'auto';
	openLinksInNewTab?: boolean;
	allowIframes?: boolean;
	className?: string;
}

export interface MarkdownRendererEvents {
	rendered: CustomEvent<{ html: string }>;
	error: CustomEvent<Error>;
}

declare const MarkdownRenderer: SvelteComponent<MarkdownRendererProps, MarkdownRendererEvents>;
export default MarkdownRenderer;
