<script lang="ts">
	import { Select as SelectPrimitive, type WithoutChild } from "bits-ui";
	import { cn } from "$lib/utils";

	let {
		ref = $bindable(null),
		class: className,
		placeholder,
		...restProps
	}: WithoutChild<SelectPrimitive.ValueProps> = $props();
</script>

<SelectPrimitive.Value
	bind:ref
	class={cn("text-sm", className)}
	{placeholder}
	{...restProps}
/>
