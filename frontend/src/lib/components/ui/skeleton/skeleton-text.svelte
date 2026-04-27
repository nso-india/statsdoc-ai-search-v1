<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		lines?: number;
		variant?: 'paragraph' | 'heading' | 'list' | 'mixed';
		widths?: string[];
	};

	export let lines: number = 3;
	export let variant: 'paragraph' | 'heading' | 'list' | 'mixed' = 'paragraph';
	export let widths: string[] = [];

	let className: $$Props["class"] = undefined;
	export { className as class };

	function getLineWidth(index: number): string {
		if (widths.length > 0) {
			return widths[index % widths.length];
		}
		
		switch (variant) {
			case 'heading':
				return index === 0 ? 'w-3/4' : 'w-1/2';
			case 'paragraph':
				const paragraphWidths = ['w-full', 'w-11/12', 'w-4/5', 'w-5/6', 'w-3/4'];
				return paragraphWidths[index % paragraphWidths.length];
			case 'list':
				return 'w-2/3';
			case 'mixed':
				if (index === 0) return 'w-3/4'; // Title
				if (index % 4 === 1) return 'w-full'; // Full line
				if (index % 4 === 2) return 'w-5/6'; // Slightly shorter
				return 'w-4/5'; // Default
			default:
				return 'w-full';
		}
	}

	function getLineHeight(index: number): string {
		switch (variant) {
			case 'heading':
				return index === 0 ? 'h-6' : 'h-5';
			case 'paragraph':
				return 'h-4';
			case 'list':
				return 'h-4';
			case 'mixed':
				return index === 0 ? 'h-6' : 'h-4';
			default:
				return 'h-4';
		}
	}

	// Base skeleton element class
	const baseSkeletonClass = "animate-pulse rounded-md bg-muted";
</script>

<div class={cn("space-y-2", className)} {...$$restProps}>
	{#each Array(lines) as _, i}
		{#if variant === 'list'}
			<div class="flex items-center space-x-2">
				<div class={cn(baseSkeletonClass, "h-2 w-2 rounded-full")}></div>
				<div class={cn(baseSkeletonClass, getLineHeight(i), getLineWidth(i))}></div>
			</div>
		{:else}
			<div class={cn(baseSkeletonClass, getLineHeight(i), getLineWidth(i))}></div>
		{/if}
	{/each}
</div>