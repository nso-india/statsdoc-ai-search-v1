import { toast } from 'svelte-sonner';
import { WEBUI_API_BASE_URL } from '$lib/constants';

// Helper function for API requests
async function apiRequest(endpoint: string, options: RequestInit = {}) {
	const token = localStorage.getItem('access_token');
	const headers = {
		'Content-Type': 'application/json',
		...(token && { 'Authorization': `Bearer ${token}` }),
		...options.headers
	};

	const response = await fetch(`${WEBUI_API_BASE_URL}${endpoint}`, {
		...options,
		headers
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Request failed' }));
		
		// Handle Django ValidationError with non_field_errors
		if (error.non_field_errors && Array.isArray(error.non_field_errors)) {
			const errorMessage = error.non_field_errors[0];
			
			// Show all validation errors to user
			toast.error(errorMessage);
			
			throw new Error(errorMessage);
		}
		
		// Handle other error formats
		const errorMessage = error.detail || error.message || 'API request failed';
		throw new Error(errorMessage);
	}

	// Handle 204 No Content responses (like delete operations)
	if (response.status === 204) {
		return null;
	}

	return response.json();
}

// New Chat API for WebSocket-based backend
export const newChatApi = {
	// Get all chats for the current user
	async getChats() {
		try {
			const chats = await apiRequest('/chat/chats/', {
				method: 'GET'
			});
			
			// Filter out any chats that might cause frontend errors
			return (chats || []).filter((chat: any) => {
				try {
					// Basic validation of chat structure
					return chat && typeof chat.id === 'number';
				} catch (error) {
					console.warn('Filtering out invalid chat:', chat?.id, error);
					return false;
				}
			});
		} catch (error) {
			console.error('Error fetching chats:', error);
			return [];
		}
	},

	// Create a new chat
	async createChat(title: string) {
		return apiRequest('/chat/chats/', {
			method: 'POST',
			body: JSON.stringify({ title })
		});
	},

	// Get messages for a specific chat
	async getMessages(chatId: number) {
		try {
			const messages = await apiRequest(`/chat/chats/${chatId}/messages/`, {
				method: 'GET'
			});
			
			// Filter out any messages that might cause frontend errors
			return (messages || []).filter((message: any) => {
				try {
					// Basic validation - ensure we have required fields
					if (!message || typeof message.id === 'undefined' || !message.role) {
						return false;
					}
					
					// Try to process content safely
					if (typeof message.content === 'string') {
						return true;
					} else if (message.content && typeof message.content === 'object') {
						return true;
					}
					
					return false;
				} catch (error) {
					console.warn('Filtering out invalid message:', message?.id, error);
					return false;
				}
			});
		} catch (error) {
			console.error('Error fetching messages:', error);
			// Return empty array instead of throwing to prevent app crash
			return [];
		}
	},

	// Check file processing status (for specific file IDs in a chat)
	async checkFileStatus(fileIds: number[]) {
		try {
			// Get all files and filter by the provided IDs
			const response = await apiRequest('/upload/', {
				method: 'GET'
			});
			
			if (Array.isArray(response)) {
				// Filter files by the provided IDs and return their status
				return response.filter(file => fileIds.includes(file.id)).map(file => ({
					id: file.id,
					status: file.status,
					file_name: file.file_name
				}));
			}
			return [];
		} catch (error) {
			console.error('Error checking file status:', error);
			return [];
		}
	},

	// Check chat status (for /c/{id} page on load/refresh)
	async getChatStatus(chatId: number) {
		try {
			// Check if there are any files still processing for this chat
			const unprocessedFiles = await this.checkChatFileStatus(chatId);
			
			if (unprocessedFiles.length > 0) {
				// Separate files by status
				const failedFiles = unprocessedFiles.filter(file => file.status === 'FAILED');
				const processingFiles = unprocessedFiles.filter(file => 
					file.status === 'PENDING' || file.status === 'IN_PROGRESS'
				);
				
				if (failedFiles.length > 0 && processingFiles.length === 0) {
					// All files failed, no processing files left - chat is ready
					return {
						status: 'failed',
						processingFiles: [], // Important: empty array so polling stops
						failedFiles: failedFiles
					};
				} else if (processingFiles.length > 0) {
					// Still have files processing
					return {
						status: 'processing',
						processingFiles: processingFiles, // Only actively processing files
						failedFiles: failedFiles
					};
				} else {
					// No processing or failed files
					return {
						status: 'completed',
						processingFiles: []
					};
				}
			} else {
				return {
					status: 'completed',
					processingFiles: []
				};
			}
		} catch (error) {
			console.error('Error checking chat status:', error);
			return {
				status: 'completed',
				processingFiles: []
			};
		}
	},

	// Check unprocessed files for a specific chat (for page refresh recovery)
	async checkChatFileStatus(chatId: number) {
		try {
			const response = await apiRequest(`/upload/?chat_id=${chatId}`, {
				method: 'GET'
			});
			
			
			if (Array.isArray(response)) {
				// Double check that files belong to this chat_id
				const filteredFiles = response.filter(file => 
					file.chat_id === chatId && (
						file.status === 'PENDING' || 
						file.status === 'IN_PROGRESS' || 
						file.status === 'FAILED'
					)
				).map(file => ({
					id: file.id,
					status: file.status,
					file_name: file.file_name
				}));
				
				return filteredFiles;
			}
			return [];
		} catch (error) {
			console.error('Error checking chat file status:', error);
			return [];
		}
	},

	// Delete a chat
	async deleteChat(chatId: number) {
		return apiRequest(`/chat/chats/${chatId}/delete/`, {
			method: 'DELETE'
		});
	},

	// Send message to existing chat (API-based, not WebSocket)
	async sendMessage(chatId: number, message: string) {
		try {
			const response = await apiRequest(`/chat/chats/${chatId}/message/`, {
				method: 'POST',
				body: JSON.stringify({
					message: message.trim()
				})
			});
			
			return response;
		} catch (error) {
			console.error('Error sending message to chat:', error);
			throw error;
		}
	},

	// Upload files to a chat
	async uploadFilesToChat(files: File[], prompt: string = '', chatId?: number | null, knowledgeBaseId?: number | null, languageId?: string | null) {
		try {
			const formData = new FormData();
			
			// Add all files
			files.forEach(file => {
				formData.append('file', file);
			});
			
			// Add chat_id as separate field if provided
			if (chatId) {
				formData.append('chat_id', chatId.toString());
			}
			
			// Add knowledge_base_id if provided
			if (knowledgeBaseId) {
				formData.append('knowledge_base_id', knowledgeBaseId.toString());
			}
			
			// Add prompt directly (not as other_info JSON)
			if (prompt.trim()) {
				formData.append('prompt', prompt.trim());
			}
			
			// Add language_id if provided
			if (languageId) {
				formData.append('language_id', languageId);
			}

			// Get token for auth header
			const token = localStorage.getItem('access_token');
			
			const response = await fetch(`${WEBUI_API_BASE_URL}/chat/chats/upload/`, {
				method: 'POST',
				headers: {
					...(token && { 'Authorization': `Bearer ${token}` })
					// Don't set Content-Type, let browser set it with boundary for FormData
				},
				body: formData
			});

			if (!response.ok) {
				const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
				throw new Error(error.detail || error.message || 'Upload failed');
			}

			const result = await response.json();
			
			// Handle the response from ChatFileUploadAPIView
			// Backend returns: {'message': 'File uploaded and processing started.', 'chat_id': chat.id}
			return {
				success: true,
				chat_id: result.chat_id,
				message: result.message || 'Files uploaded successfully',
				uploaded_files: [] // The backend doesn't return file IDs in this format
			};
		} catch (error) {
			console.error('Error uploading files to chat:', error);
			throw error;
		}
	},

	// Delete a file from a chat
	async deleteChatFile(chatId: number, fileId: number) {
		try {
			return await apiRequest(`/chat/chats/${chatId}/${fileId}/delete/`, {
				method: 'DELETE'
			});
		} catch (error) {
			console.error('Error deleting chat file:', error);
			throw error;
		}
	}
};

// WebSocket connection helper for new backend
export class NewChatWebSocket {
	private ws: WebSocket | null = null;
	private roomName: string;
	private onMessage: (data: any) => void;
	private onStatusChange: (status: 'connecting' | 'connected' | 'disconnected') => void;

	constructor(
		roomName: string,
		onMessage: (data: any) => void,
		onStatusChange: (status: 'connecting' | 'connected' | 'disconnected') => void
	) {
		this.roomName = roomName;
		this.onMessage = onMessage;
		this.onStatusChange = onStatusChange;
	}

	connect() {
		const token = localStorage.getItem('access_token');
		const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/${this.roomName}${token ? `/?token=${token}` : '/'}`;
		
		this.onStatusChange('connecting');
		this.ws = new WebSocket(wsUrl);

		this.ws.onopen = () => {
			this.onStatusChange('connected');
		};

		this.ws.onmessage = (event) => {
			const data = JSON.parse(event.data);
			this.onMessage(data);
		};

		this.ws.onclose = () => {
			this.onStatusChange('disconnected');
			// Auto-reconnect after 3 seconds
			setTimeout(() => this.connect(), 3000);
		};

		this.ws.onerror = (error) => {
			console.error('WebSocket error:', error);
			this.onStatusChange('disconnected');
		};
	}

	sendMessage(content: string, chatId?: number | null) {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify({
				message: content,
				chat_id: chatId
			}));
		}
	}

	disconnect() {
		if (this.ws) {
			this.ws.close();
		}
	}

	get isConnected() {
		return this.ws && this.ws.readyState === WebSocket.OPEN;
	}
}
