<script lang="ts">
    import X from '@lucide/svelte/icons/x';
    
    export let file: File;
    export let onRemove: () => void;
    
    function formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
</script>

<div class="inline-flex items-center gap-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full px-2.5 py-1 text-xs font-medium border border-blue-200 dark:border-blue-800">
    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
    </svg>
    <span class="truncate max-w-24">{file.name}</span>
    <span class="text-blue-600 dark:text-blue-400">({formatFileSize(file.size)})</span>
    <button 
        type="button"
        on:click={onRemove}
        class="hover:bg-blue-200 dark:hover:bg-blue-800 rounded-full p-0.5 transition-colors"
        aria-label="Remove file"
    >
        <X class="w-3 h-3" />
    </button>
</div>
