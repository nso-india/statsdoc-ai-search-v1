import { WEBUI_API_BASE_URL } from '$lib/constants';
import { get } from 'svelte/store';
import { authToken } from '$lib/stores';

// Types
export interface UploadedFile {
  id: number;
  file_name: string;
  original_name: string;
  file_size: number;
  file_type: string;
  upload_status: string;
  created_at: string;
  updated_at: string;
  docling_json?: any;
  other_info?: any;
  reviewed?: boolean;
}

export interface FileUploadResponse {
  success?: UploadedFile[];
  errors?: string[];
  message?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  docling_json?: any; // For backward compatibility with existing code
}

// Helper function to get auth headers
function getAuthHeaders() {
  const token = get(authToken);
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
  };
}

// File validation functions
export function validateFileType(file: File): boolean {
  // Allowed file extensions (matching backend)
  const allowedExtensions = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.json', '.xml', '.html', '.htm',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.zip', '.tar', '.gz'
  ];
  
  // Get file extension
  const fileName = file.name.toLowerCase();
  const hasAllowedExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
  
  // Check for double extensions (security check)
  const parts = fileName.split('.');
  if (parts.length > 2) {
    // Check if any intermediate part looks like a dangerous extension
    const dangerousExts = ['.exe', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.js'];
    for (let i = 1; i < parts.length - 1; i++) {
      if (dangerousExts.includes('.' + parts[i])) {
        console.warn('Double extension detected:', fileName);
        return false;
      }
    }
  }
  
  // Allowed MIME types (matching backend)
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    'application/json',
    'text/xml',
    'application/xml',
    'text/html',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/zip',
    'application/x-tar',
    'application/gzip',
  ];
  
  const hasAllowedMimeType = allowedTypes.includes(file.type);
  
  return hasAllowedExtension && (hasAllowedMimeType || !file.type);
}

export function validateFileSize(file: File, maxSizeMB: number = 100): boolean {
  // Match backend limit of 100MB
  return file.size <= maxSizeMB * 1024 * 1024;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// API Functions with multiple signatures for backward compatibility
export async function getFiles(): Promise<ApiResponse<UploadedFile[]>>;
export async function getFiles(token: string): Promise<UploadedFile[]>;
export async function getFiles(token?: string): Promise<ApiResponse<UploadedFile[]> | UploadedFile[]> {
  try {
    const headers = token ? 
      { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } :
      getAuthHeaders();

    const response = await fetch(`${WEBUI_API_BASE_URL}/upload/`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const files = data.results || data;

    // Return format based on whether token was passed (backward compatibility)
    if (token) {
      return files;
    }

    return {
      success: true,
      data: files
    };
  } catch (error) {
    console.error('Error fetching files:', error);
    
    if (token) {
      throw error; // For old signature, throw error
    }
    
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch files'
    };
  }
}

// Upload files with multiple signatures
export async function uploadFiles(files: File[], otherInfo?: any, onProgress?: (progress: any) => void): Promise<FileUploadResponse>;
export async function uploadFiles(token: string, files: File[]): Promise<FileUploadResponse>;
export async function uploadFiles(
  tokenOrFiles: string | File[],
  filesOrOtherInfo?: File[] | any,
  onProgress?: (progress: any) => void
): Promise<FileUploadResponse> {
  try {
    let files: File[];
    let otherInfo: any = {};
    let token: string | null = null;

    // Handle different signatures
    if (typeof tokenOrFiles === 'string') {
      // uploadFiles(token, files) signature
      token = tokenOrFiles;
      files = filesOrOtherInfo as File[];
    } else {
      // uploadFiles(files, otherInfo, onProgress) signature
      files = tokenOrFiles;
      otherInfo = filesOrOtherInfo || {};
    }

    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append('file', file);
    });
    
    // Extract chat_id from otherInfo if present
    let chatId = null;
    let cleanedOtherInfo = { ...otherInfo };
    
    if (otherInfo && otherInfo.chat_id) {
      chatId = otherInfo.chat_id;
      delete cleanedOtherInfo.chat_id; // Remove chat_id from other_info
    }
    
    // Add chat_id as separate field if present
    if (chatId) {
      formData.append('chat_id', chatId.toString());
    }
    
    // Add remaining other_info if there's anything left
    if (cleanedOtherInfo && Object.keys(cleanedOtherInfo).length > 0) {
      formData.append('other_info', JSON.stringify(cleanedOtherInfo));
    }

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      const authTokenValue = get(authToken);
      if (authTokenValue) {
        headers['Authorization'] = `Bearer ${authTokenValue}`;
      }
    }

    const response = await fetch(`${WEBUI_API_BASE_URL}/upload/`, {
      method: 'POST',
      headers,
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        errors: [data.detail || data.message || 'Upload failed'],
        message: 'Upload failed'
      };
    }

    return {
      success: Array.isArray(data) ? data : [data],
      message: 'Files uploaded successfully'
    };
  } catch (error) {
    console.error('Error uploading files:', error);
    return {
      errors: [error instanceof Error ? error.message : 'Upload failed'],
      message: 'Upload failed'
    };
  }
}

// Get docling JSON with multiple signatures
export async function getDoclingJson(fileId: string | number): Promise<ApiResponse<any>>;
export async function getDoclingJson(token: string, fileId: string | number): Promise<ApiResponse<any>>;
export async function getDoclingJson(
  tokenOrFileId: string | number, 
  fileId?: string | number
): Promise<ApiResponse<any>> {
  try {
    let actualFileId: string | number;
    let headers: Record<string, string>;

    if (fileId !== undefined) {
      // getDoclingJson(token, fileId) signature
      const token = tokenOrFileId as string;
      actualFileId = fileId;
      headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    } else {
      // getDoclingJson(fileId) signature
      actualFileId = tokenOrFileId;
      headers = getAuthHeaders();
    }

    const response = await fetch(`${WEBUI_API_BASE_URL}/files/${actualFileId}/docling-json/`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      docling_json: data // For backward compatibility
    };
  } catch (error) {
    console.error('Error fetching docling data:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch document data'
    };
  }
}

// Approve file with multiple signatures
export async function approveFile(fileId: string | number): Promise<ApiResponse<any>>;
export async function approveFile(token: string, fileId: string | number): Promise<ApiResponse<any>>;
export async function approveFile(
  tokenOrFileId: string | number,
  fileId?: string | number
): Promise<ApiResponse<any>> {
  try {
    let actualFileId: string | number;
    let headers: Record<string, string>;

    if (fileId !== undefined) {
      // approveFile(token, fileId) signature
      const token = tokenOrFileId as string;
      actualFileId = fileId;
      headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    } else {
      // approveFile(fileId) signature
      actualFileId = tokenOrFileId;
      headers = getAuthHeaders();
    }

    const response = await fetch(`${WEBUI_API_BASE_URL}/files/${actualFileId}/approve-file/`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data
    };
  } catch (error) {
    console.error('Error approving file:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to approve file'
    };
  }
}

export async function deleteFile(fileId: string | number): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/files/${fileId}/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return {
      success: true,
      data: { message: 'File deleted successfully' }
    };
  } catch (error) {
    console.error('Error deleting file:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete file'
    };
  }
}

// AI Comments API with multiple signatures
export async function getAIComments(fileId: string | number): Promise<ApiResponse<any>>;
export async function getAIComments(token: string, fileId: string | number): Promise<ApiResponse<any>>;
export async function getAIComments(
  tokenOrFileId: string | number,
  fileId?: string | number
): Promise<ApiResponse<any>> {
  try {
    let actualFileId: string | number;
    let headers: Record<string, string>;

    if (fileId !== undefined) {
      // getAIComments(token, fileId) signature
      const token = tokenOrFileId as string;
      actualFileId = fileId;
      headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    } else {
      // getAIComments(fileId) signature
      actualFileId = tokenOrFileId;
      headers = getAuthHeaders();
    }

    const response = await fetch(`${WEBUI_API_BASE_URL}/files/${actualFileId}/ai-comments/`, {
      headers,
    });

    if (!response.ok) {
      if (response.status === 404) {
        // Return empty comments if endpoint doesn't exist yet
        return {
          success: true,
          comments: [],
          data: { comments: [] }
        };
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      comments: data.comments || data.results || data || [],
      data
    };
  } catch (error) {
    console.error('Error fetching AI comments:', error);
    
    // Return empty comments instead of error for better UX
    return {
      success: true,
      comments: [],
      data: { comments: [] }
    };
  }
}