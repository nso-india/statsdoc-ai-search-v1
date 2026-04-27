<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		size?: 'sm' | 'md' | 'lg' | 'xl';
		shape?: 'circle' | 'square' | 'rounded';
	};

	export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
	export let shape: 'circle' | 'square' | 'rounded' = 'circle';

	let className: $$Props["class"] = undefined;
	export { className as class };

	const sizeClasses = {
		sm: 'h-8 w-8',
		md: 'h-10 w-10',
		lg: 'h-12 w-12',
		xl: 'h-16 w-16'
	};

	const shapeClasses = {
		circle: 'rounded-full',
		square: 'rounded-none',
		rounded: 'rounded-lg'
	};
</script>

<div 
	class={cn(
		"bg-muted animate-pulse", 
		sizeClasses[size], 
		shapeClasses[shape], 
		className
	)} 
	{...$$restProps}
></div>