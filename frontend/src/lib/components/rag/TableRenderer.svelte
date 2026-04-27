<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Table, Download, Search } from '@lucide/svelte/icons';

	const dispatch = createEventDispatcher();

	export let content: string;
	export let options: TableOptions = {};

	interface TableOptions {
		theme?: 'light' | 'dark' | 'auto';
		searchable?: boolean;
		downloadable?: boolean;
		sortable?: boolean;
	}

	let searchTerm = '';
	let parsedTable: { headers: string[], rows: string[][] } | null = null;

	// Default options
	const defaultOptions: TableOptions = {
		theme: 'auto',
		searchable: false,
		downloadable: false,
		sortable: false,
		...options
	};

	// Parse markdown table or HTML table
	$: parsedTable = parseTable(content);
	$: filteredRows = filterRows(parsedTable?.rows || [], searchTerm);

	function parseTable(tableContent: string): { headers: string[], rows: string[][] } | null {
		try {
			// Try parsing as markdown table first
			const lines = tableContent.trim().split('\n');
			if (lines.length >= 2 && lines[1].includes('|') && lines[1].includes('-')) {
				return parseMarkdownTable(lines);
			}
			
			// Try parsing as HTML table
			if (tableContent.includes('<table') || tableContent.includes('<tr')) {
				return parseHtmlTable(tableContent);
			}

			return null;
		} catch (error) {
			dispatch('error', error instanceof Error ? error : new Error('Failed to parse table'));
			return null;
		}
	}

	function parseMarkdownTable(lines: string[]): { headers: string[], rows: string[][] } {
		const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
		const rows: string[][] = [];

		for (let i = 2; i < lines.length; i++) {
			const cells = lines[i].split('|').map(c => c.trim()).filter(c => c);
			if (cells.length > 0) {
				rows.push(cells);
			}
		}

		return { headers, rows };
	}

	function parseHtmlTable(html: string): { headers: string[], rows: string[][] } {
		const parser = new DOMParser();
		const doc = parser.parseFromString(html, 'text/html');
		const table = doc.querySelector('table');
		
		if (!table) throw new Error('No table found');

		const headers: string[] = [];
		const headerCells = table.querySelectorAll('th');
		headerCells.forEach(th => headers.push(th.textContent?.trim() || ''));

		const rows: string[][] = [];
		const tableRows = table.querySelectorAll('tbody tr, tr');
		tableRows.forEach(tr => {
			const cells: string[] = [];
			const tableCells = tr.querySelectorAll('td, th');
			if (tableCells.length > 0 && !tr.querySelector('th')) { // Skip header row
				tableCells.forEach(td => cells.push(td.textContent?.trim() || ''));
				if (cells.length > 0) rows.push(cells);
			}
		});

		return { headers, rows };
	}

	function filterRows(rows: string[][], search: string): string[][] {
		if (!search.trim()) return rows;
		
		const searchLower = search.toLowerCase();
		return rows.filter(row => 
			row.some(cell => cell.toLowerCase().includes(searchLower))
		);
	}

	function downloadTable() {
		if (!parsedTable) return;

		try {
			let csv = parsedTable.headers.join(',') + '\n';
			csv += filteredRows.map(row => 
				row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
			).join('\n');

			const blob = new Blob([csv], { type: 'text/csv' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = 'table-data.csv';
			a.click();
			URL.revokeObjectURL(url);
		} catch (error) {
			dispatch('error', new Error('Failed to download table'));
		}
	}
</script>

{#if parsedTable}
	<div class="table-renderer" data-theme={defaultOptions.theme}>
		<!-- Header -->
		<div class="table-header">
			<div class="table-info">
				<Table class="w-4 h-4" />
				<span class="table-label">Data Table</span>
				<span class="table-stats">
					{parsedTable.headers.length} columns • {filteredRows.length} rows
				</span>
			</div>
			
			<div class="table-actions">
				{#if defaultOptions.searchable}
					<div class="search-wrapper">
						<Search class="w-4 h-4 search-icon" />
						<input 
							type="text"
							placeholder="Search table..."
							class="search-input"
							bind:value={searchTerm}
						>
					</div>
				{/if}
				
				{#if defaultOptions.downloadable}
					<button 
						class="action-btn download-btn"
						on:click={downloadTable}
						title="Download as CSV"
					>
						<Download class="w-4 h-4" />
					</button>
				{/if}
			</div>
		</div>

		<!-- Table Content -->
		<div class="table-content">
			<table class="data-table">
				<thead>
					<tr>
						{#each parsedTable.headers as header}
							<th>{header}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each filteredRows as row, rowIndex}
						<tr>
							{#each row as cell, cellIndex}
								<td>{cell}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>

			{#if filteredRows.length === 0}
				<div class="empty-state">
					<Table class="w-8 h-8 text-gray-400" />
					<p>No matching rows found</p>
					{#if searchTerm}
						<button 
							class="clear-search"
							on:click={() => searchTerm = ''}
						>
							Clear search
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Footer -->
		<div class="table-footer">
			<div class="table-metadata">
				<span>Total: {parsedTable.rows.length} rows</span>
				{#if searchTerm}
					<span>Filtered: {filteredRows.length} results</span>
				{/if}
			</div>
		</div>
	</div>
{:else}
	<div class="table-error">
		<Table class="w-8 h-8 text-red-500" />
		<div class="error-details">
			<h4>Invalid table format</h4>
			<p>Unable to parse the table content. Please ensure it's in markdown or HTML table format.</p>
		</div>
	</div>
{/if}

<style>
	.table-renderer {
		border-radius: 0.5rem;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		font-size: 0.875rem;
	}

	.table-renderer[data-theme="dark"] {
		border-color: #374151;
		background: #1f2937;
	}

	.table-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #fef3c7;
		border-bottom: 1px solid #f59e0b;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.table-renderer[data-theme="dark"] .table-header {
		background: #78350f;
		border-bottom-color: #f59e0b;
	}

	.table-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #92400e;
	}

	.table-renderer[data-theme="dark"] .table-info {
		color: #fef3c7;
	}

	.table-label {
		font-size: 0.875rem;
	}

	.table-stats {
		font-size: 0.75rem;
		color: #d97706;
		background: #fef7cd;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
	}

	.table-renderer[data-theme="dark"] .table-stats {
		color: #fed7aa;
		background: #9a3412;
	}

	.table-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.search-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: 0.75rem;
		color: #6b7280;
		pointer-events: none;
	}

	.search-input {
		padding: 0.375rem 0.75rem 0.375rem 2.25rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		background: #ffffff;
		color: #374151;
		font-size: 0.875rem;
		width: 200px;
	}

	.table-renderer[data-theme="dark"] .search-input {
		border-color: #4b5563;
		background: #374151;
		color: #f3f4f6;
	}

	.search-input:focus {
		outline: none;
		border-color: #f59e0b;
		box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
	}

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.375rem 0.5rem;
		border: none;
		border-radius: 0.25rem;
		background: transparent;
		color: #92400e;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
	}

	.action-btn:hover {
		background: #fef7cd;
		color: #78350f;
	}

	.table-renderer[data-theme="dark"] .action-btn {
		color: #fed7aa;
	}

	.table-renderer[data-theme="dark"] .action-btn:hover {
		background: #9a3412;
		color: #fef3c7;
	}

	.table-content {
		overflow-x: auto;
		max-height: 500px;
		overflow-y: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.data-table th,
	.data-table td {
		padding: 0.75rem;
		text-align: left;
		border-bottom: 1px solid #e5e7eb;
		vertical-align: top;
	}

	.data-table th {
		background: #f9fafb;
		font-weight: 600;
		color: #374151;
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.table-renderer[data-theme="dark"] .data-table th {
		background: #374151;
		color: #f9fafb;
		border-bottom-color: #4b5563;
	}

	.table-renderer[data-theme="dark"] .data-table td {
		border-bottom-color: #4b5563;
		color: #d1d5db;
	}

	.data-table tr:nth-child(even) {
		background: #f9fafb;
	}

	.table-renderer[data-theme="dark"] .data-table tr:nth-child(even) {
		background: #374151;
	}

	.data-table tr:hover {
		background: #f3f4f6;
	}

	.table-renderer[data-theme="dark"] .data-table tr:hover {
		background: #4b5563;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		text-align: center;
		color: #6b7280;
	}

	.empty-state p {
		margin: 0.5rem 0 1rem 0;
		font-size: 0.875rem;
	}

	.clear-search {
		padding: 0.375rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		background: #ffffff;
		color: #374151;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.clear-search:hover {
		background: #f3f4f6;
		border-color: #9ca3af;
	}

	.table-footer {
		padding: 0.5rem 1rem;
		background: #f8fafc;
		border-top: 1px solid #e5e7eb;
	}

	.table-renderer[data-theme="dark"] .table-footer {
		background: #374151;
		border-top-color: #4b5563;
	}

	.table-metadata {
		display: flex;
		gap: 1rem;
		font-size: 0.75rem;
		color: #6b7280;
	}

	.table-renderer[data-theme="dark"] .table-metadata {
		color: #9ca3af;
	}

	.table-error {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		padding: 2rem;
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

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.table-header {
			flex-direction: column;
			align-items: stretch;
		}

		.table-actions {
			justify-content: space-between;
		}

		.search-input {
			width: 150px;
		}

		.data-table {
			font-size: 0.75rem;
		}

		.data-table th,
		.data-table td {
			padding: 0.5rem;
		}

		.table-stats {
			display: none;
		}
	}
</style>
