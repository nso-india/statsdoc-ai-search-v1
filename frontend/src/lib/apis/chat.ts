// Chat API for handling file uploads and chat creation
const REMOTE_BACKEND_HOST = import.meta.env.VITE_REMOTE_BACKEND_HOST || 'statsdoc.ai.mospi.gov.in';
const WEBUI_API_BASE_URL = typeof window !== 'undefined' 
	? `https://${REMOTE_BACKEND_HOST}/api`
	: `http://web:8000/api`;

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
		throw new Error(error.detail || error.message || 'API request failed');
	}

	return response.json();
}

// Helper function for file upload requests
async function fileUploadRequest(endpoint: string, formData: FormData) {
	const token = localStorage.getItem('access_token');
	const headers: Record<string, string> = {};
	
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}
	// Don't set Content-Type header for FormData - let browser set it with boundary

	const response = await fetch(`${WEBUI_API_BASE_URL}${endpoint}`, {
		method: 'POST',
		headers,
		body: formData
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Request failed' }));
		throw new Error(error.detail || error.message || 'File upload failed');
	}

	return response.json();
}

export const chatApi = {
		// Upload files and create/update chat
	async uploadFiles(files: File[], prompt: string = '', chatId?: number) {
		const formData = new FormData();
		
		// Add files
		files.forEach(file => {
			formData.append('file', file);
		});
		
		// Add prompt
		if (prompt) {
			formData.append('prompt', prompt);
		}
		
		// Add chat_id if provided
		if (chatId) {
			formData.append('chat_id', chatId.toString());
		}
		
		return fileUploadRequest('/upload/', formData);
	},

	// Get chat messages (already exists in newchat.ts but adding here for consistency)
	async getChatMessages(chatId: number) {
		console.log('Fetching chat messages for chat ID:', chatId);
		try {
			const response = await apiRequest(`/chat/chats/${chatId}/messages/`, {
				method: 'GET'
			});
			console.log('Chat messages response:', response);
			return response;
		} catch (error) {
			console.error('Error fetching chat messages:', error);
			throw error;
		}
	},

	// Get chat detail including knowledge base info
	async getChatDetail(chatId: number) {
		console.log('Fetching chat detail for chat ID:', chatId);
		try {
			const response = await apiRequest(`/chat/chats/${chatId}/`, {
				method: 'GET'
			});
			console.log('Chat detail response:', response);
			return response;
		} catch (error) {
			console.error('Error fetching chat detail:', error);
			throw error;
		}
	}
};

// Export individual functions for easier importing
export const getChatMessages = chatApi.getChatMessages;
export const getChatDetail = chatApi.getChatDetail;
