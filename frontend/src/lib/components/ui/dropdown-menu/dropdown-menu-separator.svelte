<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
	import { cn } from "$lib/utils";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		class: className,
		...restProps
	}: ComponentProps<DropdownMenuPrimitive.Separator> = $props();
</script>

<DropdownMenuPrimitive.Separator
	bind:ref
	class={cn("bg-muted -mx-1 my-1 h-px", className)}
	{...restProps}
/>
