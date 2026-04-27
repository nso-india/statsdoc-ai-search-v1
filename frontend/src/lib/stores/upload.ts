import { writable, derived, get } from 'svelte/store';
import { fileSizeLimitBytes } from './settings';
import { toast } from 'svelte-sonner';

// Upload state interface
export interface FileUploadState {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  progress: number;
  error?: string;
  uploadedFile?: any;
}

// Single file upload store
export const uploadStore = writable({
  isUploading: false,
  progress: 0,
  error: null as string | null,
  abortController: null as AbortController | null,
});

// Multi-file upload store
export const multiFileUploadStore = writable<FileUploadState[]>([]);

// Derived stores
export const isUploading = derived(
  [uploadStore, multiFileUploadStore],
  ([$uploadStore, $multiFileUploadStore]) => {
    return $uploadStore.isUploading || $multiFileUploadStore.some(f => f.status === 'uploading');
  }
);

export const overallUploadStatus = derived(
  multiFileUploadStore,
  ($multiFileUploadStore) => {
    if ($multiFileUploadStore.length === 0) return {
      status: 'idle',
      total: 0,
      completed: 0,
      pending: 0,
      failed: 0,
      uploading: 0
    };
    
    const uploading = $multiFileUploadStore.filter(f => f.status === 'uploading');
    const completed = $multiFileUploadStore.filter(f => f.status === 'completed');
    const failed = $multiFileUploadStore.filter(f => f.status === 'failed');
    const pending = $multiFileUploadStore.filter(f => f.status === 'pending');
    
    let status = 'idle';
    if (uploading.length > 0) status = 'uploading';
    else if (failed.length > 0 && completed.length === 0) status = 'failed';
    else if (completed.length === $multiFileUploadStore.length) status = 'completed';
    else if (completed.length > 0 || failed.length > 0) status = 'partial';
    
    return {
      status,
      total: $multiFileUploadStore.length,
      completed: completed.length,
      pending: pending.length,
      failed: failed.length,
      uploading: uploading.length
    };
  }
);

// Multi-file upload actions
export const multiFileUploadActions = {
  // Validate file size before adding
  validateFile: (file: File): { isValid: boolean; error?: string } => {
    const maxSizeBytes = get(fileSizeLimitBytes);
    if (file.size > maxSizeBytes) {
      const maxSizeMB = Math.round(maxSizeBytes / (1024 * 1024));
      return {
        isValid: false,
        error: `File "${file.name}" is too large. Maximum size allowed is ${maxSizeMB}MB.`
      };
    }
    return { isValid: true };
  },

  addFiles: (files: File[]) => {
    const validFiles: File[] = [];
    const errors: string[] = [];

    // Validate each file before adding
    files.forEach(file => {
      const validation = multiFileUploadActions.validateFile(file);
      if (validation.isValid) {
        validFiles.push(file);
      } else {
        errors.push(validation.error!);
        toast.error(validation.error!);
      }
    });

    // Add only valid files
    if (validFiles.length > 0) {
      multiFileUploadStore.update(store => {
        const newFileStates = validFiles.map(file => ({
          id: `${file.name}-${Date.now()}-${Math.random()}`,
          file,
          status: 'pending' as const,
          progress: 0,
        }));
        return [...store, ...newFileStates];
      });
    }

    return { validFiles: validFiles.length, totalFiles: files.length, errors };
  },

  removeFile: (fileId: string) => {
    multiFileUploadStore.update(store => 
      store.filter(f => f.id !== fileId)
    );
  },

  updateFileStatus: (fileId: string, status: FileUploadState['status'], error?: string, uploadedFile?: any) => {
    multiFileUploadStore.update(store => 
      store.map(f => f.id === fileId 
        ? { ...f, status, error, uploadedFile, progress: status === 'completed' ? 100 : f.progress }
        : f
      )
    );
  },

  updateFileProgress: (fileId: string, progress: number) => {
    multiFileUploadStore.update(store => 
      store.map(f => f.id === fileId ? { ...f, progress } : f)
    );
  },

  clearAll: () => {
    multiFileUploadStore.set([]);
  },

  clearCompleted: () => {
    multiFileUploadStore.update(store => 
      store.filter(f => f.status !== 'completed')
    );
  },

  clear: () => {
    multiFileUploadStore.set([]);
  },
};

// Single upload actions
export const uploadActions = {
  setUploading: (isUploading: boolean) => {
    uploadStore.update(store => ({ ...store, isUploading }));
  },

  updateProgress: (progress: number) => {
    uploadStore.update(store => ({ ...store, progress }));
  },

  setError: (error: string | null) => {
    uploadStore.update(store => ({ ...store, error }));
  },

  addError: (error: string) => {
    uploadStore.update(store => ({ ...store, error }));
  },

  clearErrors: () => {
    uploadStore.update(store => ({ ...store, error: null }));
  },

  startUpload: (abortController: AbortController) => {
    uploadStore.update(store => ({ 
      ...store, 
      isUploading: true, 
      progress: 0, 
      error: null,
      abortController 
    }));
  },

  completeUpload: (uploadedFiles: any[], errors?: string[]) => {
    uploadStore.update(store => ({ 
      ...store, 
      isUploading: false, 
      progress: 100,
      error: errors && errors.length > 0 ? errors.join(', ') : null,
      abortController: null
    }));
  },

  cancelUpload: () => {
    uploadStore.update(store => {
      if (store.abortController) {
        store.abortController.abort();
      }
      return { 
        ...store, 
        isUploading: false, 
        progress: 0,
        abortController: null 
      };
    });
  },

  reset: () => {
    uploadStore.set({ isUploading: false, progress: 0, error: null, abortController: null });
  },
};

// Extend the uploadStore with methods for compatibility
const createExtendedUploadStore = () => {
  const { subscribe, set, update } = uploadStore;

  return {
    subscribe,
    set,
    update,
    ...uploadActions
  };
};

// Export enhanced store
export const enhancedUploadStore = createExtendedUploadStore();