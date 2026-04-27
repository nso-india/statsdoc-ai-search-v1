<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils";
	import { Skeleton } from "./index.js";

	type $$Props = HTMLAttributes<HTMLDivElement> & {
		pages?: number;
		showThumbnails?: boolean;
		showHeader?: boolean;
		variant?: 'viewer' | 'thumbnails' | 'full';
	};

	export let pages: number = 3;
	export let showThumbnails: boolean = false;
	export let showHeader: boolean = true;
	export let variant: 'viewer' | 'thumbnails' | 'full' = 'full';

	let className: $$Props["class"] = undefined;
	export { className as class };
</script>

<div class={cn("flex h-full", className)} {...$$restProps}>
	{#if variant === 'full' || variant === 'thumbnails'}
		<!-- Sidebar with thumbnails -->
		<div class="w-80 border-r bg-muted/10 flex flex-col">
			<!-- Sidebar Header -->
			<div class="p-4 border-b">
				<Skeleton class="h-5 w-32 mb-3" />
				<!-- Filter options -->
				<div class="space-y-2">
					<Skeleton class="h-8 w-full rounded-md" />
					<div class="flex space-x-2">
						<Skeleton class="h-6 w-16 rounded-full" />
						<Skeleton class="h-6 w-20 rounded-full" />
					</div>
				</div>
			</div>
			
			<!-- Thumbnails -->
			<div class="flex-1 overflow-hidden p-4">
				<div class="space-y-3">
					{#each Array(pages) as _, i}
						<div class="relative group">
							<div class="bg-white rounded-lg border shadow-sm overflow-hidden">
								<Skeleton class="aspect-[3/4] w-full" />
								<!-- Page number badge -->
								<div class="absolute top-2 right-2">
									<Skeleton class="h-6 w-8 rounded-md" />
								</div>
								<!-- Content badges -->
								<div class="absolute bottom-2 left-2 flex space-x-1">
									<Skeleton class="h-4 w-12 rounded-full" />
									<Skeleton class="h-4 w-14 rounded-full" />
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}

	{#if variant === 'full' || variant === 'viewer'}
		<!-- Main viewer -->
		<div class="flex-1 flex flex-col">
			{#if showHeader}
				<!-- Document Header -->
				<div class="border-b bg-background p-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center space-x-4">
							<Skeleton class="h-8 w-8 rounded" />
							<div class="space-y-1">
								<Skeleton class="h-6 w-48" />
								<Skeleton class="h-4 w-32" />
							</div>
						</div>
						<div class="flex items-center space-x-2">
							<Skeleton class="h-6 w-16 rounded-full" />
							<Skeleton class="h-8 w-20 rounded-md" />
						</div>
					</div>
				</div>
			{/if}

			<!-- Document Content -->
			<div class="flex-1 overflow-auto p-6">
				<div class="max-w-4xl mx-auto space-y-8">
					{#each Array(pages) as _, pageIndex}
						<div class="bg-white rounded-lg border shadow-sm overflow-hidden">
							<!-- Page Header -->
							<div class="flex items-center justify-between p-4 border-b bg-muted/5">
								<div class="flex items-center space-x-2">
									<Skeleton class="h-5 w-5 rounded-full" />
									<Skeleton class="h-4 w-16" />
								</div>
								<div class="flex space-x-2">
									<Skeleton class="h-5 w-12 rounded-full" />
									<Skeleton class="h-5 w-16 rounded-full" />
								</div>
							</div>
							
							<!-- Page Content -->
							<div class="p-6">
								<div class="space-y-4">
									<!-- Title -->
									<Skeleton class="h-6 w-3/4" />
									
									<!-- Paragraphs -->
									<div class="space-y-2">
										<Skeleton class="h-4 w-full" />
										<Skeleton class="h-4 w-11/12" />
										<Skeleton class="h-4 w-4/5" />
									</div>
									
									<!-- Table or Image occasionally -->
									{#if pageIndex === 1}
										<div class="my-6 p-4 border rounded-lg bg-muted/5">
											<Skeleton class="h-32 w-full" />
											<div class="mt-2 space-y-1">
												<Skeleton class="h-3 w-1/3" />
												<Skeleton class="h-3 w-1/4" />
											</div>
										</div>
									{/if}
									
									<!-- More content -->
									<div class="space-y-2">
										<Skeleton class="h-4 w-full" />
										<Skeleton class="h-4 w-5/6" />
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>