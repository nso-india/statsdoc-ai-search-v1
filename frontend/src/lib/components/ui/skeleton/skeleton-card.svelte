<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";
	import { Skeleton } from "./index.js";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		showHeader?: boolean;
		showFooter?: boolean;
		headerLines?: number;
		contentLines?: number;
		footerLines?: number;
	};

	export let showHeader: boolean = true;
	export let showFooter: boolean = false;
	export let headerLines: number = 1;
	export let contentLines: number = 3;
	export let footerLines: number = 1;

	let className: $$Props["class"] = undefined;
	export { className as class };
</script>

<div class={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...$$restProps}>
	{#if showHeader}
		<div class="flex flex-col space-y-1.5 p-6 pb-3">
			{#each Array(headerLines) as _, i}
				<Skeleton class="h-5 {i === 0 ? 'w-1/3' : 'w-1/4'}" />
			{/each}
		</div>
	{/if}
	
	<div class="p-6 {showHeader ? 'pt-0' : ''} {showFooter ? 'pb-3' : ''}">
		<div class="space-y-3">
			{#each Array(contentLines) as _, i}
				<Skeleton class="h-4 {i % 3 === 0 ? 'w-full' : i % 3 === 1 ? 'w-11/12' : 'w-4/5'}" />
			{/each}
		</div>
	</div>

	{#if showFooter}
		<div class="flex items-center p-6 pt-0">
			<div class="flex space-x-2 w-full">
				{#each Array(footerLines) as _}
					<Skeleton class="h-4 w-20" />
				{/each}
			</div>
		</div>
	{/if}
</div>