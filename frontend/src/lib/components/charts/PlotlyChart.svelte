<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { PlotlyHTMLElement } from 'plotly.js-dist-min';

	export let figureData: string | null = null;
	export let className: string = '';
	export let debug: boolean = false;

	let chartContainer: HTMLDivElement;
	let plotlyLoaded = false;
	let Plotly: any = null;

	async function loadPlotly() {
		if (!plotlyLoaded) {
			try {
				// Dynamic import of Plotly to reduce bundle size
				Plotly = await import('plotly.js-dist-min');
				plotlyLoaded = true;
			} catch (error) {
				console.error('Failed to load Plotly:', error);
			}
		}
	}

	async function renderChart() {
		if (!figureData || !chartContainer || !plotlyLoaded || !Plotly) return;

		try {
			if (debug) {
				console.log('Rendering chart with data type:', typeof figureData);
				console.log('Figure data preview:', figureData?.substring(0, 200) + '...');
			}
			
			// Check if figureData is already an object or needs parsing
			let parsedData;
			if (typeof figureData === 'string') {
				// If it's a string, try to parse as JSON
				if (figureData.startsWith('<') || figureData.includes('<html>')) {
					// This is HTML, not JSON - show error
					throw new Error('Received HTML instead of JSON chart data. Backend may not be updated.');
				}
				parsedData = JSON.parse(figureData);
			} else {
				// Already an object
				parsedData = figureData;
			}
			
			// Extract data, layout, and config from the figure
			const { data, layout, config } = parsedData;

			// Detect theme for proper text colors
			const isDark = document.documentElement.classList.contains('dark') || 
						   window.matchMedia('(prefers-color-scheme: dark)').matches;

			// Configure responsive layout with theme-aware colors
			const responsiveLayout = {
				...layout,
				autosize: true,
				responsive: true,
				margin: { t: 50, r: 50, b: 50, l: 50 },
				paper_bgcolor: isDark ? '#1f2937' : '#ffffff',
				plot_bgcolor: isDark ? '#1f2937' : '#ffffff',
				font: {
					color: isDark ? '#f3f4f6' : '#374151',
					family: 'system-ui, sans-serif'
				},
				xaxis: {
					...layout.xaxis,
					gridcolor: isDark ? '#374151' : '#e5e7eb',
					tickcolor: isDark ? '#6b7280' : '#9ca3af',
					linecolor: isDark ? '#6b7280' : '#9ca3af'
				},
				yaxis: {
					...layout.yaxis,
					gridcolor: isDark ? '#374151' : '#e5e7eb',
					tickcolor: isDark ? '#6b7280' : '#9ca3af',
					linecolor: isDark ? '#6b7280' : '#9ca3af'
				}
			};

			// Configure responsive config
			const responsiveConfig = {
				...config,
				responsive: true,
				displayModeBar: true,
				displaylogo: false,
				modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
			};

			// Clear any existing plot
			Plotly.purge(chartContainer);

			// Create new plot
			await Plotly.newPlot(chartContainer, data, responsiveLayout, responsiveConfig);

			// Make it responsive to window resize
			window.addEventListener('resize', handleResize);
		} catch (error) {
			console.error('Error rendering Plotly chart:', error);
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			chartContainer.innerHTML = `<div class="p-4 text-red-600">Error rendering chart: ${errorMessage}</div>`;
		}
	}

	function handleResize() {
		if (chartContainer && Plotly) {
			Plotly.Plots.resize(chartContainer);
		}
	}

	onMount(async () => {
		await loadPlotly();
		if (figureData) {
			renderChart();
		}
	});

	onDestroy(() => {
		if (chartContainer && Plotly) {
			Plotly.purge(chartContainer);
		}
		window.removeEventListener('resize', handleResize);
	});

	// Reactive statement to re-render when figureData changes
	$: if (figureData && plotlyLoaded && chartContainer) {
		renderChart();
	}
</script>

<div 
	bind:this={chartContainer} 
	class="plotly-chart-container {className}"
	style="width: 100%; height: 400px; min-height: 300px;"
>
	{#if !plotlyLoaded}
		<div class="flex items-center justify-center h-full">
			<div class="text-center">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
				<p class="text-gray-600 text-sm">Loading chart...</p>
			</div>
		</div>
	{:else if !figureData}
		<div class="flex items-center justify-center h-full">
			<p class="text-gray-500 text-sm">No chart data available</p>
		</div>
	{/if}
</div>

<style>
	:global(.plotly-chart-container .plotly) {
		width: 100% !important;
		height: 100% !important;
	}

	:global(.plotly-chart-container .main-svg) {
		background-color: transparent !important;
	}

	/* Dark mode support */
	:global(.dark .plotly-chart-container) {
		color-scheme: dark;
	}
</style>
