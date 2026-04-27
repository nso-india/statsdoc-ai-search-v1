<script lang="ts">
    import * as AlertDialog from "$lib/components/ui/alert-dialog";
    import X from '@lucide/svelte/icons/x';

    let { open = $bindable(false) } = $props();

    const url = encodeURI('/User Manual 2.0.pdf');
</script>

<AlertDialog.Root bind:open>
    <AlertDialog.Content 
        class="sm:max-w-[900px] w-full h-[80vh] p-4"
        oninteractoutside={() => open = false}
    >
        <button
            onclick={() => open = false}
            class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
            aria-label="Close"
        >
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
        </button>

        <AlertDialog.Header>
            <AlertDialog.Title class="text-2xl">User Manual 2.0</AlertDialog.Title>
        </AlertDialog.Header>

        <div class="h-[calc(80vh-6rem)] mt-2 rounded-sm overflow-hidden border border-gray-200">
            <iframe src={url} class="w-full h-full" frameborder="0"></iframe>
        </div>

        <AlertDialog.Footer class="mt-4 px-4 pb-4">
            <a href={url} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                Open User Manual in new tab
            </a>
        </AlertDialog.Footer>
    </AlertDialog.Content>
</AlertDialog.Root>

<style>
    .text-2xl {
        font-size: 1.5rem;
    }
</style>
