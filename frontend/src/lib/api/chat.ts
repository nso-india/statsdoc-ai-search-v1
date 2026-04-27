// Real API implementation for Django backend
import { authToken } from '$lib/stores';
import { get } from 'svelte/store';
import { WEBUI_API_BASE_URL, WEBSOCKET_BASE_URL } from '$lib/constants/app';
import { toast } from 'svelte-sonner';

export interface RAGMessage {
	id: string;
	sender_type: 'user' | 'assistant' | 'system';
	message_type: 'text' | 'query_result' | 'error' | 'thinking';
	content: string;
	query_data?: {
		sql_result?: any[];
		chart_data?: any;
		timestamp?: string;
	} | null;
	figure?: string | null; // JSON chart data for Plotly rendering
	sources?: Array<{
		title: string;
		page?: number;
	}> | null;
	metadata?: any;
	is_streaming: boolean;
	is_complete: boolean;
	created_at: string;
}

export interface RAGConversation {
	id: string;
	title?: string | null;
	auto_title?: string | null;
	created_at: string;
	updated_at: string;
	total_messages: number;
	messages?: RAGMessage[];
}

export interface ConversationListItem {
	id: string;
	title?: string | null;
	auto_title?: string | null;
	created_at: string;
	updated_at: string;
	last_message?: {
		content: string;
		sender_type: string;
		created_at: string;
	} | null;
	message_count: number;
	total_messages: number;
}

// Real ChatAPI implementation - OpenWebUI style
export class ChatAPI {
	private static conversationCache = new Map<string, RAGConversation>();
	private static activeRequests = new Map<string, Promise<any>>();
	
	private static getAuthHeaders() {
		const token = get(authToken) || localStorage.getItem('access_token');
		return {
			'Content-Type': 'application/json',
			...(token && { 'Authorization': `Bearer ${token}` })
		};
	}

	private static async apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const response = await fetch(`${WEBUI_API_BASE_URL}${endpoint}`, {
			headers: this.getAuthHeaders(),
			...options
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

		return response.json();
	}

	// Prevent duplicate API calls
	private static async dedupedRequest<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
		if (this.activeRequests.has(key)) {
			return this.activeRequests.get(key) as Promise<T>;
		}

		const request = requestFn().finally(() => {
			this.activeRequests.delete(key);
		});

		this.activeRequests.set(key, request);
		return request;
	}

	static async getConversations(): Promise<ConversationListItem[]> {
		try {
			const chats = await this.apiRequest<any[]>('/chat/chats/');
			// Transform backend response to match frontend interface
			return chats.map(chat => ({
				id: chat.id.toString(),
				title: chat.title,
				auto_title: null,
				created_at: chat.created_at,
				updated_at: chat.updated_at,
				last_message: chat.last_message ? {
					content: chat.last_message.content,
					sender_type: chat.last_message.role,
					created_at: chat.last_message.timestamp
				} : null,
				message_count: chat.message_count || 0,
				total_messages: chat.message_count || 0
			}));
		} catch (error) {
			console.error('Error fetching conversations:', error);
			return [];
		}
	}

	static async deleteConversation(conversationId: string): Promise<void> {
		try {
			await this.apiRequest(`/chat/chats/${conversationId}/delete/`, {
				method: 'DELETE'
			});
		} catch (error) {
			console.error('Error deleting conversation:', error);
			throw error;
		}
	}

	static async createNewChat(data: { title?: string; message: string }): Promise<{ id: string }> {
		try {
			const response = await this.apiRequest<any>('/chat/chats/', {
				method: 'POST',
				body: JSON.stringify({
					title: data.title || 'New Chat'
				})
			});
			return { id: response.id.toString() };
		} catch (error) {
			console.error('Error creating new chat:', error);
			throw error;
		}
	}
}

// Placeholder WebSocket Manager for compatibility
export class ChatWebSocketManager {
	constructor(conversationId: string, onMessage?: (data: any) => void) {
		// Placeholder implementation
	}
	
	connect() {
		// Placeholder implementation
	}
	
	disconnect() {
		// Placeholder implementation
	}
	
	sendMessage(message: string) {
		// Placeholder implementation
	}
}

export interface ChatWebSocketMessage {
	type: string;
	message: any;
}

export function getWebSocketManager(conversationId: string, onMessage?: (data: any) => void): ChatWebSocketManager {
	return new ChatWebSocketManager(conversationId, onMessage);
}

export function disconnectWebSocket() {
	// Placeholder implementation
}

// Re-export WebSocket manager from stores
// TODO: Implement websocket store
// export { 
// 	ChatWebSocketManager, 
// 	getWebSocketManager, 
// 	disconnectWebSocket,
// 	type ChatWebSocketMessage
// } from '$lib/stores/websocket';
