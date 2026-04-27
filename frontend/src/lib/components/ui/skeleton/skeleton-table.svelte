<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";
	import { Skeleton } from "./index.js";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		rows?: number;
		columns?: number;
		showHeader?: boolean;
		showActions?: boolean;
		showCheckbox?: boolean;
	};

	export let rows: number = 5;
	export let columns: number = 4;
	export let showHeader: boolean = true;
	export let showActions: boolean = true;
	export let showCheckbox: boolean = false;

	let className: $$Props["class"] = undefined;
	export { className as class };

	$: totalColumns = columns + (showCheckbox ? 1 : 0) + (showActions ? 1 : 0);
</script>

<div class={cn("w-full overflow-auto", className)} {...$$restProps}>
	<table class="w-full caption-bottom text-sm">
		{#if showHeader}
			<thead class="[&_tr]:border-b">
				<tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
					{#if showCheckbox}
						<th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-12">
							<Skeleton class="h-4 w-4" />
						</th>
					{/if}
					{#each Array(columns) as _, i}
						<th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
							<Skeleton class="h-4 {i === 0 ? 'w-32' : i === 1 ? 'w-24' : 'w-20'}" />
						</th>
					{/each}
					{#if showActions}
						<th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground w-24">
							<Skeleton class="h-4 w-16 mx-auto" />
						</th>
					{/if}
				</tr>
			</thead>
		{/if}
		<tbody class="[&_tr:last-child]:border-0">
			{#each Array(rows) as _, rowIndex}
				<tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
					{#if showCheckbox}
						<td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
							<Skeleton class="h-4 w-4" />
						</td>
					{/if}
					{#each Array(columns) as _, colIndex}
						<td class="p-4 align-middle">
							{#if colIndex === 0}
								<!-- First column often has icon + text -->
								<div class="flex items-center space-x-3">
									<Skeleton class="h-10 w-10 rounded-lg" />
									<div class="space-y-1">
										<Skeleton class="h-4 w-32" />
										<Skeleton class="h-3 w-20" />
									</div>
								</div>
							{:else if colIndex === columns - 1}
								<!-- Last column often has badges -->
								<Skeleton class="h-6 w-16 rounded-full" />
							{:else}
								<!-- Regular text columns -->
								<Skeleton class="h-4 w-24" />
							{/if}
						</td>
					{/each}
					{#if showActions}
						<td class="p-4 align-middle text-center">
							<div class="flex items-center justify-center space-x-1">
								<Skeleton class="h-8 w-8 rounded" />
								<Skeleton class="h-8 w-8 rounded" />
								<Skeleton class="h-8 w-8 rounded" />
							</div>
						</td>
					{/if}
				</tr>
			{/each}
		</tbody>
	</table>
</div>