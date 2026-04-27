<script lang="ts">
	export let message: {
		id?: number;
		role: 'user' | 'assistant';
		content: string | any;
		timestamp: string;
		chat_id?: number;
		data_response?: {
			text?: string;
			dataframe?: string;
			figure?: string;
			table_names_identified?: string[];
			documents_relevance?: any[];
		};
	};

	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	
	let plotlyContainer: HTMLDivElement;

	// Parse user message content
	function parseUserContent(content: string | any) {
		console.log('🔍 Parsing user content:', content, typeof content);
		
		if (typeof content === 'string') {
			// Handle Python dict string format (e.g., "{'content': 'text', 'files': [...]}")
			if (content.startsWith('{') && content.includes('content')) {
				try {
					// Convert Python dict format to JSON format
					let jsonStr = content
						.replace(/'/g, '"')  // Replace single quotes with double quotes
						.replace(/True/g, 'true')  // Handle Python booleans
						.replace(/False/g, 'false')
						.replace(/None/g, 'null');
					
					const parsed = JSON.parse(jsonStr);
					console.log('✅ Parsed user Python dict:', parsed);
					return {
						content: parsed.content || content,
						files: parsed.files || []
					};
				} catch (parseError) {
					console.warn('❌ Failed to parse Python dict format:', parseError);
					// If parsing fails, try to extract content and files manually
					const contentMatch = content.match(/'content':\s*'([^']*?)'/);
					const extractedContent = contentMatch ? contentMatch[1] : content;
					
					// Try to extract files manually using a more flexible regex
					const filesMatch = content.match(/'files':\s*(\[.*?\])/s);
					let files = [];
					if (filesMatch) {
						try {
							// Handle complex nested objects in files array
							let filesStr = filesMatch[1];
							
							// Replace single quotes with double quotes, but be careful with nested objects
							filesStr = filesStr
								.replace(/'/g, '"')
								.replace(/True/g, 'true')
								.replace(/False/g, 'false')
								.replace(/None/g, 'null');
							
							files = JSON.parse(filesStr);
							console.log('✅ Extracted files via regex:', files);
						} catch (regexParseError) {
							console.warn('❌ Failed to parse extracted files:', regexParseError);
							
							// Last resort: try to extract basic file info manually
							const filePatterns = content.match(/'id':\s*(\d+)[^}]*'file_name':\s*'([^']*)'[^}]*'file_url':\s*'([^']*)'/g);
							if (filePatterns) {
								files = filePatterns.map((pattern, index) => {
									const idMatch = pattern.match(/'id':\s*(\d+)/);
									const nameMatch = pattern.match(/'file_name':\s*'([^']*)'/);
									const urlMatch = pattern.match(/'file_url':\s*'([^']*)'/);
									
									return {
										id: idMatch ? parseInt(idMatch[1]) : index,
										file_name: nameMatch ? nameMatch[1] : 'Unknown file',
										file_url: urlMatch ? urlMatch[1] : ''
									};
								});
								console.log('✅ Manually extracted file info:', files);
							}
						}
					}
					
					return { content: extractedContent, files };
				}
			}
			
			// Try to parse as regular JSON
			try {
				const parsed = JSON.parse(content);
				return {
					content: parsed.content || content,
					files: parsed.files || []
				};
			} catch {
				return { content, files: [] };
			}
		}
		
		// Handle object content
		if (content && typeof content === 'object') {
			return { 
				content: content.content || content, 
				files: content.files || [] 
			};
		}
		
		return { content: content || '', files: [] };
	}

	// Parse assistant message content
	function parseAssistantContent(content: string | any) {
		console.log('🔍 Parsing assistant content:', content, typeof content);
		
		if (typeof content === 'string') {
			// Handle JSON string format from API
			if (content.startsWith('{')) {
				try {
					const parsed = JSON.parse(content);
					console.log('✅ Parsed JSON string:', parsed);
					
					// Handle nested content structure: {"content": {"response": "...", "qdrant_data": {...}}}
					if (parsed.content && typeof parsed.content === 'object') {
						return {
							response: parsed.content.response || parsed.content.content || content,
							qdrant_data: parsed.content.qdrant_data || null
						};
					}
					
					// Handle direct structure: {"response": "...", "qdrant_data": {...}}
					return {
						response: parsed.response || parsed.content || content,
						qdrant_data: parsed.qdrant_data || null
					};
				} catch (parseError) {
					console.warn('❌ Failed to parse JSON string:', parseError);
					return { response: content, qdrant_data: null };
				}
			}
			
			// Handle Python dict string format (fallback)
			if (content.includes('qdrant_data')) {
				try {
					let jsonStr = content
						.replace(/'/g, '"')
						.replace(/True/g, 'true')
						.replace(/False/g, 'false')
						.replace(/None/g, 'null');
					
					const parsed = JSON.parse(jsonStr);
					console.log('✅ Parsed Python dict:', parsed);
					return {
						response: parsed.content || parsed.response || content,
						qdrant_data: parsed.qdrant_data || null
					};
				} catch (parseError) {
					console.warn('❌ Failed to parse Python dict format:', parseError);
					return { response: content, qdrant_data: null };
				}
			}
			
			return { response: content, qdrant_data: null };
		} else if (content && typeof content === 'object') {
			// Handle already parsed object (from WebSocket)
			console.log('✅ Object content:', content);
			
			// Handle nested content structure
			if (content.content && typeof content.content === 'object') {
				return {
					response: content.content.response || content.content.content || JSON.stringify(content),
					qdrant_data: content.content.qdrant_data || null
				};
			}
			
			// Handle direct structure
			return {
				response: content.response || content.content || JSON.stringify(content),
				qdrant_data: content.qdrant_data || null
			};
		}
		
		return { response: content || '', qdrant_data: null };
	}

	$: {
		console.log('🔍 Message component reactive update:', {
			id: message.id,
			role: message.role,
			content: message.content,
			contentType: typeof message.content
		});
		
		if (message.role === 'user') {
			const parsed = parseUserContent(message.content);
			console.log('🔍 User content parsed:', parsed);
		} else {
			const parsed = parseAssistantContent(message.content);
			console.log('🔍 Assistant content parsed:', parsed);
		}
	}

	$: userContent = message.role === 'user' ? parseUserContent(message.content) : null;
	$: assistantContent = message.role === 'assistant' ? parseAssistantContent(message.content) : null;
	
	let plotlyContainer: HTMLDivElement;

	onMount(() => {
		// Render Plotly chart if figure data exists
		if (message.data_response?.figure && plotlyContainer) {
			renderPlotlyChart();
		}
	});

	async function renderPlotlyChart() {
		try {
			// Dynamically import Plotly
			const Plotly = await import('plotly.js-dist-min') as any;
			
			// Parse the HTML and extract the JSON data
			const parser = new DOMParser();
			const doc = parser.parseFromString(message.data_response!.figure!, 'text/html');
			const scriptTag = doc.querySelector('script[type="application/json"]');
			
			if (scriptTag) {
				const plotData = JSON.parse(scriptTag.textContent || '{}');
				await Plotly.newPlot(plotlyContainer, plotData.data, plotData.layout, {
					responsive: true,
					displayModeBar: true
				});
			}
		} catch (error) {
			console.error('Failed to render Plotly chart:', error);
		}
	}

	function formatTimestamp(timestamp: string) {
		return new Date(timestamp).toLocaleTimeString([], { 
			hour: '2-digit', 
			minute: '2-digit' 
		});
	}

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text).then(() => {
			toast.success('Copied to clipboard successfully!');
		}).catch(() => {
			toast.error('Failed to copy to clipboard');
		});
	}
</script>

<div class="flex items-start space-x-3 {message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}">
	<!-- Avatar -->
	<div class="w-8 h-8 rounded-full flex items-center justify-center {message.role === 'user' ? 'bg-blue-500' : 'bg-gray-500'}">
		{#if message.role === 'user'}
			<svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
				<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
			</svg>
		{:else}
			<svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
				<path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
				<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
			</svg>
		{/if}
	</div>

	<!-- Message Content -->
	<div class="flex-1 {message.role === 'user' ? 'max-w-xs lg:max-w-md' : 'max-w-full'}">
		<div class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 {message.role === 'user' ? 'bg-blue-50 border-blue-200' : ''}">
			<!-- Main message content -->
			<div class="prose prose-sm max-w-none">
				{#if message.role === 'user'}
					{@html (userContent?.content || message.content).replace(/\n/g, '<br>')}
				{:else}
					{@html (assistantContent?.response || message.content).replace(/\n/g, '<br>')}
				{/if}
			</div>

			<!-- Citations for assistant messages -->
			{#if message.role === 'assistant' && assistantContent?.qdrant_data?.context}
				<div class="mt-4">
					<details class="bg-gray-50 rounded-lg p-3">
						<summary class="text-sm font-medium text-gray-700 cursor-pointer">
							Citations
						</summary>
						<div class="mt-2 p-3 bg-white rounded border border-gray-200">
							<div class="text-xs text-gray-800 leading-relaxed whitespace-pre-wrap">
								{assistantContent.qdrant_data.context}
							</div>
						</div>
					</details>
				</div>
			{/if}

			<!-- Data Response (for assistant messages) -->
			{#if message.role === 'assistant' && message.data_response}
				<div class="mt-4 space-y-4">
					<!-- Dataframe Table -->
					{#if message.data_response.dataframe}
						<div class="border border-gray-200 rounded-lg overflow-hidden">
							<div class="bg-gray-50 px-3 py-2 border-b border-gray-200 flex items-center justify-between">
								<h4 class="text-sm font-medium text-gray-700">Data Results</h4>
								<button 
									on:click={() => copyToClipboard(message.data_response?.dataframe || '')}
									class="text-xs text-gray-500 hover:text-gray-700"
								>
									Copy
								</button>
							</div>
							<div class="p-3 overflow-x-auto">
								<div class="prose prose-sm max-w-none">
									{@html message.data_response.dataframe}
								</div>
							</div>
						</div>
					{/if}

					<!-- Plotly Chart -->
					{#if message.data_response.figure}
						<div class="border border-gray-200 rounded-lg overflow-hidden">
							<div class="bg-gray-50 px-3 py-2 border-b border-gray-200">
								<h4 class="text-sm font-medium text-gray-700">Visualization</h4>
							</div>
							<div class="p-3">
								<div bind:this={plotlyContainer} class="w-full h-64"></div>
							</div>
						</div>
					{/if}

					<!-- Table Names -->
					{#if message.data_response.table_names_identified && message.data_response.table_names_identified.length > 0}
						<div class="bg-gray-50 rounded-lg p-3">
							<h4 class="text-sm font-medium text-gray-700 mb-2">Tables Analyzed</h4>
							<div class="flex flex-wrap gap-1">
								{#each message.data_response.table_names_identified as tableName}
									<span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
										{tableName}
									</span>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Relevant Documents -->
					{#if message.data_response.documents_relevance && message.data_response.documents_relevance.length > 0}
						<details class="bg-gray-50 rounded-lg p-3">
							<summary class="text-sm font-medium text-gray-700 cursor-pointer">
								Relevant Documents ({message.data_response.documents_relevance.length})
							</summary>
							<div class="mt-2 space-y-3">
								{#each message.data_response.documents_relevance.slice(0, 5) as doc}
									<div class="bg-white rounded-lg p-3 border border-gray-200 text-xs">
										<!-- Document Header -->
										<div class="flex justify-between items-start mb-2">
											<div class="font-medium text-gray-900">
												{doc.metadata?.file_name || doc.metadata?.title || 'Document'}
											</div>
											{#if doc.score}
												<div class="text-green-600 font-medium">
													{(doc.score * 100).toFixed(1)}%
												</div>
											{/if}
										</div>
										
										<!-- Document ID -->
										{#if doc.id}
											<div class="text-gray-500 mb-2">
												<span class="font-medium">ID:</span> {doc.id}
											</div>
										{/if}
										
										<!-- File Information -->
										{#if doc.metadata}
											<div class="mb-2 space-y-1">
												{#if doc.metadata.file_id}
													<div class="text-gray-600">
														<span class="font-medium">File ID:</span> {doc.metadata.file_id}
													</div>
												{/if}
												{#if doc.metadata.file_name}
													<div class="text-gray-600">
														<span class="font-medium">File:</span> {doc.metadata.file_name}
													</div>
												{/if}
											</div>
										{/if}
										
										<!-- Document Content -->
										{#if doc.document}
											<div class="mt-2 p-2 bg-gray-50 rounded border-l-4 border-blue-400">
												<div class="text-gray-700 font-medium text-xs mb-1">Content:</div>
												<div class="text-gray-800 text-xs leading-relaxed whitespace-pre-wrap">
													{doc.document.length > 200 ? doc.document.substring(0, 200) + '...' : doc.document}
												</div>
											</div>
										{/if}
										
										<!-- Metadata Document (if different from main document) -->
										{#if doc.metadata?.document && doc.metadata.document !== doc.document}
											<div class="mt-2 p-2 bg-yellow-50 rounded border-l-4 border-yellow-400">
												<div class="text-gray-700 font-medium text-xs mb-1">Metadata Content:</div>
												<div class="text-gray-800 text-xs leading-relaxed whitespace-pre-wrap">
													{doc.metadata.document.length > 200 ? doc.metadata.document.substring(0, 200) + '...' : doc.metadata.document}
												</div>
											</div>
										{/if}
									</div>
								{/each}
							</div>
						</details>
					{/if}
				</div>
			{/if}

			<!-- Timestamp -->
			<div class="mt-2 text-xs text-gray-500">
				{formatTimestamp(message.timestamp)}
			</div>
		</div>

		<!-- Files for user messages (moved outside message bubble) -->
		{#if message.role === 'user' && userContent?.files && userContent.files.length > 0}
			<div class="mt-2">
				<div class="text-xs text-gray-500 mb-1">Attachments:</div>
				<div class="flex flex-wrap gap-2">
					{#each userContent.files as file}
						<div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
							<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
							</svg>
							{file.file_name ? file.file_name.split('/').pop() : 'File'}
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	:global(.prose table) {
		font-size: 0.75rem;
		border-collapse: collapse;
		width: 100%;
	}
	
	:global(.prose th),
	:global(.prose td) {
		border: 1px solid #e5e7eb;
		padding: 0.25rem 0.5rem;
		text-align: left;
	}
	
	:global(.prose th) {
		background-color: #f9fafb;
		font-weight: 600;
	}
</style>
