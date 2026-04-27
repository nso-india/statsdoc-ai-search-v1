<script lang="ts">
	import { createEventDispatcher, onDestroy } from 'svelte';
	import { uploadFiles, validateFileType, validateFileSize, formatFileSize } from '$lib/apis/files.js';
	import { uploadStore, multiFileUploadStore, multiFileUploadActions, isUploading, overallUploadStatus } from '$lib/stores/upload.js';
	import type { UploadedFile } from '$lib/apis/files.js';

	// Props
	export let acceptedTypes: string[] = [];
	export let maxFileSize: number = 10; // MB
	export let maxFiles: number = 10;
	export let multiple: boolean = true;
	export let disabled: boolean = false;
	export let showProgress: boolean = true;
	export let showFileList: boolean = true;
	export let allowCancel: boolean = true;
	export let otherInfo: any = {};

	// Component state
	let fileInput: HTMLInputElement;
	let dragOver = false;
	let validationErrors: string[] = [];

	// Event dispatch
	const dispatch = createEventDispatcher<{
		uploadStart: { files: File[] };
		uploadProgress: { percentage: number };
		uploadComplete: { files: UploadedFile[] };
		uploadError: { error: string };
		fileRemoved: { fileId: string };
	}>();

	// Reactive statements
	$: canUpload = !$isUploading && !disabled;
	$: hasFiles = $multiFileUploadStore.length > 0;

	// File validation
	function validateFiles(files: FileList | File[]): { valid: File[]; errors: string[] } {
		const valid: File[] = [];
		const errors: string[] = [];
		const fileArray = Array.from(files);

		// Check file count
		if (fileArray.length > maxFiles) {
			errors.push(`Maximum ${maxFiles} files allowed`);
			return { valid, errors };
		}

		// Check total files including existing
		if ($multiFileUploadStore.length + fileArray.length > maxFiles) {
			errors.push(`Total files would exceed maximum of ${maxFiles}`);
			return { valid, errors };
		}

		fileArray.forEach((file, index) => {
			const fileErrors: string[] = [];

			// Validate file type
			if (acceptedTypes.length > 0 && !validateFileType(file)) {
				fileErrors.push(`File type not allowed: ${file.type || 'unknown'}`);
			}

			// Validate file size
			if (!validateFileSize(file, maxFileSize)) {
				fileErrors.push(`File size exceeds ${maxFileSize}MB: ${formatFileSize(file.size)}`);
			}

			// Check for duplicate names
			const isDuplicate = $multiFileUploadStore.some(existingFile => 
				existingFile.file.name === file.name
			);
			if (isDuplicate) {
				fileErrors.push(`File already selected: ${file.name}`);
			}

			if (fileErrors.length === 0) {
				valid.push(file);
			} else {
				errors.push(`${file.name}: ${fileErrors.join(', ')}`);
			}
		});

		return { valid, errors };
	}

	// Handle file selection
	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			addFiles(target.files);
		}
	}

	// Handle drag and drop
	function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
		
		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			addFiles(files);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragOver = true;
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
	}

	// Add files to upload queue
	function addFiles(files: FileList | File[]) {
		const { valid, errors } = validateFiles(files);
		
		validationErrors = errors;

		if (valid.length > 0) {
			multiFileUploadActions.addFiles(valid);
			dispatch('uploadStart', { files: valid });
		}

		// Clear file input
		if (fileInput) {
			fileInput.value = '';
		}
	}

	// Remove file from upload queue
	function removeFile(fileId: string) {
		multiFileUploadActions.removeFile(fileId);
		dispatch('fileRemoved', { fileId });
	}

	// Upload function with proper store integration
	async function startUpload() {
		const filesToUpload = $multiFileUploadStore.filter(f => f.status === 'pending').map(f => f.file);
		if (!filesToUpload.length) return;

		try {
			const abortController = new AbortController();
			uploadStore.update(store => ({ 
				...store, 
				isUploading: true, 
				progress: 0, 
				error: null,
				abortController 
			}));

			// Update file states to uploading
			$multiFileUploadStore.forEach(fileState => {
				if (fileState.status === 'pending') {
					multiFileUploadActions.updateFileStatus(fileState.id, 'uploading');
				}
			});

			const response = await uploadFiles(filesToUpload, otherInfo, (progress) => {
				uploadStore.update(store => ({ ...store, progress: progress.percentage || 0 }));
				dispatch('uploadProgress', { percentage: progress.percentage });
			});

			if (response.success && response.success.length > 0) {
				// Success - update file states
				$multiFileUploadStore.forEach(fileState => {
					if (fileState.status === 'uploading') {
						multiFileUploadActions.updateFileStatus(fileState.id, 'completed', undefined, response.success.find(f => f.filename === fileState.file.name));
					}
				});

				validationErrors = [];

				uploadStore.update(store => ({ 
					...store, 
					isUploading: false, 
					progress: 100,
					error: null,
					abortController: null
				}));

				dispatch('uploadComplete', { files: response.success });
			} else {
				// Handle partial errors or failures
				const errorMessages = response.errors || ['Upload failed'];
				
				uploadStore.update(store => ({ 
					...store, 
					isUploading: false, 
					error: errorMessages.join(', '),
					abortController: null
				}));
				
				// Update file states for multi-file upload
				$multiFileUploadStore.forEach(fileState => {
					if (fileState.status === 'uploading') {
						multiFileUploadActions.updateFileStatus(fileState.id, 'failed', errorMessages.join(', '));
					}
				});

				dispatch('uploadError', { error: errorMessages.join(', ') });
			}
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Upload failed';
			uploadStore.update(store => ({ 
				...store, 
				isUploading: false, 
				error: errorMessage,
				abortController: null
			}));
			
			// Update failed file states
			$multiFileUploadStore.forEach(fileState => {
				if (fileState.status === 'uploading') {
					multiFileUploadActions.updateFileStatus(fileState.id, 'failed', errorMessage);
				}
			});

			dispatch('uploadError', { error: errorMessage });
		}
	}

	function cancelUpload() {
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
		
		multiFileUploadActions.clearAll();
		dispatch('uploadCancelled');
	}

	function clearFiles() {
		multiFileUploadActions.clearAll();
		validationErrors = [];
	}

	function clearValidationErrors() {
		validationErrors = [];
	}
</script>

<!-- File Upload Component -->
<div class="file-upload-container">
	<!-- Upload Area -->
	<div 
		class="upload-area"
		class:drag-over={dragOver}
		class:disabled={!canUpload}
		ondrop={handleDrop}
		ondragover={handleDragOver}
		ondragleave={handleDragLeave}
		role="button"
		tabindex="0"
		onclick={() => canUpload && fileInput?.click()}
		onkeydown={(e) => {
			if ((e.key === 'Enter' || e.key === ' ') && canUpload) {
				e.preventDefault();
				fileInput?.click();
			}
		}}
	>
		<input
			bind:this={fileInput}
			type="file"
			{multiple}
			accept={acceptedTypes.join(',')}
			onchange={handleFileSelect}
			disabled={!canUpload}
			class="file-input"
		/>

		<div class="upload-content">
			<div class="upload-icon">
				<svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
					<path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
				</svg>
			</div>
			
			<div class="upload-text">
				{#if dragOver}
					<p class="primary-text">Drop files here to upload</p>
				{:else if canUpload}
					<p class="primary-text">Click to select files or drag and drop</p>
					<p class="secondary-text">
						{#if acceptedTypes.length > 0}
							Accepted types: {acceptedTypes.join(', ')}
						{/if}
						{#if maxFileSize}
							• Max size: {maxFileSize}MB per file
						{/if}
						{#if maxFiles > 1}
							• Max files: {maxFiles}
						{/if}
					</p>
				{:else}
					<p class="primary-text">Upload disabled</p>
				{/if}
			</div>
		</div>
	</div>

	<!-- Validation Errors -->
	{#if validationErrors.length > 0}
		<div class="error-container">
			<div class="error-header">
				<span>Validation Errors</span>
				<button 
					type="button" 
					class="error-close" 
					onclick={clearValidationErrors}
					aria-label="Clear validation errors"
				>
					×
				</button>
			</div>
			<ul class="error-list">
				{#each validationErrors as error}
					<li>{error}</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- File List -->
	{#if showFileList && hasFiles}
		<div class="file-list">
			<div class="file-list-header">
				<h3>Selected Files ({$overallUploadStatus.total})</h3>
				<div class="file-list-actions">
					{#if $overallUploadStatus.pending > 0 && canUpload}
						<button 
							type="button" 
							class="btn btn-primary"
							onclick={startUpload}
						>
							Upload {$overallUploadStatus.pending} Files
						</button>
					{/if}
					
					{#if $isUploading && allowCancel}
						<button 
							type="button" 
							class="btn btn-secondary"
							onclick={cancelUpload}
						>
							Cancel Upload
						</button>
					{/if}
					
					<button 
						type="button" 
						class="btn btn-outline"
						onclick={clearFiles}
						disabled={$isUploading}
					>
						Clear All
					</button>
				</div>
			</div>

			<div class="file-items">
				{#each $multiFileUploadStore as fileState (fileState.id)}
					<div class="file-item" class:error={fileState.status === 'error'}>
						<div class="file-info">
							<div class="file-name">{fileState.file.name}</div>
							<div class="file-details">
								{formatFileSize(fileState.file.size)}
								• {fileState.file.type || 'Unknown type'}
								• Status: {fileState.status}
							</div>
							{#if fileState.error}
								<div class="file-error">{fileState.error}</div>
							{/if}
						</div>

						{#if showProgress && (fileState.status === 'uploading' || fileState.status === 'completed')}
							<div class="progress-container">
								<div class="progress-bar">
									<div 
										class="progress-fill" 
										style="width: {fileState.progress}%"
									></div>
								</div>
								<span class="progress-text">{fileState.progress}%</span>
							</div>
						{/if}

						<div class="file-actions">
							{#if fileState.status === 'pending' || fileState.status === 'error'}
								<button 
									type="button" 
									class="btn-icon" 
									onclick={() => removeFile(fileState.id)}
									aria-label="Remove file"
									disabled={$isUploading}
								>
									<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
										<path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
									</svg>
								</button>
							{:else if fileState.status === 'completed'}
								<div class="status-icon success">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
										<path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z" />
									</svg>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Overall Progress -->
	{#if showProgress && $isUploading}
		<div class="overall-progress">
			<div class="progress-header">
				<span>Overall Progress</span>
				<span>{$overallUploadStatus.completed} / {$overallUploadStatus.total} files</span>
			</div>
			<div class="progress-bar large">
				<div 
					class="progress-fill" 
					style="width: {($overallUploadStatus.completed / $overallUploadStatus.total) * 100}%"
				></div>
			</div>
		</div>
	{/if}
</div>

<style>
	.file-upload-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 16px;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		background-color: #fff;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}

	.upload-area {
		border: 2px dashed #d1d5db;
		border-radius: 8px;
		padding: 24px;
		text-align: center;
		cursor: pointer;
		transition: border-color 0.3s;
	}

	.upload-area.drag-over {
		border-color: #295887;
		background-color: #eff6ff;
	}

	.upload-area.disabled {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.file-input {
		display: none;
	}

	.upload-content {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.upload-icon {
		margin-bottom: 12px;
	}

	.upload-icon svg {
		width: 48px;
		height: 48px;
		color: #9ca3af;
	}

	.primary-text {
		font-size: 16px;
		font-weight: 500;
		color: #111827;
		margin: 0;
	}

	.secondary-text {
		font-size: 14px;
		color: #6b7280;
		margin: 4px 0 0 0;
	}

	.error-container {
		margin-top: 16px;
		padding: 12px;
		background-color: #fee2e2;
		border: 1px solid #f87171;
		border-radius: 8px;
	}

	.error-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.error-header span {
		font-weight: 500;
		color: #b91c1c;
	}

	.error-close {
		background: none;
		border: none;
		color: #b91c1c;
		cursor: pointer;
		font-size: 16px;
	}

	.error-list {
		margin: 8px 0 0 0;
		padding: 0;
		list-style-type: none;
	}

	.error-list li {
		font-size: 14px;
		color: #b91c1c;
	}

	.file-list {
		margin-top: 16px;
	}

	.file-list-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
	}

	.file-list-header h3 {
		font-size: 16px;
		font-weight: 500;
		color: #111827;
		margin: 0;
	}

	.file-list-actions {
		display: flex;
		gap: 8px;
	}

	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 8px 12px;
		font-size: 14px;
		font-weight: 500;
		color: #fff;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		transition: background-color 0.3s;
	}

	.btn-primary {
		background-color: #16306b;
	}

	.btn-primary:hover {
		background-color: rgba(22, 48, 107, 0.9);
	}

	.btn-secondary {
		background-color: #64748b;
	}

	.btn-secondary:hover {
		background-color: #475569;
	}

	.btn-outline {
		background-color: transparent;
		border: 2px solid #16306b;
		color: #16306b;
	}

	.btn-outline:hover {
		background-color: #eff6ff;
	}

	.file-items {
		border-top: 1px solid #e5e7eb;
		padding-top: 12px;
	}

	.file-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		margin-bottom: 8px;
		background-color: #f9fafb;
		transition: background-color 0.3s;
	}

	.file-item.error {
		border-color: #f87171;
		background-color: #fee2e2;
	}

	.file-info {
		flex: 1;
		margin-right: 12px;
	}

	.file-name {
		font-size: 14px;
		font-weight: 500;
		color: #111827;
	}

	.file-details {
		font-size: 12px;
		color: #6b7280;
		margin-top: 4px;
	}

	.file-error {
		font-size: 12px;
		color: #b91c1c;
		margin-top: 4px;
	}

	.progress-container {
		width: 100%;
		height: 8px;
		background-color: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
		margin-top: 8px;
	}

	.progress-bar {
		height: 100%;
		display: flex;
		align-items: center;
	}

	.progress-fill {
		height: 100%;
		background-color: #16306b;
		transition: width 0.3s;
	}

	.progress-text {
		font-size: 12px;
		color: #111827;
		margin-left: 8px;
	}

	.file-actions {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.btn-icon {
		background: none;
		border: none;
		color: #16306b;
		cursor: pointer;
	}

	.status-icon {
		width: 16px;
		height: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.status-icon.success {
		color: #4caf50;
	}

	.overall-progress {
		margin-top: 16px;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
	}

	.progress-bar.large {
		height: 8px;
		background-color: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background-color: #16306b;
		transition: width 0.3s;
	}
</style>