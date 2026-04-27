<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
	import { cn } from "$lib/utils";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		class: className,
		inset = false,
		...restProps
	}: ComponentProps<DropdownMenuPrimitive.Label> & {
		inset?: boolean;
	} = $props();
</script>

<DropdownMenuPrimitive.Label
	bind:ref
	class={cn("px-2 py-1.5 text-sm font-semibold", inset && "pl-8", className)}
	{...restProps}
>
	{@render children?.()}
</DropdownMenuPrimitive.Label>
