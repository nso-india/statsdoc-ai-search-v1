<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		size?: 'sm' | 'md' | 'lg' | 'xl';
		variant?: 'primary' | 'muted' | 'accent';
		text?: string;
		showText?: boolean;
	};

	export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
	export let variant: 'primary' | 'muted' | 'accent' = 'primary';
	export let text: string = 'Loading...';
	export let showText: boolean = false;

	let className: $$Props["class"] = undefined;
	export { className as class };

	const sizeClasses = {
		sm: 'h-4 w-4',
		md: 'h-6 w-6', 
		lg: 'h-8 w-8',
		xl: 'h-12 w-12'
	};

	const variantClasses = {
		primary: 'text-primary',
		muted: 'text-muted-foreground',
		accent: 'text-accent-foreground'
	};

	const textSizeClasses = {
		sm: 'text-xs',
		md: 'text-sm',
		lg: 'text-base',
		xl: 'text-lg'
	};
</script>

<div class={cn("flex items-center justify-center", className)} {...$$restProps}>
	<div class="flex flex-col items-center space-y-2">
		<svg
			class={cn(
				"animate-spin",
				sizeClasses[size],
				variantClasses[variant]
			)}
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
		>
			<circle
				class="opacity-25"
				cx="12"
				cy="12"
				r="10"
				stroke="currentColor"
				stroke-width="4"
			></circle>
			<path
				class="opacity-75"
				fill="currentColor"
				d="m12 2 0 4c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8c0-1.57-.45-3.03-1.24-4.26l2.83-2.83c1.52 2.14 2.41 4.75 2.41 7.59 0 7.18-5.82 13-13 13s-13-5.82-13-13 5.82-13 13-13z"
			></path>
		</svg>
		
		{#if showText && text}
			<p class={cn(
				"font-medium",
				textSizeClasses[size],
				variantClasses[variant]
			)}>
				{text}
			</p>
		{/if}
	</div>
</div>