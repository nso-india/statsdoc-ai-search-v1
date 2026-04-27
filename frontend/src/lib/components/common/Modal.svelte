<script lang="ts">
	import { onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';
	import { flyAndScale } from '$lib/utils/transitions';

	export let show = true;
	export let size = 'md';
	export let containerClassName = 'p-3';
	export let className = 'bg-white dark:bg-gray-900 rounded-2xl';

	const sizeToWidth = (size: string) => {
		if (size === 'full') {
			return 'w-full';
		}
		if (size === 'xs') {
			return 'w-[16rem]';
		} else if (size === 'sm') {
			return 'w-[30rem]';
		} else if (size === 'md') {
			return 'w-[42rem]';
		} else if (size === 'lg') {
			return 'w-[56rem]';
		} else if (size === 'xl') {
			return 'w-[70rem]';
		} else if (size === '2xl') {
			return 'w-[84rem]';
		} else if (size === '3xl') {
			return 'w-[100rem]';
		} else {
			return 'w-[56rem]';
		}
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			console.log('Escape pressed');
			show = false;
		}
	};

	$: if (show) {
		window.addEventListener('keydown', handleKeyDown);
		document.body.style.overflow = 'hidden';
	} else {
		window.removeEventListener('keydown', handleKeyDown);
		document.body.style.overflow = 'unset';
	}

	onDestroy(() => {
		window.removeEventListener('keydown', handleKeyDown);
		document.body.style.overflow = 'unset';
	});
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		aria-modal="true"
		role="dialog"
		class="modal fixed top-0 right-0 left-0 bottom-0 bg-black/60 w-full h-screen max-h-[100dvh] {containerClassName} flex justify-center z-50 overflow-y-auto overscroll-contain"
		in:fade={{ duration: 150 }}
		on:mousedown={() => {
			show = false;
		}}
	>
		<div
			class="m-auto max-w-full {sizeToWidth(size)} {size !== 'full'
				? 'mx-2'
				: ''} shadow-3xl min-h-fit scrollbar-hidden {className}"
			in:flyAndScale
			on:mousedown={(e) => {
				e.stopPropagation();
			}}
		>
			<slot />
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
