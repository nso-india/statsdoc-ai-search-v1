<script lang="ts">
	import { page } from '$app/stores';
	import { Copy } from 'lucide-svelte/icons';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { AdminChatAPI, type UserChatMessage } from '$lib/apis/admin-chats';
	import { getChatMessages } from '$lib/apis/chat';
	import { authToken } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';
	import { openProtectedMedia } from '$lib/utils/mediaAccess';

	// Import components for rich content rendering
	import MarkdownRenderer from '$lib/components/rag/MarkdownRenderer.svelte';
	import PlotlyChart from '$lib/components/charts/PlotlyChart.svelte';
	import { toast } from 'svelte-sonner';

	// Types for our message structure
	interface MessageContent {
		content: string;
		data_response?: {
			text?: string;
			dataframe?: string;
			figure?: any;
			table_names_identified?: string[];
			documents_relevance?: any[];
		};
		file_id?: number;
		file_name?: string;
		file_url?: string;
	}

	interface ChatMessage {
		id: string;
		role: 'user' | 'assistant';
		content: string | MessageContent;
		created_at?: string;
		timestamp?: string;
		chat_id?: string;
		file_id?: number;
		file_name?: string;
		file_url?: string;
	}

	// Get conversation ID from URL params
	let conversationId: string;
	let userId: number | undefined;
	let messages: ChatMessage[] = [];
	let loading = true;
	let error = '';

	// Theme support for markdown
	let theme: 'light' | 'dark' | 'auto' = 'auto';

	// Helper function to get message content
	function getMessageContent(message: ChatMessage): string {
		try {
			
			if (typeof message.content === 'string') {
				// Handle Python dict string format first
				if (message.content.startsWith('{') && message.content.includes('content')) {
					try {
						let jsonStr = message.content
							.replace(/'/g, '"')
							.replace(/True/g, 'true')
							.replace(/False/g, 'false')
							.replace(/None/g, 'null');
						
						const parsed = JSON.parse(jsonStr);
						
						if (message.role === 'user') {
							return parsed.content || message.content;
						} else {
							if (parsed.content && typeof parsed.content === 'object') {
								return parsed.content.response || parsed.content.content || message.content;
							}
							return parsed.response || parsed.content || message.content;
						}
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for content:', parseError);
						
						if (message.role === 'user') {
							const contentMatch = message.content.match(/'content':\s*'([^']*?)'/);
							if (contentMatch) {
								return contentMatch[1];
							}
						}
						return message.content;
					}
				}
				
				// Handle regular JSON string format from API
				if (message.content.startsWith('{')) {
					try {
						const parsed = JSON.parse(message.content);
						
						if (message.role === 'user') {
							return parsed.content || message.content;
						} else {
							if (parsed.content && typeof parsed.content === 'object') {
								return parsed.content.response || parsed.content.content || message.content;
							}
							return parsed.response || parsed.content || message.content;
						}
					} catch (parseError) {
						console.warn('❌ Failed to parse JSON for content:', parseError);
						return message.content;
					}
				}
				
				return message.content;
			} else if (message.content && typeof message.content === 'object') {
				if (message.role === 'user') {
					return message.content.content || '';
				} else {
					if (message.content.content && typeof message.content.content === 'object') {
						return message.content.content.response || message.content.content.content || '';
					}
					return message.content.response || message.content.content || '';
				}
			}
			return '';
		} catch (error) {
			console.warn('⚠️ Error processing message content:', error);
			return 'Error displaying message content';
		}
	}

	// Helper function to get data response
	function getDataResponse(message: ChatMessage) {
		try {
			if (typeof message.content === 'object' && message.content && message.content.data_response) {
				return message.content.data_response;
			}
			return null;
		} catch (error) {
			console.warn('Error processing data response:', error);
			return null;
		}
	}

	// Helper function to get file information
	function getFileInfo(message: ChatMessage) {
		try {
			// Check if file info is in the content object
			if (typeof message.content === 'object' && message.content) {
				if (message.content.file_id && message.content.file_name) {
					return {
						file_id: message.content.file_id,
						file_name: message.content.file_name,
						file_url: message.content.file_url
					};
				}
			}
			
			// Check if file info is directly on the message
			if (message.file_id && message.file_name) {
				return {
					file_id: message.file_id,
					file_name: message.file_name,
					file_url: message.file_url
				};
			}
			
			return null;
		} catch (error) {
			console.warn('⚠️ Error processing file info:', error);
			return null;
		}
	}

	// Helper function to get files array
	function getFiles(message: ChatMessage) {
		try {
			if (typeof message.content === 'string') {
				// Handle Python dict string format
				if (message.content.startsWith('{') && message.content.includes('files')) {
					try {
						let jsonStr = message.content
							.replace(/'/g, '"')
							.replace(/True/g, 'true')
							.replace(/False/g, 'false')
							.replace(/None/g, 'null');
						
						const parsed = JSON.parse(jsonStr);
						return parsed.files || [];
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for files:', parseError);
						return [];
					}
				}
				
				// Handle regular JSON string format
				if (message.content.startsWith('{')) {
					try {
						const parsed = JSON.parse(message.content);
						
						if (parsed.content && typeof parsed.content === 'object' && parsed.content.files) {
							return parsed.content.files || [];
						}
						
						return parsed.files || [];
					} catch (parseError) {
						console.warn('❌ Failed to parse JSON for files:', parseError);
						return [];
					}
				}
				
				return [];
			} else if (message.content && typeof message.content === 'object') {
				if (message.content.content && typeof message.content.content === 'object' && message.content.content.files) {
					return message.content.content.files || [];
				}
				
				return message.content.files || [];
			}
			return [];
		} catch (error) {
			console.warn('⚠️ Error processing files:', error);
			return [];
		}
	}

	// Helper function to get citations
	function getCitations(message: ChatMessage) {
		try {
			
			if (typeof message.content === 'string') {
				if (message.content.startsWith('{')) {
					try {
						const parsed = JSON.parse(message.content);
						
						// Handle nested structure: {"content": {"response": "...", "qdrant_data": {...}}}
						if (parsed.content && typeof parsed.content === 'object' && parsed.content.qdrant_data) {
							// Check for new citations array first
							if (parsed.content.qdrant_data.citations && Array.isArray(parsed.content.qdrant_data.citations)) {
								return parsed.content.qdrant_data.citations;
							}
							// Fallback to old context field
							const context = parsed.content.qdrant_data?.context;
							return context || null;
						}
						
						// Handle direct structure: {"response": "...", "qdrant_data": {...}}
						if (parsed.qdrant_data) {
							// Check for new citations array first
							if (parsed.qdrant_data.citations && Array.isArray(parsed.qdrant_data.citations)) {
								return parsed.qdrant_data.citations;
							}
							// Fallback to old context field
							const context = parsed.qdrant_data?.context;
							return context || null;
						}
						
						return null;
					} catch (parseError) {
						console.warn('❌ Failed to parse JSON for citations:', parseError);
						return null;
					}
				}
				
				// Handle Python dict string format (fallback)
				if (message.content.includes('qdrant_data')) {
					try {
						let jsonStr = message.content
							.replace(/'/g, '"')
							.replace(/True/g, 'true')
							.replace(/False/g, 'false')
							.replace(/None/g, 'null');
						
						const parsed = JSON.parse(jsonStr);
						// Check for new citations array first
						if (parsed.qdrant_data?.citations && Array.isArray(parsed.qdrant_data.citations)) {
							return parsed.qdrant_data.citations;
						}
						// Fallback to old context field
						const context = parsed.qdrant_data?.context;
						return context || null;
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for citations:', parseError);
						return null;
					}
				}
				
				return null;
			} else if (message.content && typeof message.content === 'object') {
				
				// Handle nested structure
				if (message.content.content && typeof message.content.content === 'object' && message.content.content.qdrant_data) {
					// Check for new citations array first
					if (message.content.content.qdrant_data.citations && Array.isArray(message.content.content.qdrant_data.citations)) {
						return message.content.content.qdrant_data.citations;
					}
					// Fallback to old context field
					const context = message.content.content.qdrant_data?.context;
					return context || null;
				}
				
				// Handle direct structure
				if (message.content.qdrant_data) {
					// Check for new citations array first
					if (message.content.qdrant_data.citations && Array.isArray(message.content.qdrant_data.citations)) {
						return message.content.qdrant_data.citations;
					}
					// Fallback to old context field
					const context = message.content.qdrant_data?.context;
					return context || null;
				}
				
				return null;
			}
			
			return null;
		} catch (error) {
			console.error('⚠️ Error getting citations:', error);
			return null;
		}
	}

	// Helper function to format timestamp
	function formatTimestamp(message: ChatMessage): string {
		const timestamp = message.created_at || message.timestamp;
		if (!timestamp) return '';
		
		const date = new Date(timestamp);
		return date.toLocaleDateString('en-US', { 
			month: '2-digit', 
			day: '2-digit', 
			year: 'numeric'
		}) + ' at ' + date.toLocaleTimeString('en-US', { 
			hour: 'numeric', 
			minute: '2-digit',
			hour12: true
		});
	}

	async function copyMessage(content: string | MessageContent) {
		try {
			const textContent = typeof content === 'string' ? content : (content?.content || '');
			if (textContent) {
				await navigator.clipboard.writeText(textContent);
				toast.success('Copied to clipboard successfully!');
			}
		} catch (err) {
			console.error('Failed to copy:', err);
			toast.error('Failed to copy to clipboard');
		}
	}

	async function loadChatHistory() {
		try {
			const response = await AdminChatAPI.getChatMessages(parseInt(conversationId), userId);
			
			const chatMessages = Array.isArray(response) ? response : response.messages || [];
			
			// Process API messages
			const processedMessages = (chatMessages || []).map((apiMessage: any) => {
				
				if (apiMessage.role === 'user') {
					return {
						id: apiMessage.id.toString(),
						role: 'user',
						content: apiMessage.content,
						created_at: apiMessage.created_at,
						timestamp: apiMessage.created_at || apiMessage.timestamp,
						chat_id: conversationId
					};
				}
				
				if (apiMessage.role === 'assistant') {
					try {
						let parsedContent;
						
						if (typeof apiMessage.content === 'object' && apiMessage.content !== null) {
							parsedContent = apiMessage.content;
						} else if (typeof apiMessage.content === 'string') {
							parsedContent = JSON.parse(apiMessage.content);
						} else {
							parsedContent = { content: null, data_response: null };
						}
						
						return {
							id: apiMessage.id.toString(),
							role: 'assistant',
							content: {
								content: parsedContent.content || '',
								data_response: parsedContent.data_response || null,
								file_id: apiMessage.file_id || null,
								file_name: apiMessage.file_name || null,
								file_url: apiMessage.file_url || null
							},
							created_at: apiMessage.created_at,
							timestamp: apiMessage.created_at || apiMessage.timestamp,
							chat_id: conversationId,
							file_id: apiMessage.file_id,
							file_name: apiMessage.file_name,
							file_url: apiMessage.file_url
						};
					} catch (parseError) {
						return {
							id: apiMessage.id.toString(),
							role: 'assistant',
							content: {
								content: apiMessage.content || '',
								data_response: null,
								file_id: apiMessage.file_id || null,
								file_name: apiMessage.file_name || null,
								file_url: apiMessage.file_url || null
							},
							created_at: apiMessage.created_at,
							timestamp: apiMessage.created_at || apiMessage.timestamp,
							chat_id: conversationId,
							file_id: apiMessage.file_id,
							file_name: apiMessage.file_name,
							file_url: apiMessage.file_url
						};
					}
				}
				
				return {
					id: apiMessage.id.toString(),
					...apiMessage,
					timestamp: apiMessage.created_at || apiMessage.timestamp,
					chat_id: conversationId
				};
			});
			
			// Filter valid messages
			const validMessages = processedMessages.filter(msg => {
				try {
					getMessageContent(msg);
					return true;
				} catch (error) {
					console.warn('Filtering out invalid message:', msg.id, error);
					return false;
				}
			});
			
			messages = validMessages;
		} catch (err) {
			console.error('Error loading chat history:', err);
			
			if (err instanceof Error && err.message.includes('404')) {
				error = 'Chat not found or access denied.';
			} else {
				error = 'Failed to load chat history.';
			}
			messages = [];
		}
	}

	// Initialize on mount
	onMount(() => {
		// Check authentication
		const token = get(authToken);
		if (!token) {
			goto('/login');
			return;
		}

		if (browser && $page.params.id) {
			conversationId = $page.params.id;
			// Get user ID from URL search params
			userId = $page.url.searchParams.get('user') ? parseInt($page.url.searchParams.get('user')!) : undefined;
			
			if (conversationId) {
				loadChatHistory().finally(() => {
					loading = false;
				});
			} else {
				error = 'Invalid chat ID';
				loading = false;
			}
		}
	});

	// Reactive statement
	$: if ($page.params.id && browser) {
		const newId = $page.params.id;
		const newUserId = $page.url.searchParams.get('user') ? parseInt($page.url.searchParams.get('user')!) : undefined;
		
		if (newId !== conversationId && newId) {
			conversationId = newId;
			userId = newUserId;
			loading = true;
			error = '';
			loadChatHistory().finally(() => {
				loading = false;
			});
		} else if (newUserId !== userId) {
			// User ID changed, reload chat history
			userId = newUserId;
			loading = true;
			error = '';
			loadChatHistory().finally(() => {
				loading = false;
			});
		}
	}
</script>

<svelte:head>
	<title>Chat {conversationId || 'Loading...'} - MOSPI</title>
</svelte:head>

<style>
	/* Custom styles */
	:global(.line-clamp-1) {
		overflow: hidden;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 1;
		line-clamp: 1;
	}

	.markdown-prose {
		color: inherit;
	}

	.chat-user, .chat-assistant {
		position: relative;
	}

	.assistant-message-profile-image {
		width: 2rem;
		height: 2rem;
	}

	/* Chart container styling */
	.chart-container {
		width: 100%;
		max-width: 100%;
		overflow: hidden;
	}

	.chart-container :global(svg) {
		max-width: 100%;
		height: auto;
	}

	.chart-container :global(div[id^="plotly"]) {
		max-width: 100% !important;
		width: 100% !important;
	}

	.chart-container :global(.plotly-graph-div) {
		max-width: 100% !important;
		width: 100% !important;
	}

	/* Table styling for data responses */
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

	:global(.dark .prose th) {
		background-color: #374151;
		border-color: #4b5563;
	}

	:global(.dark .prose td) {
		border-color: #4b5563;
	}
</style>

<div class="h-full flex flex-col bg-white dark:bg-gray-900 max-h-full overflow-hidden">

	{#if loading}
		<div class="flex h-full items-center justify-center">
			<div class="text-center">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
				<p class="text-gray-600 dark:text-gray-400">Loading conversation...</p>
			</div>
		</div>
	{:else if error}
		<div class="flex h-full items-center justify-center">
			<div class="text-center">
				<p class="text-red-600 dark:text-red-400 mb-4">{error}</p>
				<button 
					on:click={() => { loading = true; loadChatHistory().finally(() => loading = false); }}
					class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
				>
					Retry
				</button>
			</div>
		</div>
	{:else}
		<!-- Messages Area - Scrollable -->
		<div class="flex-1 overflow-y-auto overflow-x-hidden px-4 pt-4 pb-4">
			{#if messages.length === 0}
				<div class="text-center py-12">
					<div class="text-gray-400 dark:text-gray-600 mb-4">
						<svg class="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
						</svg>
					</div>
					<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No messages found</h3>
					<p class="text-gray-500 dark:text-gray-400">This conversation appears to be empty.</p>
				</div>
			{/if}

			{#each messages as message (message.id || message.created_at)}
				{#if message.role === 'user'}
					<!-- User Message -->
					<div class="flex flex-col justify-between px-0 mb-6 w-full max-w-5xl mx-auto rounded-lg group">
						<div class="flex w-full user-message group" id="message-{message.id}">
							<div class="flex-auto w-0 max-w-full pl-1">
								<div class="flex justify-end pr-2 text-xs">
									<div class="text-[0.65rem] text-gray-400 dark:text-gray-600 font-medium first-letter:capitalize mb-0.5">
										<div class="flex">
											<span class="line-clamp-1">{formatTimestamp(message)}</span>
										</div>
									</div>
								</div>
								<div class="chat-user w-full min-w-full markdown-prose">
									<div class="w-full">
										<div class="flex justify-end pb-1">
											<div class="rounded-3xl max-w-[90%] px-5 py-3 bg-gray-50 dark:bg-gray-850 rounded-tr-lg">
												<p dir="auto" class="whitespace-pre-wrap text-gray-800 dark:text-gray-100">{getMessageContent(message)}</p>
											</div>
										</div>
										
										<!-- Files Display -->
										{#if getFiles(message).length > 0}
											{@const files = getFiles(message)}
											<div class="mt-2 flex justify-end pr-2">
												<div class="max-w-[90%]">
													<div class="text-xs text-gray-500 mb-1">Attachments:</div>
													<div class="flex flex-wrap gap-2">
														{#each files as file}
															<div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700">
																<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
																	<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
																</svg>
																{file.file_name ? file.file_name.split('/').pop() : 'File'}
															</div>
														{/each}
													</div>
												</div>
											</div>
										{:else if getFileInfo(message)}
											{@const fileInfo = getFileInfo(message)}
											<div class="mt-2 flex justify-end pr-2">
												<div class="max-w-[90%]">
													<div class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
														<div class="flex items-center gap-2">
															<p class="text-sm font-medium text-blue-700 dark:text-blue-300">
																File: {fileInfo.file_name || 'Unknown file'}
															</p>
														</div>
													</div>
												</div>
											</div>
										{/if}
									</div>
								</div>
							</div>
						</div>
					</div>
				{:else}
					<!-- Assistant Message -->
					<div class="flex flex-col justify-between px-4 mb-6 w-full max-w-5xl mx-auto rounded-lg group">
						<div class="flex w-full message-{message.id}" id="message-{message.id}">
							<div class="shrink-0 ltr:mr-3 rtl:ml-3 mt-1">
								<img crossorigin="anonymous" src="/apple-touch-icon.png" class="size-8 assistant-message-profile-image object-cover rounded-full" alt="profile" draggable="false">
							</div>
							<div class="flex-auto w-0 pl-1 relative">
								<div class="self-center text-xs text-gray-400 dark:text-gray-600 font-medium first-letter:capitalize mb-2">
									<div class="flex">
										<span class="line-clamp-1">{formatTimestamp(message)}</span>
									</div>
								</div>
								<div>
									<div class="chat-assistant w-full min-w-full markdown-prose">
										<div class="w-full flex flex-col relative" id="response-content-container">
											<!-- Main content with markdown rendering -->
											<div class="prose prose-sm max-w-none dark:prose-invert text-gray-800 dark:text-gray-100">
												<MarkdownRenderer content={getMessageContent(message)} {theme} />
											</div>

											<!-- File Information Display -->
											{#if getFileInfo(message)}
												{@const fileInfo = getFileInfo(message)}
												<div class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
													<div class="flex items-center gap-2">
														<p class="text-sm font-medium text-blue-700 dark:text-blue-300">
															File: {fileInfo.file_name || 'Unknown file'}
														</p>
													</div>
												</div>
											{/if}
											
											<!-- Data Response Section -->
											{#if getDataResponse(message)}
												{@const dataResponse = getDataResponse(message)}
												
												<!-- Plotly Chart Display -->
												{#if dataResponse.figure}
													<div class="mt-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
														<h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Data Visualization</h4>
														<div class="chart-container">
															<PlotlyChart figureData={dataResponse.figure} className="rounded-md overflow-hidden" debug={true} />
														</div>
													</div>
												{/if}

												<!-- Data Table Display -->
												{#if dataResponse.dataframe}
													<div class="mt-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
														<h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Query Results</h4>
														<div class="overflow-x-auto">
															<div class="prose prose-sm max-w-none dark:prose-invert">
																<MarkdownRenderer content={dataResponse.dataframe} {theme} />
															</div>
														</div>
													</div>
												{/if}

												<!-- Table Names Identified -->
												{#if dataResponse.table_names_identified && dataResponse.table_names_identified.length > 0}
													<div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
														<h4 class="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">Data Sources Used</h4>
														<div class="flex flex-wrap gap-2">
															{#each dataResponse.table_names_identified as tableName}
																<span class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 rounded-full">
																	{tableName}
																</span>
															{/each}
														</div>
													</div>
												{/if}

												<!-- Document Relevance -->
												{#if dataResponse.documents_relevance && dataResponse.documents_relevance.length > 0}
													<div class="mt-4 p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
														<h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Related Documents</h4>
														<div class="space-y-2">
															{#each dataResponse.documents_relevance.slice(0, 3) as doc, index}
																<div class="flex items-start gap-2 text-xs">
																	<span class="flex-shrink-0 w-5 h-5 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300">
																		{index + 1}
																	</span>
																	<div class="flex-1">
																		<p class="text-gray-700 dark:text-gray-300 font-medium">
																			{doc.metadata?.file_name || 'Document reference'}
																		</p>
																		{#if doc.score}
																			<p class="text-gray-500 dark:text-gray-400">
																				Relevance: {(doc.score * 100).toFixed(1)}%
																			</p>
																		{/if}
																		{#if doc.document}
																			<p class="text-gray-600 dark:text-gray-400 text-xs mt-1">
																				{doc.document}
																			</p>
																		{:else if doc.payload?.text}
																			<p class="text-gray-600 dark:text-gray-400 text-xs mt-1">
																				{doc.payload.text}
																			</p>
																		{:else if doc.metadata?.document}
																			<p class="text-gray-600 dark:text-gray-400 text-xs mt-1">
																				{doc.metadata.document}
																			</p>
																		{/if}
																	</div>
																</div>
															{/each}
														</div>
													</div>
												{/if}
											{/if}

										<!-- Citations Section -->
										{#if getCitations(message)}
											{@const citations = getCitations(message)}
											<div class="mt-4">
												<details class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
													<summary class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
														Citations
													</summary>
													<div class="mt-2 space-y-3">
														{#if Array.isArray(citations)}
															<!-- New format: citations array with document names -->
															{#each citations as citation, index}
																<div class="p-3 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-600">
																	{#if citation.document_name}
																		<div class="text-sm font-medium mb-2">
																			{#if citation.document_link}
																				<button
																					type="button"
																					on:click={() => openProtectedMedia(citation.document_link)} 
																					class="text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 underline decoration-blue-400 dark:decoration-blue-500 hover:decoration-blue-600 dark:hover:decoration-blue-300 transition-colors inline-flex items-center gap-1 cursor-pointer"
																				>
																					{citation.document_name}
																					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
																						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
																					</svg>
																				</button>
																			{:else}
																				<span class="text-blue-700 dark:text-blue-300">{citation.document_name}</span>
																			{/if}
																		</div>
																	{/if}
																	<div class="text-xs text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
																		{citation.content}
																	</div>
																</div>
															{/each}
														{:else}
															<!-- Legacy format: single context string -->
															<div class="p-3 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-600">
																<div class="text-xs text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
																	{citations}
																</div>
															</div>
														{/if}
													</div>
												</details>
											</div>
										{/if}
									</div>
									</div>
								</div>
								
								<!-- Copy Button -->
								<div class="flex justify-start overflow-x-auto buttons text-gray-600 dark:text-gray-400 mt-2">
									<div class="flex">
										<button 
											aria-label="Copy" 
											on:click={() => copyMessage(message.content)}
											class="p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition copy-response-button"
										>
											<Copy class="w-4 h-4" />
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			{/each}
		</div>
	{/if}
</div>