<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { BarChart, Download, Maximize } from '@lucide/svelte/icons';

	const dispatch = createEventDispatcher();

	export let config: any;
	export let options: ChartOptions = {};

	interface ChartOptions {
		theme?: 'light' | 'dark' | 'auto';
		responsive?: boolean;
		enableDownload?: boolean;
	}

	let chartContainer: HTMLDivElement;
	let loading = true;
	let error = false;

	// Default options
	const defaultOptions: ChartOptions = {
		theme: 'auto',
		responsive: true,
		enableDownload: false,
		...options
	};

	onMount(async () => {
		await renderChart();
	});

	async function renderChart() {
		try {
			loading = true;
			error = false;
			
			if (!config || typeof config !== 'object') {
				throw new Error('Invalid chart configuration');
			}

			// Create placeholder chart based on type
			createPlaceholderChart();
			
		} catch (err) {
			error = true;
			dispatch('error', err instanceof Error ? err : new Error('Failed to render chart'));
		} finally {
			loading = false;
		}
	}

	function createPlaceholderChart() {
		if (!chartContainer) return;

		const chartType = config.type || 'bar';
		const title = config.title || 'Chart Visualization';
		const data = config.data || [];

		// Create a simple SVG visualization
		const svg = `
			<svg width="100%" height="250" viewBox="0 0 400 250" style="background: #f8fafc; border-radius: 8px;">
				<defs>
					<linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
						<stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.8" />
						<stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:0.6" />
					</linearGradient>
				</defs>
				
				<!-- Chart Title -->
				<text x="200" y="25" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#374151">
					${title}
				</text>
				
				<!-- Chart visualization based on type -->
				${generateChartSVG(chartType, data)}
				
				<!-- Chart type label -->
				<text x="200" y="240" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#6b7280">
					${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart • ${data.length} data points
				</text>
			</svg>
		`;

		chartContainer.innerHTML = svg;
	}

	function generateChartSVG(type: string, data: any[]): string {
		if (!data || data.length === 0) {
			return `
				<rect x="50" y="50" width="300" height="150" fill="#e5e7eb" rx="8"/>
				<text x="200" y="135" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#6b7280">
					No data available
				</text>
			`;
		}

		switch (type) {
			case 'bar':
				return generateBarChart(data);
			case 'line':
				return generateLineChart(data);
			case 'pie':
				return generatePieChart(data);
			case 'doughnut':
				return generateDoughnutChart(data);
			default:
				return generateBarChart(data);
		}
	}

	function generateBarChart(data: any[]): string {
		const maxValue = Math.max(...data.map(d => d.value || 0));
		const barWidth = 300 / data.length - 10;
		const startX = 50 + 5;

		return data.map((item, index) => {
			const height = ((item.value || 0) / maxValue) * 140;
			const x = startX + index * (barWidth + 10);
			const y = 190 - height;
			
			return `
				<rect x="${x}" y="${y}" width="${barWidth}" height="${height}" fill="url(#chartGradient)" rx="2"/>
				<text x="${x + barWidth/2}" y="210" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#374151">
					${item.label || `Item ${index + 1}`}
				</text>
				<text x="${x + barWidth/2}" y="${y - 5}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#374151">
					${item.value || 0}
				</text>
			`;
		}).join('');
	}

	function generateLineChart(data: any[]): string {
		if (data.length < 2) return generateBarChart(data);

		const maxValue = Math.max(...data.map(d => d.value || 0));
		const stepX = 300 / (data.length - 1);
		
		const points = data.map((item, index) => {
			const x = 50 + index * stepX;
			const y = 190 - ((item.value || 0) / maxValue) * 140;
			return `${x},${y}`;
		}).join(' ');

		const circles = data.map((item, index) => {
			const x = 50 + index * stepX;
			const y = 190 - ((item.value || 0) / maxValue) * 140;
			return `<circle cx="${x}" cy="${y}" r="4" fill="#1d4ed8"/>`;
		}).join('');

		return `
			<polyline points="${points}" fill="none" stroke="#3b82f6" stroke-width="2"/>
			${circles}
		`;
	}

	function generatePieChart(data: any[]): string {
		const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
		if (total === 0) return generateBarChart(data);

		const centerX = 200;
		const centerY = 125;
		const radius = 60;
		let currentAngle = 0;

		const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

		return data.map((item, index) => {
			const percentage = (item.value || 0) / total;
			const angle = percentage * 2 * Math.PI;
			
			const x1 = centerX + radius * Math.cos(currentAngle);
			const y1 = centerY + radius * Math.sin(currentAngle);
			const x2 = centerX + radius * Math.cos(currentAngle + angle);
			const y2 = centerY + radius * Math.sin(currentAngle + angle);
			
			const largeArcFlag = angle > Math.PI ? 1 : 0;
			
			const pathData = [
				`M ${centerX} ${centerY}`,
				`L ${x1} ${y1}`,
				`A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
				'Z'
			].join(' ');
			
			currentAngle += angle;
			
			return `<path d="${pathData}" fill="${colors[index % colors.length]}" stroke="#ffffff" stroke-width="2"/>`;
		}).join('');
	}

	function generateDoughnutChart(data: any[]): string {
		// Similar to pie chart but with inner circle
		const pieChart = generatePieChart(data);
		return `
			${pieChart}
			<circle cx="200" cy="125" r="30" fill="#f8fafc"/>
		`;
	}

	function downloadChart() {
		if (!chartContainer) return;

		try {
			const svg = chartContainer.querySelector('svg');
			if (!svg) return;

			const svgData = new XMLSerializer().serializeToString(svg);
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');
			const img = new Image();

			img.onload = () => {
				canvas.width = img.width;
				canvas.height = img.height;
				ctx?.drawImage(img, 0, 0);
				
				const link = document.createElement('a');
				link.download = `chart-${config.type || 'visualization'}.png`;
				link.href = canvas.toDataURL();
				link.click();
			};

			img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
		} catch (error) {
			dispatch('error', new Error('Failed to download chart'));
		}
	}

	function expandChart() {
		// Emit event for parent to handle full-screen view
		dispatch('expand', { config, chartContainer });
	}

	// Re-render when config changes
	$: if (config) {
		renderChart();
	}
</script>

<div class="chart-renderer" data-theme={defaultOptions.theme}>
	<!-- Header -->
	<div class="chart-header">
		<div class="chart-info">
			<BarChart class="w-4 h-4" />
			<span class="chart-label">Chart Visualization</span>
			{#if config?.type}
				<span class="chart-type">{config.type}</span>
			{/if}
		</div>
		
		<div class="chart-actions">
			<button 
				class="action-btn expand-btn"
				on:click={expandChart}
				title="Expand chart"
			>
				<Maximize class="w-4 h-4" />
			</button>
			
			{#if defaultOptions.enableDownload}
				<button 
					class="action-btn download-btn"
					on:click={downloadChart}
					title="Download chart"
				>
					<Download class="w-4 h-4" />
				</button>
			{/if}
		</div>
	</div>

	<!-- Content -->
	<div class="chart-content">
		{#if loading}
			<div class="chart-loading">
				<div class="loading-spinner"></div>
				<span>Rendering chart...</span>
			</div>
		{:else if error}
			<div class="chart-error">
				<BarChart class="w-8 h-8 text-red-500" />
				<div class="error-details">
					<h4>Chart rendering failed</h4>
					<p>Unable to render the chart with the provided configuration.</p>
				</div>
			</div>
		{:else}
			<div bind:this={chartContainer} class="chart-container"></div>
		{/if}
	</div>

	<!-- Footer with chart info -->
	{#if config && !loading && !error}
		<div class="chart-footer">
			<div class="chart-metadata">
				{#if config.data}
					<span>Data points: {config.data.length}</span>
				{/if}
				{#if config.type}
					<span>Type: {config.type}</span>
				{/if}
				{#if defaultOptions.responsive}
					<span>Responsive</span>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.chart-renderer {
		border-radius: 0.5rem;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		font-size: 0.875rem;
	}

	.chart-renderer[data-theme="dark"] {
		border-color: #374151;
		background: #1f2937;
	}

	.chart-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #ecfdf5;
		border-bottom: 1px solid #10b981;
	}

	.chart-renderer[data-theme="dark"] .chart-header {
		background: #064e3b;
		border-bottom-color: #10b981;
	}

	.chart-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #047857;
	}

	.chart-renderer[data-theme="dark"] .chart-info {
		color: #6ee7b7;
	}

	.chart-label {
		font-size: 0.875rem;
	}

	.chart-type {
		font-size: 0.75rem;
		color: #10b981;
		background: #d1fae5;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		text-transform: capitalize;
	}

	.chart-renderer[data-theme="dark"] .chart-type {
		color: #a7f3d0;
		background: #065f46;
	}

	.chart-actions {
		display: flex;
		gap: 0.5rem;
	}

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.375rem 0.5rem;
		border: none;
		border-radius: 0.25rem;
		background: transparent;
		color: #047857;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
	}

	.action-btn:hover {
		background: #d1fae5;
		color: #065f46;
	}

	.chart-renderer[data-theme="dark"] .action-btn {
		color: #6ee7b7;
	}

	.chart-renderer[data-theme="dark"] .action-btn:hover {
		background: #065f46;
		color: #ecfdf5;
	}

	.chart-content {
		position: relative;
		min-height: 250px;
		padding: 1rem;
	}

	.chart-loading {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		height: 250px;
		color: #6b7280;
	}

	.loading-spinner {
		width: 1.5rem;
		height: 1.5rem;
		border: 2px solid #e5e7eb;
		border-top: 2px solid #10b981;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.chart-error {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		height: 250px;
		justify-content: center;
		align-items: center;
		background: #fee2e2;
		color: #7f1d1d;
		border-radius: 0.5rem;
	}

	.error-details h4 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #dc2626;
	}

	.error-details p {
		margin: 0;
		font-size: 0.875rem;
		line-height: 1.5;
	}

	.chart-container {
		width: 100%;
		height: 100%;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.chart-footer {
		padding: 0.5rem 1rem;
		background: #f8fafc;
		border-top: 1px solid #e5e7eb;
	}

	.chart-renderer[data-theme="dark"] .chart-footer {
		background: #374151;
		border-top-color: #4b5563;
	}

	.chart-metadata {
		display: flex;
		gap: 1rem;
		font-size: 0.75rem;
		color: #6b7280;
	}

	.chart-renderer[data-theme="dark"] .chart-metadata {
		color: #9ca3af;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.chart-header {
			padding: 0.5rem 0.75rem;
		}

		.chart-content {
			padding: 0.75rem;
		}

		.chart-type {
			display: none;
		}

		.chart-metadata {
			flex-direction: column;
			gap: 0.25rem;
		}
	}
</style>
