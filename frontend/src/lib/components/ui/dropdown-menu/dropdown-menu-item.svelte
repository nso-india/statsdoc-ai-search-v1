<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
	import { cn } from "$lib/utils";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		class: className,
		inset = false,
		children,
		...restProps
	}: ComponentProps<DropdownMenuPrimitive.Item> & {
		inset?: boolean;
		children?: any;
	} = $props();
</script>

<DropdownMenuPrimitive.Item
	bind:ref
	class={cn(
		"data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
		inset && "pl-8",
		className
	)}
	{...restProps}
>
	{@render children?.()}
</DropdownMenuPrimitive.Item>
