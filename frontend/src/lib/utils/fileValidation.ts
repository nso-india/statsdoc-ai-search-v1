import { get } from 'svelte/store';
import { fileSizeLimitBytes } from '$lib/stores/settings';
import { toast } from 'svelte-sonner';

// File validation utility
export function validateFile(file: File): { isValid: boolean; error?: string } {
  const maxSizeBytes = get(fileSizeLimitBytes);
  
  if (file.size > maxSizeBytes) {
    const maxSizeMB = Math.round(maxSizeBytes / (1024 * 1024));
    return {
      isValid: false,
      error: `File "${file.name}" is too large. Maximum size allowed is ${maxSizeMB}MB.`
    };
  }
  
  return { isValid: true };
}

// Validate multiple files
export function validateFiles(files: File[]): { validFiles: File[]; errors: string[] } {
  const validFiles: File[] = [];
  const errors: string[] = [];
  
  files.forEach(file => {
    const validation = validateFile(file);
    if (validation.isValid) {
      validFiles.push(file);
    } else {
      errors.push(validation.error!);
    }
  });
  
  return { validFiles, errors };
}

// Show file validation errors as toasts
export function showFileValidationErrors(errors: string[]) {
  errors.forEach(error => {
    toast.error(error);
  });
}

// Get current file size limit for display
export function getCurrentFileSizeLimit() {
  return Math.round(get(fileSizeLimitBytes) / (1024 * 1024));
}

// Format file size for display
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
