<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { uploadFiles, validateFileType, validateFileSize, formatFileSize } from '$lib/apis/files';
    import { newChatApi } from '$lib/api/newchat';
    import Upload from '@lucide/svelte/icons/upload';
    import X from '@lucide/svelte/icons/x';
    import File from '@lucide/svelte/icons/file';
    import AlertCircle from '@lucide/svelte/icons/alert-circle';

    export let disabled = false;
    export let maxFiles = 5;
    export let maxSizeMB = 50;
    export let chatId: number | null = null;
    export let prompt = '';

    const dispatch = createEventDispatcher();

    let dragActive = false;
    let files = [];
    let uploadProgress = {};
    let uploading = false;
    let errors = [];
    let fileInput;

    // Reset component state
    export function reset() {
        files = [];
        uploadProgress = {};
        uploading = false;
        errors = [];
        if (fileInput) fileInput.value = '';
    }

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        dragActive = false;
        
        if (disabled || uploading) return;
        
        const droppedFiles = Array.from(e.dataTransfer?.files || []);
        addFiles(droppedFiles);
    }

    function handleFileSelect(e: Event) {
        const target = e.target as HTMLInputElement;
        const selectedFiles = Array.from(target.files || []);
        addFiles(selectedFiles);
    }

    function addFiles(newFiles: File[]) {
        errors = [];
        
        // Check total file count
        if (files.length + newFiles.length > maxFiles) {
            errors = [...errors, `Maximum ${maxFiles} files allowed`];
            return;
        }

        const validFiles: File[] = [];
        
        for (const file of newFiles) {
            // Check if file already exists
            if (files.some(f => f.name === file.name && f.size === file.size)) {
                errors = [...errors, `File "${file.name}" already added`];
                continue;
            }

            // Validate file type
            if (!validateFileType(file)) {
                errors = [...errors, `File "${file.name}" has unsupported format`];
                continue;
            }

            // Validate file size
            if (!validateFileSize(file, maxSizeMB)) {
                errors = [...errors, `File "${file.name}" exceeds ${maxSizeMB}MB limit`];
                continue;
            }

            validFiles.push(file);
        }

        files = [...files, ...validFiles];
    }

    function removeFile(index: number) {
        if (uploading) return;
        files = files.filter((_, i) => i !== index);
        errors = [];
    }

    async function uploadFilesWithPrompt() {
        if (files.length === 0 || uploading) return;

        uploading = true;
        errors = [];

        try {
            // Use the existing upload API first
            const response = await uploadFiles(files, { 
                chat_id: chatId,
                prompt: prompt.trim() 
            });

            if (response.success) {
                // Extract file IDs from successful uploads
                const fileIds = response.success.map(file => file.id);
                
                dispatch('upload-success', {
                    files: response.success,
                    fileIds: fileIds,
                    chatId: chatId,
                    prompt: prompt.trim()
                });
                reset();
            } else if (response.errors) {
                errors = response.errors;
            }
        } catch (error) {
            console.error('Upload error:', error);
            errors = [error instanceof Error ? error.message : 'Upload failed'];
        } finally {
            uploading = false;
        }
    }

    function handleKeyPress(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey && files.length > 0) {
            e.preventDefault();
            uploadFilesWithPrompt();
        }
    }
</script>

<div class="file-upload-container">
    <!-- File Drop Zone -->
    <div
        class="drop-zone"
        class:drag-active={dragActive}
        class:disabled
        on:drop={handleDrop}
        on:dragover|preventDefault={() => {
            if (!disabled && !uploading) dragActive = true;
        }}
        on:dragleave={() => dragActive = false}
        role="button"
        tabindex="0"
        on:click={() => !disabled && !uploading && fileInput?.click()}
        on:keydown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !disabled && !uploading) {
                fileInput?.click();
            }
        }}
    >
        <input
            bind:this={fileInput}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.csv,.html,.md"
            on:change={handleFileSelect}
            class="hidden"
            {disabled}
        />
        
        <div class="drop-zone-content">
            <Upload class="upload-icon" />
            <p class="drop-text">
                {#if files.length === 0}
                    Drop files here or click to browse
                {:else}
                    Add more files or click to browse
                {/if}
            </p>
            <p class="file-info">
                Supports PDF, Word, PowerPoint, Text files (max {maxSizeMB}MB each)
            </p>
        </div>
    </div>

    <!-- File List -->
    {#if files.length > 0}
        <div class="file-list">
            <h4>Selected Files ({files.length}/{maxFiles})</h4>
            {#each files as file, index}
                <div class="file-item">
                    <File class="file-icon" />
                    <div class="file-details">
                        <span class="file-name">{file.name}</span>
                        <span class="file-size">{formatFileSize(file.size)}</span>
                    </div>
                    {#if !uploading}
                        <button
                            class="remove-btn"
                            on:click={() => removeFile(index)}
                            title="Remove file"
                        >
                            <X size={16} />
                        </button>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}

    <!-- Errors -->
    {#if errors.length > 0}
        <div class="error-list">
            {#each errors as error}
                <div class="error-item">
                    <AlertCircle size={16} />
                    <span>{error}</span>
                </div>
            {/each}
        </div>
    {/if}

    <!-- Upload Button -->
    {#if files.length > 0}
        <div class="upload-actions">
            <button
                class="upload-btn"
                class:uploading
                on:click={uploadFilesWithPrompt}
                disabled={uploading || disabled}
            >
                {#if uploading}
                    <div class="spinner"></div>
                    Uploading...
                {:else}
                    <Upload size={16} />
                    Upload {files.length} file{files.length > 1 ? 's' : ''}
                {/if}
            </button>
        </div>
    {/if}
</div>

<svelte:window on:keydown={handleKeyPress} />

<style>
    .file-upload-container {
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
    }

    .drop-zone {
        border: 2px dashed #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        background: #fafafa;
    }

    .drop-zone:hover:not(.disabled) {
        border-color: #3b82f6;
        background: #f8fafc;
    }

    .drop-zone.drag-active {
        border-color: #3b82f6;
        background: #eff6ff;
        transform: scale(1.02);
    }

    .drop-zone.disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .drop-zone-content {
        pointer-events: none;
    }

    .upload-icon {
        width: 48px;
        height: 48px;
        color: #6b7280;
        margin: 0 auto 1rem;
    }

    .drop-text {
        font-size: 1.1rem;
        font-weight: 500;
        color: #374151;
        margin: 0 0 0.5rem;
    }

    .file-info {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0;
    }

    .file-list {
        margin-top: 1.5rem;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }

    .file-list h4 {
        margin: 0 0 1rem;
        font-size: 0.875rem;
        font-weight: 600;
        color: #374151;
    }

    .file-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 6px;
        transition: background-color 0.2s;
    }

    .file-item:hover {
        background: #f9fafb;
    }

    .file-icon {
        width: 20px;
        height: 20px;
        color: #6b7280;
        flex-shrink: 0;
    }

    .file-details {
        flex: 1;
        min-width: 0;
    }

    .file-name {
        display: block;
        font-weight: 500;
        color: #374151;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    .file-size {
        display: block;
        font-size: 0.75rem;
        color: #6b7280;
    }

    .remove-btn {
        padding: 0.25rem;
        border-radius: 4px;
        border: none;
        background: none;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.2s;
        flex-shrink: 0;
    }

    .remove-btn:hover {
        background: #fee2e2;
        color: #dc2626;
    }

    .error-list {
        margin-top: 1rem;
        padding: 1rem;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
    }

    .error-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #dc2626;
        font-size: 0.875rem;
    }

    .error-item + .error-item {
        margin-top: 0.5rem;
    }

    .upload-actions {
        margin-top: 1.5rem;
        display: flex;
        justify-content: center;
    }

    .upload-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }

    .upload-btn:hover:not(:disabled) {
        background: #2563eb;
    }

    .upload-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .upload-btn.uploading {
        background: #6b7280;
    }

    .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .hidden {
        display: none;
    }
</style>
