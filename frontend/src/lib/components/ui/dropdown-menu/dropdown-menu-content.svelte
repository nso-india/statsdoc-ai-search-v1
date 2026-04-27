<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
	import { cn, flyAndScale } from "$lib/utils";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		class: className,
		sideOffset = 4,
		transition = flyAndScale,
		transitionConfig,
		children,
		...restProps
	}: ComponentProps<DropdownMenuPrimitive.Content> & {
		children?: any;
	} = $props();
</script>

<DropdownMenuPrimitive.Content
	bind:ref
	{transition}
	{transitionConfig}
	{sideOffset}
	class={cn(
		"bg-popover text-popover-foreground z-50 min-w-[8rem] rounded-md border p-1 shadow-md focus:outline-none",
		className
	)}
	{...restProps}
>
	{@render children?.()}
</DropdownMenuPrimitive.Content>
