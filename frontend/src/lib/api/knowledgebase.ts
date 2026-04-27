import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface KnowledgeBase {
	id: number;
	name: string;
	description: string;
	created_at: string;
	updated_at: string;
	files_count: number;
}

export interface UploadedFile {
	id: number;
	file_name: string;
	uploaded_at: string;
	status: string;
	file_url: string;
	knowledge_base?: number;
	other_info?: {
		error?: string;
		message?: string;
		json_size_mb?: number;
		max_size_mb?: number;
		technical_error?: string;
	};
}

export interface CreateKnowledgeBaseData {
	name: string;
	description: string;
}

/**
 * Get authentication headers
 */
function getAuthHeaders(): HeadersInit {
	const token = localStorage.getItem('access_token') || localStorage.getItem('token');
	return {
		'Content-Type': 'application/json',
		...(token ? { 'Authorization': `Bearer ${token}` } : {})
	};
}

/**
 * Get authentication headers for multipart form data
 */
function getAuthHeadersMultipart(): HeadersInit {
	const token = localStorage.getItem('access_token') || localStorage.getItem('token');
	return {
		...(token ? { 'Authorization': `Bearer ${token}` } : {})
	};
}

/**
 * Get all knowledge bases
 */
export async function getKnowledgeBases(): Promise<KnowledgeBase[]> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/knowledge-bases/`, {
			method: 'GET',
			headers: getAuthHeaders()
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch knowledge bases: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('Error fetching knowledge bases:', error);
		throw error;
	}
}

/**
 * Get a single knowledge base by ID
 */
export async function getKnowledgeBase(id: number): Promise<KnowledgeBase> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/knowledge-bases/${id}/`, {
			method: 'GET',
			headers: getAuthHeaders()
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch knowledge base: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('Error fetching knowledge base:', error);
		throw error;
	}
}

/**
 * Create a new knowledge base
 */
export async function createKnowledgeBase(data: CreateKnowledgeBaseData): Promise<KnowledgeBase> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/knowledge-bases/`, {
			method: 'POST',
			headers: getAuthHeaders(),
			body: JSON.stringify(data)
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.detail || `Failed to create knowledge base: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('Error creating knowledge base:', error);
		throw error;
	}
}

/**
 * Update a knowledge base
 */
export async function updateKnowledgeBase(id: number, data: Partial<CreateKnowledgeBaseData>): Promise<KnowledgeBase> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/knowledge-bases/${id}/`, {
			method: 'PATCH',
			headers: getAuthHeaders(),
			body: JSON.stringify(data)
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.detail || `Failed to update knowledge base: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('Error updating knowledge base:', error);
		throw error;
	}
}

/**
 * Delete a knowledge base
 */
export async function deleteKnowledgeBase(id: number): Promise<void> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/knowledge-bases/${id}/`, {
			method: 'DELETE',
			headers: getAuthHeaders()
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `Failed to delete knowledge base: ${response.statusText}`);
		}
	} catch (error) {
		console.error('Error deleting knowledge base:', error);
		throw error;
	}
}

/**
 * Get files in a knowledge base
 */
export async function getKnowledgeBaseFiles(knowledgeBaseId: number): Promise<UploadedFile[]> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/upload/?knowledge_base=${knowledgeBaseId}`, {
			method: 'GET',
			headers: getAuthHeaders()
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch knowledge base files: ${response.statusText}`);
		}

		const data = await response.json();
		// Filter files that belong to this knowledge base
		return data.filter((file: UploadedFile) => file.knowledge_base === knowledgeBaseId);
	} catch (error) {
		console.error('Error fetching knowledge base files:', error);
		throw error;
	}
}

/**
 * Upload files to a knowledge base
 */
export async function uploadFilesToKnowledgeBase(knowledgeBaseId: number, files: File[]): Promise<UploadedFile[]> {
	try {
		const formData = new FormData();
		
		// Add each file to the form data
		files.forEach(file => {
			formData.append('file', file);
		});
		
		// Add knowledge base ID
		formData.append('knowledge_base_id', knowledgeBaseId.toString());

		const response = await fetch(`${WEBUI_API_BASE_URL}/upload/`, {
			method: 'POST',
			headers: getAuthHeadersMultipart(),
			body: formData
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `Failed to upload files: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('Error uploading files to knowledge base:', error);
		throw error;
	}
}

/**
 * Delete a file from knowledge base (and its Qdrant vectors)
 */
export async function deleteKnowledgeBaseFile(fileId: number): Promise<void> {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/files/${fileId}/delete/`, {
			method: 'DELETE',
			headers: getAuthHeaders()
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `Failed to delete file: ${response.statusText}`);
		}
	} catch (error) {
		console.error('Error deleting file from knowledge base:', error);
		throw error;
	}
}
