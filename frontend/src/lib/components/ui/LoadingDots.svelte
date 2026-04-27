<script lang="ts"></script>
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let color: string = 'text-gray-500';

	const sizeClasses = {
		sm: 'w-1 h-1',
		md: 'w-2 h-2',
		lg: 'w-3 h-3'
	};

	const dotSize = sizeClasses[size];
</script>

<div class="flex items-center space-x-1">
	<div class="{dotSize} {color} rounded-full animate-bounce" style="animation-delay: 0s;"></div>
	<div class="{dotSize} {color} rounded-full animate-bounce" style="animation-delay: 0.1s;"></div>
	<div class="{dotSize} {color} rounded-full animate-bounce" style="animation-delay: 0.2s;"></div>
</div>

<style>
	.animate-bounce {
		animation: bounce 1.4s infinite;
	}

	@keyframes bounce {
		0%, 80%, 100% {
			transform: scale(0);
			opacity: 0.5;
		}
		40% {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
