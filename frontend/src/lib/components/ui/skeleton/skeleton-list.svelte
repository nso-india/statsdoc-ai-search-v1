<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";
	import { Skeleton } from "./index.js";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		items?: number;
		showAvatar?: boolean;
		showActions?: boolean;
		variant?: 'simple' | 'detailed' | 'media';
	};

	export let items: number = 5;
	export let showAvatar: boolean = true;
	export let showActions: boolean = false;
	export let variant: 'simple' | 'detailed' | 'media' = 'detailed';

	let className: $$Props["class"] = undefined;
	export { className as class };
</script>

<div class={cn("space-y-3", className)} {...$$restProps}>
	{#each Array(items) as _, i}
		<div class="flex items-center space-x-4 p-3 rounded-lg border bg-card">
			{#if showAvatar}
				<Skeleton class="h-12 w-12 rounded-full flex-shrink-0" />
			{/if}
			
			<div class="flex-1 space-y-2">
				{#if variant === 'simple'}
					<Skeleton class="h-4 w-3/4" />
				{:else if variant === 'detailed'}
					<Skeleton class="h-5 w-2/3" />
					<Skeleton class="h-3 w-1/2" />
					<div class="flex space-x-2">
						<Skeleton class="h-4 w-16 rounded-full" />
						<Skeleton class="h-4 w-20 rounded-full" />
					</div>
				{:else if variant === 'media'}
					<div class="flex space-x-3">
						<div class="flex-1 space-y-2">
							<Skeleton class="h-5 w-3/4" />
							<Skeleton class="h-4 w-full" />
							<Skeleton class="h-4 w-2/3" />
						</div>
						<Skeleton class="h-16 w-24 rounded-md flex-shrink-0" />
					</div>
				{/if}
			</div>
			
			{#if showActions}
				<div class="flex space-x-2 flex-shrink-0">
					<Skeleton class="h-8 w-8 rounded" />
					<Skeleton class="h-8 w-8 rounded" />
				</div>
			{/if}
		</div>
	{/each}
</div>