<script lang="ts">
	import { page } from '$app/stores';
	import { ArrowUp, Copy, MoreVertical, Edit, Volume2, RotateCcw, MessageCircle, Lightbulb, Mic, Plus, Check, X } from '@lucide/svelte/icons';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { writable, get } from 'svelte/store';
	import { getChatMessages, getChatDetail } from '$lib/apis/chat';
	import { createChatWebSocket, type ChatWebSocketService } from '$lib/services/chat-websocket';
	import { authToken, user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { getLanguages, type Language } from '$lib/api/languages';
	import { uploadFiles, validateFileType, validateFileSize, type FileUploadResponse } from '$lib/apis/files';
	import { newChatApi } from '$lib/api/newchat';
	import FileChip from '$lib/components/ui/FileChip.svelte';
	import VoiceRecording from '$lib/components/VoiceRecording.svelte';
	import { openProtectedMedia } from '$lib/utils/mediaAccess';
	import { getKnowledgeBase } from '$lib/api/knowledgebase';

	// Import components for rich content rendering
	import MarkdownRenderer from '$lib/components/rag/MarkdownRenderer.svelte';
	import PlotlyChart from '$lib/components/charts/PlotlyChart.svelte';
	import { toast } from 'svelte-sonner';
	import ResponseFeedbackBar from '$lib/components/chat/ResponseFeedbackBar.svelte';
	import {
		fetchChatResponseFeedback,
		type ResponseFeedbackRating
	} from '$lib/api/responseFeedback';

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
	let messages: ChatMessage[] = [];
	let responseFeedbackByMessageId: Record<string, ResponseFeedbackRating> = {};
	let loading = true;
	let error = '';
	let sending = false;

	// WebSocket connection
	let chatWebSocket: ChatWebSocketService | null = null;
	let wsConnected = false;
	let connected = false;
	const connectionStatus = writable<'connecting' | 'connected' | 'disconnected'>('disconnected');

	// Input handling
	let inputValue = '';
	let isInputEmpty = true;
	let textarea: HTMLTextAreaElement;
	let messagesContainer: HTMLElement;

	// Edit message handling
	let editingMessageId: string | null = null;
	let editValue = '';
	let editTextarea: HTMLTextAreaElement;

	// Loading states
	let isLoading = false;

	// Theme support for markdown
	let theme: 'light' | 'dark' | 'auto' = 'auto';

	// File upload state
	let fileInput: HTMLInputElement;
	let selectedFiles: File[] = [];
	let uploadingFiles = false;
	let uploadProgress = 0;

	// Voice recording state
	let recording = false;
	let recordingLoading = false;

	// Language selection state
	let languages: Language[] = [];
	let selectedLanguageId: string | null = null;  // UUID of selected language
	
	// Knowledge base info
	let knowledgeBaseName: string | null = null;
	
	// Admin check
	let isAdmin = false;
	$: isAdmin = $user?.is_superuser || $user?.is_staff || false;

	// Disclaimer modal
	let showDisclaimerModal = false;

	// Helper function to get message content
	function getMessageContent(message: ChatMessage): string {
		try {
			console.log('🔍 Getting message content for:', message.id, message.content, typeof message.content);
			
			if (typeof message.content === 'string') {
				// Handle Python dict string format first (e.g., "{'content': 'text', 'files': [...]}")
				if (message.content.startsWith('{') && message.content.includes('content')) {
					try {
						// Convert Python dict format to JSON format
						let jsonStr = message.content
							.replace(/'/g, '"')  // Replace single quotes with double quotes
							.replace(/True/g, 'true')  // Handle Python booleans
							.replace(/False/g, 'false')
							.replace(/None/g, 'null');
						
						const parsed = JSON.parse(jsonStr);
						console.log('✅ Parsed Python dict for content:', parsed);
						
						if (message.role === 'user') {
							// For user messages, return the content field
							const userContent = parsed.content || message.content;
							return typeof userContent === 'string' ? userContent : String(userContent || '');
						} else {
							// For assistant messages, handle nested structure
							if (parsed.content && typeof parsed.content === 'object') {
								const assistantContent = parsed.content.response || parsed.content.content || message.content;
								return typeof assistantContent === 'string' ? assistantContent : String(assistantContent || '');
							}
							// Handle direct structure
							const directContent = parsed.response || parsed.content || message.content;
							return typeof directContent === 'string' ? directContent : String(directContent || '');
						}
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for content:', parseError);
						
						// Try to extract content manually
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
						console.log('✅ Parsed regular JSON for content:', parsed);
						
						if (message.role === 'user') {
							const userContent = parsed.content || message.content;
							return typeof userContent === 'string' ? userContent : String(userContent || '');
						} else {
							// Handle nested structure: {"content": {"response": "...", "qdrant_data": {...}}}
							if (parsed.content && typeof parsed.content === 'object') {
								const nestedContent = parsed.content.response || parsed.content.content || message.content;
								return typeof nestedContent === 'string' ? nestedContent : String(nestedContent || '');
							}
							// Handle direct structure: {"response": "...", "qdrant_data": {...}}
							const directContent = parsed.response || parsed.content || message.content;
							return typeof directContent === 'string' ? directContent : String(directContent || '');
						}
					} catch (parseError) {
						console.warn('❌ Failed to parse JSON for content:', parseError);
						return message.content;
					}
				}
				
				return message.content;
			} else if (message.content && typeof message.content === 'object') {
				// Handle already parsed object (from WebSocket)
				if (message.role === 'user') {
					const userContent = message.content.content || '';
					return typeof userContent === 'string' ? userContent : String(userContent);
				} else {
					// Handle nested structure
					if (message.content.content && typeof message.content.content === 'object') {
						const nestedContent = message.content.content.response || message.content.content.content || '';
						return typeof nestedContent === 'string' ? nestedContent : String(nestedContent);
					}
					// Handle direct structure
					const directContent = message.content.response || message.content.content || '';
					return typeof directContent === 'string' ? directContent : String(directContent);
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

	// Helper function to get file information (legacy single file)
	function getFileInfo(message: ChatMessage) {
		try {
			console.log('🔍 Checking file info for message:', message.id, message);
			
			// Check if file info is in the content object (WebSocket format)
			if (typeof message.content === 'object' && message.content) {
				console.log('📄 Message content object:', message.content);
				if (message.content.file_id && message.content.file_name) {
					const fileInfo = {
						file_id: message.content.file_id,
						file_name: message.content.file_name,
						file_url: message.content.file_url
					};
					console.log('✅ Found file info in content:', fileInfo);
					return fileInfo;
				}
			}
			
			// Check if file info is directly on the message (API format)
			if (message.file_id && message.file_name) {
				const fileInfo = {
					file_id: message.file_id,
					file_name: message.file_name,
					file_url: message.file_url
				};
				console.log('✅ Found file info on message:', fileInfo);
				return fileInfo;
			}
			
			console.log('❌ No file info found for message:', message.id);
			return null;
		} catch (error) {
			console.warn('⚠️ Error processing file info:', error);
			return null;
		}
	}

	// Helper function to get files array (new format)
	function getFiles(message: ChatMessage) {
		try {
			console.log('🔍 Getting files for message:', message.id, message.content, typeof message.content);
			
			if (typeof message.content === 'string') {
				// Handle Python dict string format first (e.g., "{'content': 'text', 'files': [...]}")
				if (message.content.startsWith('{') && message.content.includes('files')) {
					try {
						// Convert Python dict format to JSON format
						let jsonStr = message.content
							.replace(/'/g, '"')  // Replace single quotes with double quotes
							.replace(/True/g, 'true')  // Handle Python booleans
							.replace(/False/g, 'false')
							.replace(/None/g, 'null');
						
						const parsed = JSON.parse(jsonStr);
						console.log('✅ Parsed Python dict for files:', parsed);
						const files = parsed.files || [];
						console.log('✅ Extracted files:', files);
						return files;
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for files:', parseError);
						
						// Try to extract files manually using a more robust regex
						const filesMatch = message.content.match(/'files':\s*(\[.*?\])/s);
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
								
								const files = JSON.parse(filesStr);
								console.log('✅ Extracted files via regex:', files);
								return files;
							} catch (regexParseError) {
								console.warn('❌ Failed to parse extracted files:', regexParseError);
								
								// Last resort: try to extract basic file info manually
								const filePatterns = message.content.match(/'id':\s*(\d+)[^}]*'file_name':\s*'([^']*)'[^}]*'file_url':\s*'([^']*)'/g);
								if (filePatterns) {
									const files = filePatterns.map((pattern, index) => {
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
									return files;
								}
								return [];
							}
						}
						return [];
					}
				}
				
				// Handle regular JSON string format from API
				if (message.content.startsWith('{')) {
					try {
						const parsed = JSON.parse(message.content);
						console.log('✅ Parsed regular JSON for files:', parsed);
						
						// Handle nested structure: {"content": {"content": "text", "files": [...]}}
						if (parsed.content && typeof parsed.content === 'object' && parsed.content.files) {
							return parsed.content.files || [];
						}
						
						// Handle direct structure: {"content": "text", "files": [...]}
						return parsed.files || [];
					} catch (parseError) {
						console.warn('❌ Failed to parse JSON for files:', parseError);
						return [];
					}
				}
				
				return [];
			} else if (message.content && typeof message.content === 'object') {
				// Handle already parsed object (from WebSocket)
				console.log('✅ Object content for files:', message.content);
				
				// Handle nested structure
				if (message.content.content && typeof message.content.content === 'object' && message.content.content.files) {
					return message.content.content.files || [];
				}
				
				// Handle direct structure
				return message.content.files || [];
			}
			return [];
		} catch (error) {
			console.warn('⚠️ Error processing files:', error);
			return [];
		}
	}

	// Helper function to get citations (qdrant_data)
	function getCitations(message: ChatMessage) {
		try {
			console.log('🔍 Checking citations for message:', message.id, message.content, typeof message.content);
			
			if (typeof message.content === 'string') {
				// Handle JSON string format from API
				if (message.content.startsWith('{')) {
					try {
						const parsed = JSON.parse(message.content);
						console.log('✅ Parsed JSON for citations:', parsed);
						
						// Handle nested structure: {"content": {"response": "...", "qdrant_data": {...}}}
						if (parsed.content && typeof parsed.content === 'object' && parsed.content.qdrant_data) {
							// Check for new citations array first
							if (parsed.content.qdrant_data.citations && Array.isArray(parsed.content.qdrant_data.citations)) {
								console.log('✅ Found nested qdrant_data citations array:', parsed.content.qdrant_data.citations);
								return parsed.content.qdrant_data.citations;
							}
							// Fallback to old context field
							const context = parsed.content.qdrant_data?.context;
							console.log('✅ Found nested qdrant_data context:', context);
							return context || null;
						}
						
						// Handle direct structure: {"response": "...", "qdrant_data": {...}}
						if (parsed.qdrant_data) {
							// Check for new citations array first
							if (parsed.qdrant_data.citations && Array.isArray(parsed.qdrant_data.citations)) {
								console.log('✅ Found direct qdrant_data citations array:', parsed.qdrant_data.citations);
								return parsed.qdrant_data.citations;
							}
							// Fallback to old context field
							const context = parsed.qdrant_data?.context;
							console.log('✅ Found direct qdrant_data context:', context);
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
							console.log('✅ Parsed Python dict qdrant_data citations array:', parsed.qdrant_data.citations);
							return parsed.qdrant_data.citations;
						}
						// Fallback to old context field
						const context = parsed.qdrant_data?.context;
						console.log('✅ Parsed Python dict qdrant_data context:', context);
						return context || null;
					} catch (parseError) {
						console.warn('❌ Failed to parse Python dict format for citations:', parseError);
						return null;
					}
				}
				
				return null;
			} else if (message.content && typeof message.content === 'object') {
				// Handle already parsed object (from WebSocket)
				console.log('✅ Object content for citations:', message.content);
				
				// Handle nested structure
				if (message.content.content && typeof message.content.content === 'object' && message.content.content.qdrant_data) {
					// Check for new citations array first
					if (message.content.content.qdrant_data.citations && Array.isArray(message.content.content.qdrant_data.citations)) {
						console.log('✅ Found nested object qdrant_data citations array:', message.content.content.qdrant_data.citations);
						return message.content.content.qdrant_data.citations;
					}
					// Fallback to old context field
					const context = message.content.content.qdrant_data?.context;
					console.log('✅ Found nested object qdrant_data context:', context);
					return context || null;
				}
				
				// Handle direct structure
				if (message.content.qdrant_data) {
					// Check for new citations array first
					if (message.content.qdrant_data.citations && Array.isArray(message.content.qdrant_data.citations)) {
						console.log('✅ Found direct object qdrant_data citations array:', message.content.qdrant_data.citations);
						return message.content.qdrant_data.citations;
					}
					// Fallback to old context field
					const context = message.content.qdrant_data?.context;
					console.log('✅ Found direct object qdrant_data context:', context);
					return context || null;
				}
				
				return null;
			}
			
			console.log('❌ No citations found');
			return null;
		} catch (error) {
			console.warn('⚠️ Error processing citations:', error);
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

	// Auto-scroll to bottom when messages change
	function scrollToBottom() {
		if (messagesContainer) {
			setTimeout(() => {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}, 100);
		}
	}

	function resizeTextarea(textareaEl: HTMLTextAreaElement) {
		textareaEl.style.height = 'auto';
		const scrollHeight = textareaEl.scrollHeight;
		const minHeight = 30;
		const maxHeight = 320;

		if (scrollHeight <= maxHeight) {
			textareaEl.style.height = Math.max(scrollHeight, minHeight) + 'px';
			textareaEl.style.overflowY = 'hidden';
		} else {
			textareaEl.style.height = maxHeight + 'px';
			textareaEl.style.overflowY = 'auto';
		}
	}

	function insertAtCursor(text: string, textareaEl?: HTMLTextAreaElement) {
		const el = textareaEl ?? textarea;
		if (!el) return;

		const start = el.selectionStart ?? el.value.length;
		const end = el.selectionEnd ?? start;
		inputValue = inputValue.slice(0, start) + text + inputValue.slice(end);

		requestAnimationFrame(() => {
			const pos = start + text.length;
			el.setSelectionRange(pos, pos);
			el.focus();
			resizeTextarea(el);
		});
	}

	function handleInput(event: Event) {
		resizeTextarea(event.target as HTMLTextAreaElement);
	}

	async function sendMessage() {
		if (isInputEmpty || sending || !wsConnected) return;

		const messageContent = inputValue.trim();
		
		// Check if we have either text content or files to send
		if (!messageContent && selectedFiles.length === 0) return;

		// Clear input immediately for smooth UX
		inputValue = '';
		sending = true;

		// Reset textarea height
		if (textarea) {
			textarea.style.height = '30px'; // Reset to minimum height to match main /c page
		}

		try {
			// If we have files, upload them with the message text
			if (selectedFiles.length > 0) {
				// Pass the message text to the file upload function
				// This will handle both files and text in a single API call
				const uploadSuccess = await uploadSelectedFiles(messageContent);
				
				if (!uploadSuccess) {
					throw new Error('File upload failed');
				}
				
				// The backend will handle sending the WebSocket message for file uploads
				// so we don't need to send a separate text message
			} else if (messageContent) {
				// Only text message, no files
				// Add user message immediately to UI (optimistic update)
				const userMessage: ChatMessage = {
					id: `temp-${Date.now()}`, // Temporary ID with prefix
					role: 'user',
					content: messageContent,
					created_at: new Date().toISOString(),
					chat_id: conversationId
				};
				messages = [...messages, userMessage];
				scrollToBottom();

				// Set loading immediately when user sends message
				isLoading = true;

				// Send via WebSocket with language preference
				if (chatWebSocket && chatWebSocket.isConnected()) {
					chatWebSocket.sendMessage(messageContent, conversationId, selectedLanguageId);
				} else {
					throw new Error('WebSocket not connected');
				}
			}

		} catch (err) {
			console.error('Message sending failed:', err);
			error = 'Unable to send message. Please check your connection.';
			
			// Remove the optimistic message on error
			messages = messages.filter(m => !m.id.toString().startsWith('temp-'));
			
			// Restore input value if it was text
			if (messageContent) {
				inputValue = messageContent;
			}
			
			// Reset loading state on error
			isLoading = false;
		} finally {
			sending = false;
			// Update isInputEmpty after everything is done
			isInputEmpty = inputValue.trim() === '' && selectedFiles.length === 0;
		}
	}

	function handleWebSocketMessage(data: any) {
		console.log('Received WebSocket message:', data);
		console.log('Current messages count:', messages.length);
		console.log('Current conversationId:', conversationId);
		
		try {
			switch (data.type) {
				case 'message':
					const message = data.message;
					
					console.log('Comparing chat_id:', message.chat_id, 'with conversationId:', conversationId);
					
					// Only add messages for this specific chat (handle both string and number comparison)
					if (message.chat_id.toString() === conversationId.toString()) {
						// Remove any temporary/optimistic messages
						messages = messages.filter(m => !m.id.toString().startsWith('temp-'));
						
						// Add the new message if it doesn't already exist
						const messageExists = messages.some(m => m.id.toString() === message.id.toString());
						console.log('Message exists check:', messageExists, 'for message ID:', message.id);
						
						if (!messageExists) {
							try {
								console.log('Adding new message to UI:', message);
								// Convert WebSocket message to our format
								const newMessage: ChatMessage = {
									id: message.id.toString(),
									role: message.role,
									content: message.role === 'assistant' ? {
										content: message.content,
										data_response: message.data_response,
										file_id: message.file_id,
										file_name: message.file_name,
										file_url: message.file_url
									} : message.content,
									created_at: message.timestamp,
									chat_id: message.chat_id.toString()
								};
								
								// Validate the message can be processed before adding
								getMessageContent(newMessage);
								
								messages = [...messages, newMessage];
								console.log('Message added! New messages count:', messages.length);
								console.log('Added message:', newMessage);
								scrollToBottom();
							} catch (error) {
								console.warn('Skipping invalid WebSocket message:', message.id, error);
							}
						}
					}
					break;
					
				case 'loading':
					isLoading = data.loading;
					if (!data.loading) {
						sending = false;
					}
					console.log('Loading state changed:', isLoading);
					break;
					
				case 'error':
					console.error('WebSocket error:', data.message);
					error = data.message || 'An error occurred while processing your request.';
					isLoading = false;
					sending = false;
					break;
					
				default:
					console.log('Unknown WebSocket message type:', data.type);
			}
		} catch (error) {
			console.error('Error handling WebSocket message:', error);
		}
	}

	function connectWebSocket() {
		// Don't create a new connection if one already exists and is connected
		if (chatWebSocket && chatWebSocket.isConnected()) {
			console.log('WebSocket already connected');
			return;
		}

		// Close existing connection if it exists
		if (chatWebSocket) {
			chatWebSocket.disconnect();
		}

		// Get auth token from store
		const token = get(authToken);
		if (!token) {
			console.error('No auth token available for WebSocket connection');
			error = 'Authentication required. Please log in again.';
			return;
		}

		try {
			chatWebSocket = createChatWebSocket(conversationId);
			
			// Set up event listeners
			chatWebSocket.on('connected', () => {
				wsConnected = true;
				connected = true;
				connectionStatus.set('connected');
				console.log('WebSocket connected successfully');
				error = ''; // Clear any previous errors
			});

			chatWebSocket.on('disconnected', () => {
				wsConnected = false;
				connected = false;
				connectionStatus.set('disconnected');
				console.log('WebSocket disconnected');
			});

			chatWebSocket.on('error', (error) => {
				console.error('WebSocket error:', error);
				connectionStatus.set('disconnected');
				wsConnected = false;
				connected = false;
			});

			chatWebSocket.onMessage((message) => {
				console.log('Received WebSocket message:', message);
				
				// Convert both to strings for comparison
				const messageChat = message.chat_id?.toString();
				const currentChat = conversationId?.toString();
				
				console.log('Message chat_id:', messageChat, 'Current chat:', currentChat);
				
				// Only add messages for this specific chat
				if (messageChat === currentChat) {
					console.log('Chat IDs match, processing message');
					
					// Remove any temporary/optimistic messages
					messages = messages.filter(m => !m.id.toString().startsWith('temp-'));
					
					// Add the new message if it doesn't already exist
					const messageExists = messages.some(m => m.id.toString() === message.id.toString());
					console.log('Message exists check:', messageExists);
					
					if (!messageExists) {
						try {
							console.log('Adding new message to UI:', message);
							
							// Parse the content if it's a JSON string
							let parsedContent;
							if (message.role === 'assistant' && typeof message.content === 'string') {
								try {
									// Try to parse the content as JSON
									const contentObj = JSON.parse(message.content);
									parsedContent = {
										content: contentObj.content || '',
										data_response: contentObj.data_response || null,
										file_id: message.file_id || null,
										file_name: message.file_name || null,
										file_url: message.file_url || null
									};
									console.log('Parsed assistant content:', parsedContent);
								} catch (parseError) {
									// If parsing fails, treat as plain text
									console.log('Could not parse content as JSON, using as plain text');
									parsedContent = {
										content: message.content,
										data_response: null,
										file_id: message.file_id || null,
										file_name: message.file_name || null,
										file_url: message.file_url || null
									};
								}
							} else if (message.role === 'assistant') {
								// For assistant messages that are already objects
								parsedContent = {
									content: message.content || '',
									data_response: message.data_response || null,
									file_id: message.file_id || null,
									file_name: message.file_name || null,
									file_url: message.file_url || null
								};
							} else {
								// For user messages or non-string content
								parsedContent = message.content;
							}
							
							// Convert WebSocket message to our format
							const newMessage: ChatMessage = {
								id: message.id.toString(),
								role: message.role,
								content: parsedContent,
								created_at: message.timestamp,
								chat_id: message.chat_id.toString(),
								file_id: message.file_id,
								file_name: message.file_name,
								file_url: message.file_url
							};
							
							console.log('Converted message:', newMessage);
							
							// Validate the message can be processed before adding
							const testContent = getMessageContent(newMessage);
							console.log('Message content test:', testContent);
							
							messages = [...messages, newMessage];
							console.log('Message added! New messages count:', messages.length);
							console.log('All messages:', messages);
							scrollToBottom();
						} catch (error) {
							console.warn('Skipping invalid WebSocket message:', message.id, error);
						}
					} else {
						console.log('Message already exists, skipping');
					}
				} else {
					console.log('Chat IDs do not match, ignoring message');
				}
			});

			chatWebSocket.onLoading((loadingState) => {
				console.log('Loading state changed:', loadingState);
				isLoading = loadingState;
			});

			chatWebSocket.onError((error) => {
				console.error('WebSocket connection error:', error);
			});

			// Connect to WebSocket
			connectionStatus.set('connecting');
			chatWebSocket.connect();
		} catch (err) {
			console.error('Error setting up WebSocket:', err);
			error = 'Failed to establish real-time connection';
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		} else if (event.key === 'Tab') {
			event.preventDefault();
			insertAtCursor('\t', event.target as HTMLTextAreaElement);
		}
	}

	// Edit message functions
	function startEditMessage(messageId: string, currentContent: string) {
		editingMessageId = messageId;
		editValue = currentContent;
		setTimeout(() => {
			if (editTextarea) {
				editTextarea.focus();
				editTextarea.style.height = 'auto';
				editTextarea.style.height = editTextarea.scrollHeight + 'px';
			}
		}, 50);
	}

	function cancelEdit() {
		editingMessageId = null;
		editValue = '';
	}

	function handleEditInput(event: Event) {
		const el = event.target as HTMLTextAreaElement;
		el.style.height = 'auto';
		const scrollHeight = el.scrollHeight;
		const minHeight = 40;
		const maxHeight = 200;

		if (scrollHeight <= maxHeight) {
			el.style.height = Math.max(scrollHeight, minHeight) + 'px';
			el.style.overflowY = 'hidden';
		} else {
			el.style.height = maxHeight + 'px';
			el.style.overflowY = 'auto';
		}
	}

	function handleEditKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			submitEditedMessage();
		} else if (event.key === 'Escape') {
			event.preventDefault();
			cancelEdit();
		} else if (event.key === 'Tab') {
			event.preventDefault();
			const el = event.target as HTMLTextAreaElement;
			const start = el.selectionStart ?? el.value.length;
			const end = el.selectionEnd ?? start;
			editValue = editValue.slice(0, start) + '\t' + editValue.slice(end);
			requestAnimationFrame(() => {
				const pos = start + 1;
				el.setSelectionRange(pos, pos);
				handleEditInput({ target: el } as Event);
			});
		}
	}

	async function submitEditedMessage() {
		if (!editingMessageId || editValue.trim() === '') return;

		const messageId = editingMessageId;
		if (messageId.startsWith('temp-')) {
			toast.error('Please wait for the message to send before editing.');
			return;
		}

		if (!chatWebSocket || !chatWebSocket.isConnected()) {
			toast.error('Connection lost. Please refresh and try again.');
			return;
		}

		const newContent = editValue.trim();
		const editIndex = messages.findIndex((msg) => msg.id.toString() === messageId);
		if (editIndex === -1) return;

		const removedMessageIds = messages.slice(editIndex + 1).map((msg) => msg.id.toString());
		const updatedMessage: ChatMessage = {
			...messages[editIndex],
			content: newContent
		};

		messages = [...messages.slice(0, editIndex), updatedMessage];
		responseFeedbackByMessageId = Object.fromEntries(
			Object.entries(responseFeedbackByMessageId).filter(
				([id]) => !removedMessageIds.includes(id)
			)
		);

		editingMessageId = null;
		editValue = '';
		isLoading = true;
		sending = true;
		scrollToBottom();

		try {
			chatWebSocket.sendEditMessage(
				newContent,
				messageId,
				conversationId,
				selectedLanguageId
			);
		} catch (err) {
			console.error('Failed to resend edited message:', err);
			isLoading = false;
			sending = false;
			toast.error('Failed to resend message. Please try again.');
		}
	}

	async function copyUserMessage(message: ChatMessage) {
		try {
			const rawText = getMessageContent(message);
			if (rawText && rawText !== '[object Object]' && rawText !== 'Error displaying message content') {
				await navigator.clipboard.writeText(rawText);
				toast.success('Copied to clipboard');
			} else {
				toast.error('No text content to copy');
			}
		} catch (err) {
			console.error('Failed to copy:', err);
			toast.error('Failed to copy to clipboard');
		}
	}

	async function copyMessage(content: string | MessageContent) {
		try {
			// Get the raw text response using the same logic as getMessageContent
			const rawText = getMessageContent({ 
				id: 'temp', 
				role: 'assistant', 
				content: content 
			} as ChatMessage);
			
			if (rawText && rawText !== '[object Object]' && rawText !== 'Error displaying message content') {
				await navigator.clipboard.writeText(rawText);
				toast.success('Copied to clipboard successfully!');
			} else {
				toast.error('No text content to copy');
			}
		} catch (err) {
			console.error('Failed to copy:', err);
			toast.error('Failed to copy to clipboard');
		}
	}

	// File upload functions
	function triggerFileUpload() {
		fileInput?.click();
	}

	function handleFileSelection(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;
		
		if (files && files.length > 0) {
			const fileArray = Array.from(files);
			
			// Add files to selected files (max 5 files)
			const totalFiles = selectedFiles.length + fileArray.length;
			if (totalFiles > 5) {
				toast.error('Maximum 5 files allowed');
				target.value = '';
				return;
			}
			
			// Validate file sizes (max 50MB each)
			const invalidFiles = fileArray.filter(file => file.size > 50 * 1024 * 1024);
			if (invalidFiles.length > 0) {
				toast.error('File size must be less than 50MB');
				target.value = '';
				return;
			}
			
			selectedFiles = [...selectedFiles, ...fileArray];
			
			// Don't upload automatically - wait for user to click send button
		}
		
		// Reset the input so same file can be selected again
		target.value = '';
	}

	async function uploadSelectedFiles(messageText = '') {
		if (selectedFiles.length === 0) return false;

		uploadingFiles = true;
		uploadProgress = 0;

		try {
			// Validate files before upload
			const validFiles = selectedFiles.filter(file => {
				if (!validateFileType(file)) {
					toast.error(`File type not supported: ${file.name}`);
					return false;
				}
				if (!validateFileSize(file, 50)) {
					toast.error(`File too large: ${file.name} (max 50MB)`);
					return false;
				}
				return true;
			});

			if (validFiles.length === 0) {
				uploadingFiles = false;
				selectedFiles = [];
				return false;
			}

			// Use the chat-specific upload API that properly handles chat_id
			// Pass the message text along with the files
			const response = await newChatApi.uploadFilesToChat(validFiles, messageText, parseInt(conversationId), null, selectedLanguageId);

			if (response.success) {
				toast.success(`Successfully uploaded ${validFiles.length} file(s)`);
				
				// Clear selected files after successful upload
				selectedFiles = [];
				
				
				return true; // Indicate success
			} else {
				toast.error('Failed to upload files');
				return false; // Indicate failure
			}
		} catch (error) {
			console.error('File upload error:', error);
			toast.error('Failed to upload files');
			return false; // Indicate failure
		} finally {
			uploadingFiles = false;
			uploadProgress = 0;
		}
	}

	function removeSelectedFile(index: number) {
		selectedFiles = selectedFiles.filter((_, i) => i !== index);
	}

	function isRateableMessage(message: ChatMessage): boolean {
		if (message.role !== 'assistant') return false;
		const id = message.id?.toString() || '';
		if (!id || id.startsWith('temp-')) return false;
		return /^\d+$/.test(id);
	}

	function handleResponseRated(messageId: string, rating: ResponseFeedbackRating) {
		responseFeedbackByMessageId = {
			...responseFeedbackByMessageId,
			[messageId]: rating
		};
	}

	async function loadResponseFeedback() {
		if (!conversationId) return;

		try {
			const token = get(authToken);
			const items = await fetchChatResponseFeedback(conversationId, token);
			const next: Record<string, ResponseFeedbackRating> = {};

			for (const item of items) {
				next[String(item.message_id)] = item.rating;
			}

			responseFeedbackByMessageId = next;
		} catch (err) {
			console.warn('Could not load response feedback:', err);
		}
	}

	async function loadChatHistory() {
		try {
			const response = await getChatMessages(parseInt(conversationId));
			
			// The Django API returns the messages array directly
			const chatMessages = Array.isArray(response) ? response : response.messages || [];
			
			// Fetch knowledge base name from chat list
			try {
				const chats = await newChatApi.getChats();
				const currentChat = chats.find((chat: any) => chat.id === parseInt(conversationId));
				
				if (currentChat && currentChat.knowledge_base) {
					
					// Fetch knowledge base details
					const kb = await getKnowledgeBase(currentChat.knowledge_base);
					knowledgeBaseName = kb.name;
				} else {
				}
			} catch (kbError) {
				console.error('Error fetching knowledge base info:', kbError);
			}
			
			// Process API messages to properly handle content structure
			const processedMessages = (chatMessages || []).map((apiMessage: any) => {
					
					// For user messages, use as-is
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
					
					// For assistant messages, parse the JSON content properly
					if (apiMessage.role === 'assistant') {
						try {
							let parsedContent;
							
							// Check if content is already an object
							if (typeof apiMessage.content === 'object' && apiMessage.content !== null) {
								parsedContent = apiMessage.content;
							} else if (typeof apiMessage.content === 'string') {
								// Try to parse the content as JSON
								parsedContent = JSON.parse(apiMessage.content);
							} else {
								// Handle null or undefined content
								parsedContent = { content: null, data_response: null };
							}
							
							
							// Structure the message to have both content and data_response at the right level
							return {
								id: apiMessage.id.toString(),
								role: 'assistant',
								content: {
									content: parsedContent.content || '',
									data_response: parsedContent.data_response || null,
									qdrant_data: parsedContent.qdrant_data || null,
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
							// If parsing fails, treat as plain text content
							return {
								id: apiMessage.id.toString(),
								role: 'assistant',
								content: {
									content: apiMessage.content || '',
									data_response: null,
									qdrant_data: null,
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
					
					// Fallback for any other cases
					return {
						id: apiMessage.id.toString(),
						...apiMessage,
						timestamp: apiMessage.created_at || apiMessage.timestamp,
						chat_id: conversationId
					};
				});
				
				// Filter out any messages that might cause frontend errors
				const validMessages = processedMessages.filter(msg => {
					try {
						// Test if we can safely process the message
						getMessageContent(msg);
						return true;
					} catch (error) {
						console.warn('Filtering out invalid message:', msg.id, error);
						return false;
					}
				});
				
				messages = validMessages;
				await loadResponseFeedback();
		} catch (err) {
			console.error('Error loading chat history:', err);
			// Don't show error for 404 - might be a new chat
			if (!err.message?.includes('404') && !err.message?.includes('No Chat matches')) {
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
			if (conversationId) {
				loadChatHistory().finally(() => {
					loading = false;
					scrollToBottom();
				});
				connectWebSocket();
			} else {
				error = 'Invalid chat ID';
				loading = false;
			}
		}
	});

	// Cleanup on destroy
	onDestroy(() => {
		if (chatWebSocket) {
			chatWebSocket.disconnect();
		}
	});

	// Voice recording functions
	async function startVoiceRecording() {
		recordingLoading = true;
		try {
			// Request microphone permission
			let stream = await navigator.mediaDevices
				.getUserMedia({ audio: true })
				.catch(function (err) {
					toast.error(`Permission denied when accessing microphone: ${err}`);
					recordingLoading = false;
					return null;
				});

			if (stream) {
				// Permission granted, start recording
				recording = true;
				// Keep recordingLoading true until recording actually starts
				const tracks = stream.getTracks();
				tracks.forEach((track) => track.stop());
			}
			
			if (!stream) {
				recordingLoading = false;
			}
			
			stream = null;
		} catch {
			toast.error('Permission denied when accessing microphone');
			recordingLoading = false;
		}
	}

	function onVoiceRecordingStarted() {
		recordingLoading = false;
	}

	function onVoiceRecordingCancel() {
		recording = false;
		recordingLoading = false;
	}

	function onVoiceRecordingConfirm(data: any) {
		const { text } = data.detail;
		recording = false;
		recordingLoading = false;
		insertAtCursor(text);
	}

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;
		
		if (!files || files.length === 0) return;
		
		try {
			uploadingFiles = true;
			uploadProgress = 0;

			// Validate files
			for (const file of Array.from(files)) {
				if (!validateFileType(file)) {
					throw new Error(`Invalid file type: ${file.type}`);
				}
				if (!validateFileSize(file)) {
					throw new Error(`File too large: ${file.name}`);
				}
			}

			// Add files to selection
			selectedFiles = [...selectedFiles, ...Array.from(files)];
			
			// Update empty state
			isInputEmpty = inputValue.trim() === '' && selectedFiles.length === 0;
			
		} catch (error) {
			console.error('File upload error:', error);
			toast.error(error.message || 'Failed to upload file');
		} finally {
			uploadingFiles = false;
			if (target) {
				target.value = '';
			}
		}
	}

	// Reactive statements
	$: if ($page.params.id && browser) {
		const newId = $page.params.id;
		if (newId !== conversationId && newId) {
			conversationId = newId;
			loading = true;
			error = '';
			
			// Load languages if not already loaded
			if (languages.length === 0) {
				getLanguages().then(langs => {
					languages = langs;
					if (langs.length > 0 && !selectedLanguageId) {
						selectedLanguageId = langs[0].id;  // Default to first language
					}
				}).catch(error => {
					console.error('Error loading languages:', error);
				});
			}
			
			loadChatHistory().finally(() => {
				loading = false;
				scrollToBottom();
			});
			connectWebSocket();
		}
	}

	// Auto-scroll when messages change
	$: if (messages.length > 0) {
		setTimeout(scrollToBottom, 100);
	}

	// Update isInputEmpty reactively - allow send when text or files are present
	$: isInputEmpty = inputValue.trim() === '' && selectedFiles.length === 0;

	function showDisclaimer() {
		showDisclaimerModal = true;
	}
</script>

<svelte:head>
	<title>Chat {conversationId || 'Loading...'} - MOSPI</title>
</svelte:head>

<style>
	/* Custom styles for OpenWebUI-like interface */
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

	:global(.group:hover .invisible) {
		visibility: visible;
	}

	.assistant-message-profile-image {
		width: 2rem;
		height: 2rem;
	}

	/* Ensure proper height and scrolling for the main chat container */
	:global(.chat-container) {
		height: 100%;
		max-height: 100%;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	:global(.messages-container) {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		min-height: 0; /* Important for flex child scrolling */
		max-height: 100%;
	}

	:global(.input-container) {
		flex-shrink: 0;
		max-height: 200px; /* Limit input area height */
		overflow: visible;
	}

	/* Input area specific styling */
	:global(.input-form-container) {
		max-height: 150px; /* Limit form height within input container */
	}

	:global(.input-textarea-container) {
		max-height: 100px; /* Limit textarea container height */
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

	/* Dark mode support */
	:global(.dark .bg-gray-850) {
		background-color: rgb(31 41 55);
	}

	:global(.dark .bg-gray-900) {
		background-color: rgb(17 24 39);
	}

	/* Hover effects */
	:global(.hover\:bg-black\/5:hover) {
		background-color: rgba(0, 0, 0, 0.05);
	}

	:global(.dark .dark\:hover\:bg-white\/5:hover) {
		background-color: rgba(255, 255, 255, 0.05);
	}

	/* Input styling */
	:global(.scrollbar-hidden) {
		scrollbar-width: none;
		-ms-overflow-style: none;
	}

	:global(.scrollbar-hidden::-webkit-scrollbar) {
		display: none;
	}

	:global(.outline-hidden) {
		outline: none;
	}

	:global(.outline-hidden:focus) {
		outline: none;
		box-shadow: none;
	}

	:global(.input-prose) {
		word-wrap: break-word;
		overflow-wrap: break-word;
	}

	/* Edit mode styling */
	.edit-textarea {
		font-family: system-ui, sans-serif;
		line-height: 1.5;
	}

	.edit-textarea:focus {
		outline: none;
		box-shadow: none;
	}

	:global(.user-message-action-btn) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.375rem;
		border-radius: 0.5rem;
		transition: background-color 0.15s ease, color 0.15s ease;
	}

	:global(.user-message-action-btn:hover) {
		background: rgba(0, 0, 0, 0.05);
		color: #111827;
	}

	:global(.dark .user-message-action-btn:hover) {
		background: rgba(255, 255, 255, 0.08);
		color: #fff;
	}

	/* Background effects */
	:global(.bg-white\/90) {
		background-color: rgba(255, 255, 255, 0.9);
	}

	:global(.dark .bg-gray-400\/5) {
		background-color: rgba(156, 163, 175, 0.05);
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

	/* Additional styles for improved layout */
	/* Primary color definition */
	:global(.bg-primary) {
		background-color: #16306b; /* MOSPI primary color */
	}
	
	:global(.hover\:bg-primary\/90:hover) {
		background-color: rgba(22, 48, 107, 0.9); /* MOSPI primary color with 90% opacity */
	}
	
	/* Ensure textarea doesn't interfere with button positioning */
	textarea {
		transition: height 0.2s ease-in-out;
	}
	
	/* Prevent layout shift on button hover */
	button {
		transition: all 0.2s ease-in-out;
	}
	
	/* Ensure input container maintains proper spacing */
	.input-container {
		min-height: fit-content;
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		z-index: 10;
	}
	
	@media (min-width: 768px) {
		.input-container {
			position: sticky;
			left: auto;
			right: auto;
		}
	}

	/* Fix file positioning - make input stay at bottom and files appear above */
	.input-form-container {
		display: flex;
		flex-direction: column-reverse; /* Reverse order so files appear above input */
	}
	
	/* Responsive adjustments */
	@media (max-width: 640px) {
		.input-container {
			padding-left: 1rem;
			padding-right: 1rem;
		}
		
		/* Add padding to messages container to prevent overlap with fixed input */
		.messages-container {
			padding-bottom: 200px !important;
		}
	}
</style>

<div class="h-full flex flex-col bg-white dark:bg-gray-900 chat-container max-h-full overflow-hidden">

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
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto overflow-x-hidden px-4 pt-4 pb-4 messages-container min-h-0">

				
				{#if messages.length === 0}
					<div class="text-center py-12">
						<div class="text-gray-400 dark:text-gray-600 mb-4">
							<svg class="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
							</svg>
						</div>
						<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Continue your conversation</h3>
						<p class="text-gray-500 dark:text-gray-400">Ask me anything about data analysis, statistics, or documents.</p>
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
												{#if editingMessageId === message.id.toString()}
													<!-- Edit Mode -->
													<div class="rounded-3xl max-w-[90%] px-5 py-3 bg-gray-50 dark:bg-gray-850 rounded-tr-lg w-full">
														<div class="w-full">
															<textarea
																bind:this={editTextarea}
																bind:value={editValue}
																on:input={handleEditInput}
																on:keydown={handleEditKeyDown}
																class="w-full resize-none text-gray-800 dark:text-gray-100 bg-transparent border-none outline-none font-normal min-h-[40px] max-h-48 scrollbar-hidden edit-textarea"
																style="font-family: system-ui, sans-serif; overflow-y: hidden;"
																placeholder="Edit your message..."
															></textarea>
														</div>
														<div class="flex justify-end gap-2 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
															<button 
																on:click={cancelEdit}
																class="px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
																title="Cancel (Esc)"
															>
																Cancel
															</button>
															<button 
																on:click={submitEditedMessage}
																class="px-3 py-1.5 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-md transition-colors"
																title="Send edited message (Enter)"
															>
																Send
															</button>
														</div>
													</div>
												{:else}
													<!-- Display Mode -->
													<div class="rounded-3xl max-w-[90%] px-5 py-3 bg-gray-50 dark:bg-gray-850 rounded-tr-lg">
														<p dir="auto" class="whitespace-pre-wrap text-gray-800 dark:text-gray-100">{getMessageContent(message)}</p>
													</div>
												{/if}
											</div>
											
											<!-- Files Display moved outside message bubble -->
											{#if getFiles(message).length > 0}
												{@const files = getFiles(message)}
												{@debug files}
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
											
											<div class="flex justify-end text-gray-600 dark:text-gray-400 mt-1 pr-2">
												{#if editingMessageId !== message.id.toString() && !message.id.toString().startsWith('temp-')}
													<div class="flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
														<button
															type="button"
															aria-label="Copy message"
															title="Copy"
															class="user-message-action-btn"
															on:click={() => copyUserMessage(message)}
														>
															<Copy class="h-4 w-4" />
														</button>
														<button
															type="button"
															aria-label="Edit message"
															title="Edit"
															class="user-message-action-btn"
															on:click={() =>
																startEditMessage(
																	message.id.toString(),
																	getMessageContent(message)
																)}
														>
															<Edit class="h-4 w-4" />
														</button>
													</div>
												{/if}
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					{:else}
						<!-- Assistant Message -->
						<div class="flex flex-col justify-between px-1 sm:px-4 mb-6 w-full max-w-5xl mx-auto rounded-lg group">
							<div class="flex w-full message-{message.id}" id="message-{message.id}">
								<div class="shrink-0 ltr:mr-1.5 sm:ltr:mr-3 rtl:ml-1.5 sm:rtl:ml-3 mt-1">
									<img crossorigin="anonymous" src="/apple-touch-icon.png" class="size-5 sm:size-8 assistant-message-profile-image object-cover rounded-full" alt="profile" draggable="false">
								</div>
								<div class="flex-auto w-0 pl-0 sm:pl-1 relative">
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

												<!-- Citations Section (New Format) -->
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
									
									<!-- Response feedback + copy -->
									<ResponseFeedbackBar
										messageId={message.id}
										rating={responseFeedbackByMessageId[message.id] ?? null}
										disabled={!isRateableMessage(message)}
										onCopy={() => copyMessage(message.content)}
										onRated={handleResponseRated}
									/>
								</div>
							</div>
						</div>
					{/if}
				{/each}

				{#if isLoading}
					<div class="flex flex-col justify-between px-1 sm:px-0 mb-6 w-full max-w-5xl mx-auto rounded-lg">
						<div class="flex w-full px-0 sm:px-0">
							<div class="shrink-0 ltr:mr-1.5 sm:ltr:mr-3 rtl:ml-1.5 sm:rtl:ml-3 mt-1">
								<img crossorigin="anonymous" src="/apple-touch-icon.png" class="size-5 sm:size-8 assistant-message-profile-image object-cover rounded-full" alt="profile" draggable="false">
							</div>
							<div class="flex-auto w-0 pl-0 sm:pl-1 relative">
								<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
									<div class="flex items-center space-x-2">
										<div class="flex space-x-1">
											<div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
											<div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
											<div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
		</div>

		<!-- Input Area - Fixed at bottom -->
		<div class="flex-shrink-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 input-container">
			<div class="w-full max-w-4xl mx-auto px-4 py-3">
				<!-- Hidden file input -->
				<input 
					type="file" 
					bind:this={fileInput}
					on:change={handleFileUpload}
					multiple
					accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.csv,.html,.md"
					style="display: none;"
				>
				
				{#if recording}
					<VoiceRecording
						bind:recording
						transcribe={true}
						on:started={onVoiceRecordingStarted}
						on:cancel={onVoiceRecordingCancel}
						on:confirm={onVoiceRecordingConfirm}
					/>
				{:else}
					<form class="w-full flex flex-col gap-1.5 input-form-container" on:submit|preventDefault={sendMessage}>
					<!-- Main Input Container with exact styling from main /c page -->
					<div class="flex-1 flex flex-col relative w-full shadow-lg rounded-3xl transition px-1 bg-white/90 dark:bg-gray-400/5 dark:text-gray-100" dir="auto">
								<!-- Selected Files Display - Inside container (placed after input due to column-reverse) -->
						{#if selectedFiles.length > 0}
							<div class="px-3 pt-2.5 pb-1">
								<div class="flex flex-wrap gap-1.5">
									{#each selectedFiles as file, index}
										<FileChip 
											{file} 
											onRemove={() => removeSelectedFile(index)} 
										/>
									{/each}
								</div>
							</div>
						{/if}
						<div class="px-2.5 relative">
							<div class="scrollbar-hidden rtl:text-right ltr:text-left bg-transparent dark:text-gray-100 outline-hidden w-full pt-2.5 pb-[45px] px-1 resize-none h-fit max-h-80 overflow-auto" id="chat-input-container">
								<div class="relative w-full min-w-full h-full min-h-fit input-prose">
									<textarea
										placeholder="Continue the conversation..."
										class="w-full resize-none text-base text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 bg-transparent border-none outline-none font-normal min-h-[30px] max-h-80 pr-16 pt-3 scrollbar-hidden"
										style="font-family: system-ui, sans-serif; overflow-y: hidden;"
										bind:value={inputValue}
										on:input={handleInput}
										on:keydown={handleKeyDown}
										bind:this={textarea}
										disabled={sending}
									></textarea>
								</div>
							</div>
							
							<!-- Buttons positioned absolutely at bottom of input container -->
							<div class="absolute bottom-1 left-0 right-0 flex justify-between px-3">
								<div class="flex items-center gap-2">
			<!-- Report/Manual Name Display -->
			{#if knowledgeBaseName}
				<div class="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full py-1.5 px-3 text-xs font-medium border border-blue-200 dark:border-blue-800">
					<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
					</svg>
					<span>{knowledgeBaseName}</span>
				</div>
			{/if}									<!-- Language Selector -->
									<div class="relative">
										<select 
											bind:value={selectedLanguageId}
											tabindex="-1"
											class="flex items-center gap-1.5 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full py-1.5 pl-8 pr-3 outline-none focus:outline-none transition-all border border-gray-200 dark:border-gray-700 text-xs font-medium cursor-pointer appearance-none"
										>
											{#each languages as lang}
												<option value={lang.id}>{lang.name}</option>
											{/each}
										</select>
										<img src="/language.svg" alt="language" class="absolute left-2.5 top-1/2 -translate-y-1/2 size-6 pointer-events-none" />
									</div>
								</div>
								
								<div class="flex space-x-1 items-center">
									<button 
										id="voice-input-button" 
										class="text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5" 
										type="button" 
										aria-label="Voice Input"
										tabindex="-1"
										on:click={startVoiceRecording}
										disabled={recordingLoading || sending || !wsConnected}
									>
										<Mic class="w-5 h-5 translate-y-[0.5px]" />
									</button>
									
									<button 
										id="send-message-button" 
										class="text-white transition rounded-full p-1.5 {isInputEmpty || sending || !wsConnected ? 'bg-gray-200 dark:bg-gray-700 cursor-not-allowed' : 'bg-primary hover:bg-primary/90'}" 
										type="submit" 
										tabindex="-1"
										disabled={isInputEmpty || sending || !wsConnected}
									>
										{#if sending}
											<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
										{:else}
											<ArrowUp class="size-5" />
										{/if}
									</button>
								</div>
							</div>
						</div>
					</div>
				</form>
			{/if}
			
			<!-- Disclaimer -->
			<div class="mt-2 text-center">
				<p class="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
					The MoSPI StatsDoc AI Assistant is an AI system. This AI chatbot is designed to answer queries related to MoSPI documents that are selected while asking queries. For more accurate and relevant responses, users are encouraged to provide prompts with clarity and context. There may be different responses for same query as they are generated by Large Language Model that are probabilistic in nature. By accessing this service, users agree to the following 
					<button class="text-blue-600 dark:text-blue-400 hover:underline underline" on:click={() => showDisclaimer()}>Disclaimer</button>.
				</p>
			</div>
		</div>

		<!-- Disclaimer Modal -->
		{#if showDisclaimerModal}
			<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" on:click={() => showDisclaimerModal = false} on:keydown={(e) => { if (e.key === 'Escape') showDisclaimerModal = false; }}>
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl mx-4 max-h-[80vh] overflow-y-auto" on:click|stopPropagation on:keydown|stopPropagation>
					<div class="flex justify-between items-center mb-4">
						<h2 class="text-xl font-bold text-gray-900 dark:text-white">Disclaimer</h2>
						<button class="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white" aria-label="Close disclaimer" on:click={() => showDisclaimerModal = false}>
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
							</svg>
						</button>
					</div>
					<div class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
						<p class="mb-4">
							The "MoSPI StatsDoc AI Assistant" is an Initiative of the Ministry of Statistics and Programme Implementation (MoSPI). The content and responses generated by this tool are intended solely to facilitate document search with the help of AI Enabled Intelligent Search.
						</p>
						<p class="mb-4">
							This chatbot is powered by third-party Large Language Models (LLMs) and fine-tuned to improve the user experience by searching through documents semantically, and despite the implementation of safeguards and guardrails, the responses generated should not be taken as evidence or treated as official communication. MoSPI shall not be liable for any loss, damage, or consequence arising from the use of this AI system.
						</p>
						<p class="mb-4">
							MoSPI makes no warranties regarding the accuracy, completeness, or reliability of the information provided. The Ministry and its staff, individually and collectively, shall not be liable for any financial or other consequences whatsoever arising from the use of this application, including but not limited to inappropriate, improper, or fraudulent use. Users are strongly cautioned to verify the accuracy and completeness of any information before relying on it for decision-making or any other purpose.
						</p>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}
</div>