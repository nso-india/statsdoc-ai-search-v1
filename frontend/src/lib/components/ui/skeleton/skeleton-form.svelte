<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";
	import { Skeleton } from "./index.js";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		fields?: number;
		showTitle?: boolean;
		showButtons?: boolean;
		buttonCount?: number;
		fieldVariant?: 'input' | 'textarea' | 'select' | 'mixed';
	};

	export let fields: number = 4;
	export let showTitle: boolean = true;
	export let showButtons: boolean = true;
	export let buttonCount: number = 2;
	export let fieldVariant: 'input' | 'textarea' | 'select' | 'mixed' = 'mixed';

	let className: $$Props["class"] = undefined;
	export { className as class };

	function getFieldType(index: number): string {
		if (fieldVariant === 'mixed') {
			const types = ['input', 'input', 'select', 'textarea'];
			return types[index % types.length];
		}
		return fieldVariant;
	}
</script>

<div class={cn("space-y-6", className)} {...$$restProps}>
	{#if showTitle}
		<div class="space-y-2">
			<Skeleton class="h-7 w-48" />
			<Skeleton class="h-4 w-64" />
		</div>
	{/if}

	<div class="space-y-4">
		{#each Array(fields) as _, i}
			{@const fieldType = getFieldType(i)}
			<div class="space-y-2">
				<!-- Field Label -->
				<Skeleton class="h-4 w-20" />
				
				<!-- Field Input -->
				{#if fieldType === 'input'}
					<Skeleton class="h-10 w-full rounded-md" />
				{:else if fieldType === 'textarea'}
					<Skeleton class="h-20 w-full rounded-md" />
				{:else if fieldType === 'select'}
					<div class="relative">
						<Skeleton class="h-10 w-full rounded-md" />
						<div class="absolute right-3 top-1/2 -translate-y-1/2">
							<Skeleton class="h-4 w-4" />
						</div>
					</div>
				{/if}
				
				<!-- Helper text occasionally -->
				{#if i % 3 === 0}
					<Skeleton class="h-3 w-32" />
				{/if}
			</div>
		{/each}
	</div>

	{#if showButtons}
		<div class="flex items-center space-x-3 pt-4">
			{#each Array(buttonCount) as _, i}
				<Skeleton class="h-10 {i === 0 ? 'w-24' : 'w-20'} rounded-md" />
			{/each}
		</div>
	{/if}
</div>